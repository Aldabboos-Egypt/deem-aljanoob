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


class ReturnBackFromLastSponsor(models.Model):
    _name = 'housemaidsystem.applicant.returnbackfromlastsponsor'
    _description = 'Return Back From Last Sponsor'

    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    return_date = fields.Date(string="Return Back Date", required=True, default=fields.Date.context_today)
    deliver_date = fields.Date(string="Deliver Date")
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True)
    refund_amount = fields.Float(string="Refund Amount", onchange="_disable_refund_amount",)
    paid_by_sponsor = fields.Float(string="Paid By Sponsor")
    refund_payment_invoice = fields.Many2one('account.payment', 'Refund Payment Invoice')
    previous_discount = fields.Float(string="Invoice Discount", )
    invoice_id = fields.Many2one('account.move', 'Invoice', store='True')
    old_customer_id = fields.Many2one(comodel_name="res.partner", string="Old Sponsor")
    old_invoice_id = fields.Many2one('account.move', 'Old Invoice', store='True')
    old_invoice_state = fields.Selection(related="old_invoice_id.state", string="Sales Invoice Status")
    old_invoice_total = fields.Monetary(related="old_invoice_id.amount_total", string="Sales Invoice Total Amount",
                                    currency_field='currency_id')
    old_invoice_due = fields.Monetary(related="old_invoice_id.amount_residual", string="Sales Invoice Due Amount",
                                  currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related="old_invoice_id.currency_id")
    application_action = fields.Selection(string="Action",
                                 selection=[('resell', 'Re-Sell Housemaid'),
                                            ('backtocountry', 'Back to country'), ],
                                 required=True, default='resell', )
    resell_move_id = fields.Many2one('account.move', 'Cash Box Move', store='True')
    hm_salary = fields.Float(string="Salary Amount", default=0.0, )
    hm_salary_move = fields.Many2one('account.move', 'Salary move', store='True')
    hm_salary_payment = fields.Many2one('account.payment', 'Salary payment', store='True')
    notes = fields.Text(string="Notes")

    paid_immediately = fields.Boolean(string="Paid To Sponsor", default=False, )
    pay_due_date = fields.Date(string="Pay Due Date", required=True, default=fields.Date.context_today)
    paid_immediately_move = fields.Many2one('account.move', 'Suspend Payment Move', store='True')

    refund_complete_payment = fields.Many2one('account.payment', 'Refund Complete Payment', store='True')
    refund_down_payment = fields.Many2one('account.payment', 'Refund Down Payment', store='True')
    reverse_move_sales_recongnized = fields.Many2one('account.move', 'Reverse Sales Recognized', store='True')
    refund_discount_payment = fields.Many2one('account.move', 'Refund Discount Payment', store='True')
    reverse_transfer_sales_to_return = fields.Many2one('account.move', 'Reverse Return Office', store='True')
    reverse_move_sales_deferred = fields.Many2one('account.move', 'Reverse Sales Deferred', store='True')

    # ================ constraints =================================
    def apply(self):
        self.ensure_one()
        application_obj = self.application_id

        if self.application_action == 'resell':
            application_obj.state = 'returnbackagain'
        else:
            application_obj.state = 'backtocountry'
            application_obj.previouse_state = 'sellasfinall'


        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
        body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Return Date : <span>""" + (self.return_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Previous Sponsor : <span>""" + self.old_customer_id.name + u"""</span></li>"""
        body_msg += u"""<li>Old Invoice ID : <span>""" + self.old_invoice_id.name + u"""</span></li>"""
        body_msg += u"""<li>Refund Amount : <span>""" + str(self.refund_amount) + u"""</span></li>"""
        body_msg += u"""<li>Salary Amount : <span>""" + str(self.hm_salary) + u"""</span></li>"""

        if self.paid_immediately:
            body_msg += u"""<li>Paid to Sponsor : Yes </li>"""
        else:
            body_msg += u"""<li>Paid to Sponsor : No </li>"""
            body_msg += u"""<li>Expected Pay Date : <span>""" + (self.pay_due_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""

        body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
        body_msg += u"""</ul>"""
        application_obj.message_post(body=body_msg)

        partner_obj = self.old_customer_id
        if partner_obj:
            partner_obj.message_post(body=body_msg)
    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name

    @api.onchange('application_action')
    @api.depends('refund_amount', 'application_action')
    def _disable_refund_amount(self):
        try:
            self.ensure_one()
            if self.application_action != 'resell':
                self.new_customer_id = None
                self.refund_amount = None

        except Exception as e:
            logger.exception("_disable_refund_amount Method")
            raise ValidationError(e)
    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            returnbackfromlastsponsor_obj = super(ReturnBackFromLastSponsor, self).create(vals)

            if returnbackfromlastsponsor_obj.application_action == 'resell':
                if returnbackfromlastsponsor_obj.refund_amount == 0.00:
                    raise ValidationError(
                        _('Refund amount is missing.'))

                #  1.1) Create new movement to register housemaid salary
                #  -------------------------------------------------------
                #  Cr: Housemaid Salary Dues
                #  Dr: Ac Rec.(Partner ID: Sponsor)
                #  Amount: Salary Amount
                #  1.2) Create new movement to post housemaid salary
                #  ---------------------------------------------------------
                #  Cr: Ac Rec. (Partner ID: Sponsor)
                #  Dr: Cash Box Return
                #  Amount: Salary Amount
                # =======================================================================================
                if returnbackfromlastsponsor_obj.hm_salary > 0.0:
                    returnbackfromlastsponsor_obj.hm_salary_move = \
                        accounting_integration.return_back_last_sponsor_move_hm_salary(
                            returnbackfromlastsponsor_obj)
                    returnbackfromlastsponsor_obj.hm_salary_payment = \
                        accounting_integration.return_back_last_sponsor_post_hm_salary(returnbackfromlastsponsor_obj)

                latest_selltest = returnbackfromlastsponsor_obj.env['housemaidsystem.applicant.selltest'].search(
                    [('application_id', '=', returnbackfromlastsponsor_obj.application_id.id)], order="id desc",
                    limit=1)

                # 2- Post refund payment by down payment amount
                # ----------------------------------------------------------------------
                # Cr: Cash
                # Dr: Acc Rec
                # Amount: Down Amount
                # ======================================================================
                if latest_selltest.down_payment_invoice:
                    returnbackfromlastsponsor_obj.refund_down_payment = accounting_integration.return_back_last_sponsor_refund_down_payment(
                        latest_selltest, latest_selltest.down_payment_invoice)


                # 3- Post refund payment for down payment amount
                # ----------------------------------------------------------------------
                # Cr: Cash
                # Dr: Acc Rec
                # Amount: Down payment amount
                # ======================================================================
                if latest_selltest.complete_payment_amount:
                    returnbackfromlastsponsor_obj.refund_complete_payment = accounting_integration.return_back_last_sponsor_refund_complete_payment(
                        latest_selltest,latest_selltest.complete_payment_invoice)
                    accounting_integration.return_back_last_sponsor_sales_invoice_unlink_payment(latest_selltest, latest_selltest.new_invoice_id)

                # 4- Reverse sales invoice
                # ------------------------
                # Cr: Acc Rec
                # Dr: Sales first sponsor
                # Amount: Sales Amount
                # =================================================================
                # returnbackfromlastsponsor_obj.reverse_move_sales_recongnized = accounting_integration.reverse_move(
                #     latest_selltest, latest_selltest.new_invoice_id, 'cancel', 'Return Back From Last Sponsor')

                # 5- Reverse recognized sales income "similar to unlink arrival"
                # ---------------------------------------------------------------
                # Cr: Sales Deferred - arrival
                # Dr: Sales Recognized - arrival
                # Amount: Sales Amount
                # ==============================================================
                returnbackfromlastsponsor_obj.reverse_move_sales_deferred = \
                    accounting_integration.reverse_move(latest_selltest, latest_selltest.invoice_sales_recong_id, 'cancel','Return Back From Last Sponsor')


                # 6- Refund discount "If Any"
                # ---------------------------------------------------------------
                # Dr: Ac rec.
                # Cr: Sales Discount expense
                # Amount: Discount Amount
                # ==============================================================
                if latest_selltest.sepecial_discount_amount > 0.0:
                    returnbackfromlastsponsor_obj.refund_discount_payment = accounting_integration.return_back_last_sponsor_refund_discount(
                        latest_selltest, latest_selltest.sepecial_discount_amount)


                # 7- Move housemaid sales amount to return office GL in order to re-sell later
                # -----------------------------------------------------------------------------
                # Cr: Sales Recognized - Return
                # Dr: Return Office management
                # Amount: Sales amount
                # ======================================================================
                returnbackfromlastsponsor_obj.reverse_transfer_sales_to_return = \
                    accounting_integration.return_back_last_sponsor_transfer_sales_to_return(returnbackfromlastsponsor_obj, latest_selltest)






                # ==============================================================OLD====================================================

                # 2- Create new refund payment to sponsor
                #  --------------------------------------
                #  Cr: Cash box return
                #  Dr: Acc Rec
                #  Amount: Refund Amount
                #==============================================================
                # if returnbackfromlastsponsor_obj.refund_amount > 0.00:
                #     returnbackfromlastsponsor_obj.refund_payment_invoice = \
                #         accounting_integration.return_back_last_sponsor_refund_payment(
                #             returnbackfromlastsponsor_obj)



                # 3- Re-Sell the housemaidsystem for Return Office based on Re-Fund amount
                #  -----------------------------------------------------------------------
                #  Cr: Acc Rec.
                #  Dr: Sales Return Office
                #  Amount: Refund Amount
                # ===================================================================
                # if returnbackfromlastsponsor_obj.refund_amount > 0.00:
                #     returnbackfromlastsponsor_obj.resell_move_id = \
                #         accounting_integration.return_back_last_sponsor_resell(returnbackfromlastsponsor_obj)


                # 2- Create new movement to suspend the cash payment to
                #    account receivable and remove it from cash return
                #  {Dr: Cash box return  / Cr: Acc Rec >> Refund Amount}
                # ==============================================================
                # if returnbackfromlastsponsor_obj.refund_amount > 0.0 and returnbackfromlastsponsor_obj.paid_immediately == False:
                #     returnbackfromlastsponsor_obj.paid_immediately_move = \
                #         accounting_integration.return_back_last_sponsor_move_dr_cash_cr_acctred(
                #             returnbackfromlastsponsor_obj)


            return returnbackfromlastsponsor_obj
        except Exception as e:
            logger.exception("Return Back From Last Sponsor Create Method")
            raise ValidationError(e)


    def write(self, vals):
        try:
            returnbackfromlastsponsor_obj = super(ReturnBackFromLastSponsor, self).write(vals)

            return returnbackfromlastsponsor_obj
        except Exception as e:
            logger.exception("Return Back From Last Sponsor write Method")
            raise ValidationError(e)


    def unlink(self):
        try:
            if self.hm_salary_move:
                accounting_integration.reverse_move(self, self.hm_salary_move,
                                                    'cancel', 'cancel return back from last sponsor.')
            if self.hm_salary_payment:
                self.hm_salary_payment.action_draft()
                self.hm_salary_payment.action_cancel()

            if self.refund_payment_invoice:
                self.refund_payment_invoice.action_draft()
                self.refund_payment_invoice.action_cancel()

            if self.resell_move_id:
                accounting_integration.reverse_move(self, self.resell_move_id,
                                                    'cancel', 'cancel return back from last sponsor.')



            return super(ReturnBackFromLastSponsor, self).unlink()
        except Exception as e:
            logger.exception("Return Back From Last Sponsor unlink Method")
            raise ValidationError(e)