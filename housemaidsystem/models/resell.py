# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging
from . import accounting_integration

logger = logging.getLogger(__name__)


class ReSell(models.Model):
    _name = 'housemaidsystem.applicant.resell'
    _description = 'Re-Sell'

    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    resell_date = fields.Date(string="Re-Sell Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True)
    notes = fields.Text(string="Notes")
    refund = fields.Float(string="Refund", default=0)
    refund_payment_invoice = fields.Many2one('account.payment', 'Down Payment Invoice')
    reverse_invoice_sales = fields.Many2one('account.move', 'Purchase Reverse Move', store='True')
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor")
    invoice_id = fields.Many2one('account.move', 'Invoice',store='True')
    invoice_po_id = fields.Many2one('account.move', 'Sales Invoice', store='True')

    invoice_state = fields.Selection(related="invoice_id.state", string="Invoice Status")
    invoice_total = fields.Monetary(related="invoice_id.amount_total", string="Invoice Total Amount",currency_field='currency_id')
    invoice_due = fields.Monetary(related="invoice_id.amount_residual", string="Invoice Due Amount",currency_field='currency_id')

    invoice_po_state = fields.Selection(related="invoice_po_id.state", string="Purchase Invoice Status")
    invoice_po_total = fields.Monetary(related="invoice_po_id.amount_total", string="Purchase Invoice Total Amount", currency_field='currency_id')
    invoice_po_due = fields.Monetary(related="invoice_po_id.amount_residual", string="Purchase Invoice Due Amount", currency_field='currency_id')

    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    invoice_new_po_id = fields.Many2one('account.move', 'Purchase PO Move', store='True')

    invoice_sales_recong_id = fields.Many2one('account.move', 'Sales Recognized Move', store='True')
    invoice_po_recong_id = fields.Many2one('account.move', 'Purchase PO Recognized Move', store='True')

    currency_id = fields.Many2one('res.currency', string='Invoice Sales Currency', related="invoice_id.currency_id")
    currency_po_id = fields.Many2one('res.currency',string='Invoice PO Currency', related="invoice_po_id.currency_id")

    new_recv_inv_id = fields.Many2one('account.move', 'Purchase Recognized Move', store='True')
    close_deliver_reject_balance = fields.Boolean(string="To Close balance of deliver reject",
                                                  default=False, )

    paid_immediately = fields.Boolean(string="Paid to Sponsor", default=False, )
    pay_due_date = fields.Date(string="Expected Date", required=True, default=fields.Date.context_today)
    paid_immediately_move = fields.Many2one('account.move', 'Suspend Payment Move', store='True')

    refund_down_payment = fields.Many2one('account.payment', 'Refund Down Payment',)
    recongnized_sales = fields.Many2one('account.move', 'Recognized Sales', )
    return_office_activation = fields.Many2one('account.move', 'Activate Return Office', )


    # ================ constraints =================================
    _sql_constraints = [
            ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
      ]

    # ==================  Main Functions ==========================
    def apply(self):
        self.ensure_one()
        application_obj = self.application_id
        application_obj.state = 'resell'

        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
        body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Re-Sell Date : <span>""" + (self.resell_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""

        body_msg += u"""<li>First Sponsor : <span>""" + self.customer_id.name + u"""</span></li>"""

        body_msg += u"""<li>Invoice ID : <span>""" + self.invoice_id.name + u"""</span></li>"""

        body_msg += u"""<li>Invoice Status : <span>""" + self.invoice_state + u"""</span></li>"""

        body_msg += u"""<li>Deal Amount : <span>""" + str(self.invoice_total if self.invoice_total else 0) + u"""</span></li>"""

        body_msg += u"""<li>Due Amount : <span>""" + str(self.invoice_due if self.invoice_due else 0) + u"""</span></li>"""

        body_msg += u"""<li>Refund Amount : <span>""" + str(self.refund if self.refund else 0) + u"""</span></li>"""

        if self.paid_immediately:
            body_msg += u"""<li>Paid to Sponsor : Yes </li>"""
        else:
            body_msg += u"""<li>Paid to Sponsor : No </li>"""
            body_msg += u"""<li>Expected Pay Date : <span>""" + (self.pay_due_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""


        body_msg += u"""</ul>"""
        application_obj.message_post(body=body_msg)

    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name
    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            resell_obj = super(ReSell, self).create(vals)
            # Summary:
            # -------
            # 1- cancel Sales invoice "similar to unlink reservation"
            # 2- remove any down payment "similar to unlink reservation"
            # 3- Create new move from deferred sales to sales to recognized the sales "similar to create new arrival"
            # 4- Recognized sales by sell the housemaid for return office management
            # ==========================================================================


            # 1- Cancel Sales invoice "similar to unlink reservation"
            #---------------------------------------------------------
            # Cr: Acc Rec
            # Dr: Sales recognized first sponsor
            # Amount: Sales Amount
            # ==============================================================
            reservation = self.env['housemaidsystem.applicant.reservations'].search([('application_id', '=',
                                                                                      resell_obj.application_id.id)],limit=1)
            resell_obj.reverse_invoice_sales = accounting_integration.reverse_move(reservation, reservation.invoice_sales_id,
                                                                              'cancel', 'Based on customer request')

            # 2- post refund payment by down payment amount {down_payment_invoice}
            # ----------------------------------------------------------------------
            # Cr: Cash
            # Dr: Acc Rec
            # Amount: Down Amount
            # ======================================================================
            if reservation.down_payment_invoice:
                resell_obj.refund_down_payment = accounting_integration.reservation_refund_down_payment(reservation, reservation.down_payment_invoice)


            # 3- Create new move from deferred sales to sales to recognized the sales "similar to create new arrival"
            #------------------------------------------------------------------------------------------------------------
            # Cr: Sales deferred - arrival
            # Dr: Sales Recognized - arrival
            # Amount: Sales Amount  account.move
            # ==============================================================
            arrival = self.env['housemaidsystem.applicant.arrival'].\
                search([('application_id', '=',resell_obj.application_id.id)],limit=1)
            resell_obj.recongnized_sales = accounting_integration.reverse_move(arrival, arrival.sales_move, 'cancel',
                                                'Reverse Arrival Transaction')

            # 4- Recognized sales by sell the housemaid for return office management
            # --------------------------------------------------------------------------
            # Cr: Sales Recognized - arrival
            # Dr: Return Office management
            # Amount: Sales amount
            # ======================================================================
            resell_obj.return_office_activation = accounting_integration.resell_transfer_sales_to_return(resell_obj)


            return resell_obj
        except Exception as e:
            logger.exception("Create Method")
            raise ValidationError(e)


    def write(self, vals):
        try:
            res = super(ReSell, self).write(vals)
            return res

        except Exception as e:
            logger.exception("ReSell write Method")
            raise ValidationError(e)


    def unlink(self):
        try:
            if self.reverse_invoice_sales:
                accounting_integration.reverse_move(self, self.reverse_invoice_sales,
                                                    'cancel', 'cancel Re-Sell after process Re-Sell')

            if self.refund_down_payment:
                self.refund_down_payment.action_draft()
                self.refund_down_payment.action_cancel()

                reservation = self.env['housemaidsystem.applicant.reservations'].search([('application_id', '=',self.application_id.id)], limit=1)
                if reservation.down_payment_invoice:
                    credit_line_a = reservation.down_payment_invoice.line_ids.filtered(lambda l: l.credit)
                    reservation.invoice_sales_id.js_assign_outstanding_line(credit_line_a.id)



            if self.recongnized_sales:
                accounting_integration.reverse_move(self, self.recongnized_sales,
                                                    'cancel', 'cancel Re-Sell after process Re-Sell')


            if self.return_office_activation:
                accounting_integration.reverse_move(self, self.return_office_activation,
                                                    'cancel', 'cancel Re-Sell after process Re-Sell')



            return super(ReSell, self).unlink()
        except Exception as e:
            logger.exception("Re-Sell unlink Method")
            raise ValidationError(e)




