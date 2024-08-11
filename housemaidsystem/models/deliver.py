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


class Deliver(models.Model):
    _name = 'housemaidsystem.applicant.deliver'
    _description = 'Deliver Housemaid For First Sponsor'

    def _get_type_id(self):
        return self.env['housemaidsystem.configuration.settings'].search([],
                                                                         limit=1).direct_journal_arrival_cash or False
    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    deliver_date = fields.Date(string="Deliver Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True)
    notes = fields.Text(string="Notes")
    paid_amount = fields.Float(string="Paid Amount", default=0)
    paid_payment_invoice = fields.Many2one('account.payment', 'Paid Payment Invoice')
    paid_payment2_invoice = fields.Many2one('account.payment', 'Paid Payment 2 Invoice')
    discount_amount = fields.Float(string="Discount Amount", required=False, default=0)
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor")
    customer_name_ar = fields.Char(related='customer_id.name_ar')
    invoice_id = fields.Many2one('account.move', 'Invoice', store='True')
    invoice_po_id = fields.Many2one('account.move', 'Sales Invoice', store='True')

    invoice_state = fields.Selection(related="invoice_id.state", string="Sales Invoice Status")
    invoice_total = fields.Monetary(related="invoice_id.amount_total", string="Sales Invoice Total Amount",currency_field='currency_id')
    invoice_due = fields.Monetary(related="invoice_id.amount_residual", string="Sales Invoice Due Amount", currency_field='currency_id')

    invoice_po_state = fields.Selection(related="invoice_po_id.state", string="Purchase Invoice Status")
    invoice_po_total = fields.Monetary(related="invoice_po_id.amount_total", string="Purchase Invoice Total Amount", currency_field='currency_id')
    invoice_po_due = fields.Monetary(related="invoice_po_id.amount_residual", string="Purchase Invoice Due Amount", currency_field='currency_id')


    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")

    invoice_sales_recong_id = fields.Many2one('account.move', 'Sales Recognized Move', store='True')
    invoice_po_recong_id = fields.Many2one('account.move', 'Purchase Recognized Move', store='True')
    invoice_new_po_id = fields.Many2one('account.move', 'Purchase PO Move', store='True')

    currency_id = fields.Many2one('res.currency', string='Sales Invoice Currency', related="invoice_id.currency_id")
    currency_po_id = fields.Many2one('res.currency', string='PO Invoice Currency',related="invoice_po_id.currency_id")
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)
    journal = fields.Many2one('account.journal', string="Payment Method", default=_get_type_id, required=True,
                              domain="['|', ('type', '=', 'cash'), ('type', '=', 'bank')]", )
    # ================ constraints =================================
    _sql_constraints = [
            ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
      ]

    # ==================  Main Functions ==========================
    def apply(self):
        self.ensure_one()
        application_obj = self.application_id


        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""

        body_msg += u"""<li>Deliver Enter Date : <span>""" + (self.transaction_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""

        body_msg += u"""<li>Deliver Date : <span>""" + (self.deliver_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""

        body_msg += u"""<li>First Sponsor : <span>""" + self.customer_id.name + u"""</span></li>"""

        body_msg += u"""<li>Invoice ID : <span>""" + self.invoice_id.name + u"""</span></li>"""

        body_msg += u"""<li>Invoice Status : <span>""" + self.invoice_state + u"""</span></li>"""

        body_msg += u"""<li>Deal Amount : <span>""" + str(self.invoice_total) + u"""</span></li>"""

        body_msg += u"""<li>Due Amount : <span>""" + str(self.invoice_due) + u"""</span></li>"""

        body_msg += u"""<li>Paid Amount : <span>""" + str(self.paid_amount) + u"""</span></li>"""

        body_msg += u"""<li>Discount Amount : <span>""" + str(self.discount_amount if self.discount_amount else 0) + u"""</span></li>"""

        if self.journal.type == 'cash':
            body_msg += u"""<li>Cash\K-Net : <span> Cash </span></li>"""
        else:
            body_msg += u"""<li>Cash\K-Net : <span> K-Net </span></li>"""

        body_msg += u"""<li>Journal Name : <span>""" + self.journal.name + u"""</span></li>"""

        body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""

        body_msg += u"""</ul>"""
        application_obj.message_post(body=body_msg)

        partner_obj = self.customer_id
        partner_obj.message_post(body=body_msg)


    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name

    def _get_labor_dtl(self):
        try:
            for record in self:
                if not record.application_id == None:
                    self.office_code = record.application_id.office_code
        except Exception as e:
            logger.exception("_get_labor_dtl Method")
            raise ValidationError(e)
    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            deliver_obj = super(Deliver, self).create(vals)

            if deliver_obj.discount_amount == 0:
                if deliver_obj.paid_amount > deliver_obj.invoice_due:
                    raise ValidationError(_("Sales invoice %s dues amount is less than "
                                            "paid amount." % deliver_obj.invoice_id.display_name))
            else:
                if deliver_obj.paid_amount + deliver_obj.discount_amount != deliver_obj.invoice_due:
                    raise ValidationError(_("Sales invoice %s dues amount should match with paid amount + "
                                            "discount amount." % deliver_obj.invoice_id.display_name))

            if deliver_obj.paid_amount + deliver_obj.discount_amount == deliver_obj.invoice_due:
                deliver_obj.application_id.state = 'deliverpaidfull'
            else:
                deliver_obj.application_id.state = 'deliverpaidpartial'

            # ==============================================================
            # Send whatsApp
            company_obj = self.env['res.company'].search([('id', '!=', 0)], limit=1)
            sponsor = self.env['res.partner'].search([('id', '=', deliver_obj.customer_id.id)], limit=1)
            message = 'Thank you Mr/Mrs: %s for selecting %s office, Please be informed, housemaid %s - %s is delivered to you successfully, you paid %.0f KWD' % (
                sponsor.name, company_obj.name, deliver_obj.application_id.external_office_id,
                deliver_obj.application_id.full_name, deliver_obj.paid_amount)
            accounting_integration.send_whatsapp(self, sponsor, message)
            # ==============================================================

            # 1- Add new payment and attach it to sales invoice
            if deliver_obj.paid_amount > 0.0:
                deliver_obj.paid_payment_invoice = accounting_integration.deliver_sales_payment(deliver_obj)


            return deliver_obj
        except Exception as e:
            logger.exception("Deliver create Method")
            raise ValidationError(e)


    def write(self, vals):
        try:
            res = super(Deliver, self).write(vals)
            return res
        except Exception as e:
            logger.exception("Deliver write Method")
            raise ValidationError(e)


    def unlink(self):
        try:
            if self.paid_payment_invoice:
                self.paid_payment_invoice.action_draft()
                self.paid_payment_invoice.action_cancel()

            if self.paid_payment2_invoice:
                self.paid_payment2_invoice.action_draft()
                self.paid_payment2_invoice.action_cancel()


            return super(Deliver, self).unlink()

        except Exception as e:
            logger.exception("Deliver unlink Method")
            raise ValidationError(e)






