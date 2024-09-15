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


class ReturnBackFromFirstSponsor(models.Model):
    _name = 'housemaidsystem.applicant.returnbackfromfirstsponsor'
    _description = 'Return Back From First Sponsor'

    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    return_date = fields.Date(string="Return Back Date", required=True, default=fields.Date.context_today)
    deliver_date = fields.Date(string="Deliver Date")
    deliver_days = fields.Integer(string="Deliver Days", compute='_calc_days')
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True)
    net_amount = fields.Float(string="Paid By Customer", onchange="_calc_refund_amount", )
    refund_amount = fields.Float(string="Refund Amount", onchange="_calc_refund_amount",)
    refund_payment_invoice = fields.Many2one('account.payment', 'Refund Payment Invoice')
    previouse_discount = fields.Float(string="Invoice Discount", default=0)
    previouse_discount_inv_id = fields.Many2one('account.move', 'Purchase Recognized Move', store='True')
    new_recv_inv_id = fields.Many2one('account.move', 'Cash box Move', store='True')
    cash_box_move_id = fields.Many2one('account.move', 'Cash Box Move', store='True')
    notes = fields.Text(string="Notes")
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor")
    customer_name_ar = fields.Char(related='customer_id.name_ar')
    new_customer_id = fields.Many2one(comodel_name="res.partner", string="New Sponsor")
    invoice_id = fields.Many2one('account.move', 'Invoice No.', store='True')
    invoice_state = fields.Selection(related="invoice_id.state", string="Invoice Status")
    invoice_total = fields.Monetary(related="invoice_id.amount_total", string="Invoice Amount",
                                    currency_field='currency_id')
    invoice_due = fields.Monetary(related="invoice_id.amount_residual", string="Sales Invoice Due Amount",
                                  currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related="invoice_id.currency_id")
    insurance = fields.Selection(string="Action Taken", selection=[('insurance',
                                                                        'Insurance - (Refund amount equal to sales amount)'),
                                                                    ('insurance-greater',
                                                                        'Insurance - (Refund amount greater than sales amount)'),
                                                                    ('insurance-smaller',
                                                                        'Insurance - (Refund amount less than sales amount)'),],
                                 required=True, default='insurance', )



    close_return_back_balance = fields.Boolean(string="To Close balance of deliver reject",
                                                  default=False, )
    sales_reverse_move = fields.Many2one('account.move', 'Sales Returned', store='True')
    purchase_reverse_move = fields.Many2one('account.move', 'Purchase Returned', store='True')
    hm_salary = fields.Float(string="Salary Amount", default=0.0, onchange="_calc_total_amount",)
    hm_salary_move = fields.Many2one('account.move', 'Salary move', store='True')
    hm_salary_payment = fields.Many2one('account.payment', 'Salary payment', store='True')
    total_amount = fields.Float(string="Total Dues")
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)

    paid_immediately = fields.Boolean(string="Paid To Sponsor", default=False, )
    pay_due_date = fields.Date(string="Expected Pay Date", required=True, default=fields.Date.context_today)
    paid_immediately_move = fields.Many2one('account.move', 'Suspend Payment Move', store='True')
    refund_down_payment = fields.Many2one('account.payment', 'Refund Down Payment', store='True')
    refund_complete_payment = fields.Many2one('account.payment', 'Refund Complete Payment', store='True')
    reverse_move_sales_recongnized = fields.Many2one('account.move', 'Reverse Sales Recognized', store='True')
    reverse_move_sales_deferred = fields.Many2one('account.move', 'Reverse Sales Deferred', store='True')
    refund_discount_payment_first = fields.Many2one('account.move', 'Refund Deliver Discount Payment', store='True')
    pay_extra_less = fields.Many2one('account.payment', 'Pay Extra\Less Payment', store='True')
    register_gain_loss = fields.Many2one('account.move', 'Register gain\loss', store='True')
    reverse_transfer_sales_to_return = fields.Many2one('account.move', 'Reverse Return Office', store='True')

    # ================ constraints =================================
    _sql_constraints = [
            ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
      ]


    def _get_labor_dtl(self):
        try:
            for record in self:
                if not record.application_id == None:
                    self.office_code = record.application_id.office_code
        except Exception as e:
            logger.exception("_get_labor_dtl Method")
            raise ValidationError(e)

    def apply(self):
        self.ensure_one()
        application_obj = self.application_id

        if self.insurance == 'insurance' or self.insurance == 'insurance-greater' or self.insurance == 'insurance-smaller':
            application_obj.state = 'returnback'

        if self.insurance == 'insurance-back-to-country' or self.insurance == 'out-insurance':
            application_obj.state = 'backtocountry'
            application_obj.previouse_state = 'deliverpaidfull'

        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
        body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Return Back Date : <span>""" + (self.return_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""

        body_msg += u"""<li>Deliver Date : <span>""" + (self.deliver_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""

        body_msg += u"""<li>First Sponsor : <span>""" + self.customer_id.name + u"""</span></li>"""

        body_msg += u"""<li>Invoice ID : <span>""" + self.invoice_id.name + u"""</span></li>"""

        body_msg += u"""<li>Invoice Status : <span>""" + self.invoice_state + u"""</span></li>"""

        body_msg += u"""<li>Deal Amount : <span>""" + str(self.invoice_total) + u"""</span></li>"""

        body_msg += u"""<li>Due Amount : <span>""" + str(self.invoice_due) + u"""</span></li>"""

        body_msg += u"""<li>Action Taken : <span>""" + self.insurance + u"""</span></li>"""

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

        partner_obj = self.customer_id
        if partner_obj:
            partner_obj.message_post(body=body_msg)
        partner_obj = self.new_customer_id
        if partner_obj:
            partner_obj.message_post(body=body_msg)
    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name


    @api.depends('deliver_date')
    def _calc_days(self):
        try:
            for record in self:
                self.deliver_days = (datetime.date.today() - record.deliver_date).days
        except Exception as e:
            logger.exception("_calc_days Method")
            raise ValidationError(e)

    @api.onchange('hm_salary', 'refund_amount')
    @api.depends('total_amount', 'refund_amount')
    def _calc_total_amount(self):
        try:
            self.ensure_one()
            self.total_amount = self.refund_amount + self.hm_salary

        except Exception as e:
            logger.exception("onchange_calc_total_amount Method")
            raise ValidationError(e)

    @api.onchange('insurance')
    @api.depends('refund_amount', 'notes', 'insurance', 'net_amount','hm_salary')
    def _calc_refund_amount(self):
        try:
            self.ensure_one()

            if self.insurance == 'insurance':
                self.notes = 'Return back during insurance period (Equal): refund amount to sponsor will be equal ' \
                             'to paid by customer amount (invoice amount - discount).'
                self.net_amount = self.invoice_total - self.previouse_discount
                self.refund_amount = self.net_amount
                self.total_amount = self.refund_amount + self.hm_salary

            elif self.insurance == 'insurance-greater':
                self.notes = 'Return back during insurance period (Greater): refund amount to sponsor will be greater than paid by customer amount (invoice amount - discount).'
                self.net_amount = self.invoice_total - self.previouse_discount
                self.refund_amount = 0.0
                self.total_amount = self.refund_amount + self.hm_salary

            elif self.insurance == 'insurance-smaller':
                self.notes = 'Return back during insurance period (Smaller): refund amount will ' \
                             'be less than paid by customer (invoice amount - discount).'
                self.net_amount = self.invoice_total - self.previouse_discount
                self.refund_amount = 0.0
                self.total_amount = self.refund_amount + self.hm_salary

            else:
                self.net_amount = self.invoice_total - self.previouse_discount
                self.refund_amount = 0.0
                self.total_amount = self.refund_amount + self.hm_salary

        except Exception as e:
            logger.exception("onchange_calc_refund_amount Method")
            raise ValidationError(e)

    def validations(self, returnbackfromfirstsponsor_obj):
        try:
            valid = True
            if returnbackfromfirstsponsor_obj.insurance == 'insurance':
                if returnbackfromfirstsponsor_obj.refund_amount != (returnbackfromfirstsponsor_obj.invoice_total-returnbackfromfirstsponsor_obj.previouse_discount):
                    valid = False
                    raise ValidationError("Refund amount should be equal to paid by customer amount %.3f (paid by customer amount = invoice amount - discount)" % (
                            returnbackfromfirstsponsor_obj.invoice_total-returnbackfromfirstsponsor_obj.previouse_discount))


            if returnbackfromfirstsponsor_obj.insurance == 'insurance-greater':
                if returnbackfromfirstsponsor_obj.refund_amount <= (returnbackfromfirstsponsor_obj.invoice_total-returnbackfromfirstsponsor_obj.previouse_discount):
                    valid = False
                    raise ValidationError("Refund amount should be greater than paid by customer amount %.3f (paid by customer amount = invoice amount - discount)" % (
                                returnbackfromfirstsponsor_obj.invoice_total - returnbackfromfirstsponsor_obj.previouse_discount))

            if returnbackfromfirstsponsor_obj.insurance == 'insurance-smaller':
                if returnbackfromfirstsponsor_obj.refund_amount >= (
                        returnbackfromfirstsponsor_obj.invoice_total - returnbackfromfirstsponsor_obj.previouse_discount):
                    valid = False
                    raise ValidationError("Refund amount should be less than sales amount %.3f (paid by customer amount = invoice amount - discount)" % (
                            returnbackfromfirstsponsor_obj.invoice_total - returnbackfromfirstsponsor_obj.previouse_discount))

            return valid
        except Exception as e:
            logger.exception("validations method")
            raise ValidationError(e)

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            returnbackfromfirstsponsor_obj = super(ReturnBackFromFirstSponsor, self).create(vals)

            if self.validations(returnbackfromfirstsponsor_obj) == True:

                # Posting Summary:
                # ================
                # 1- Create new movement to register & post housemaid salary
                # 2- Post refund payment by down payment amount
                # 3- Post refund payment by complete payment amount
                # 4- Reverse sales invoice
                # 5- Reverse recognized sales income "similar to unlink arrival"
                # 6- Refund discount "If Any"
                # 7- Move housemaid sales amount to return office GL in order to re-sell later



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
                if returnbackfromfirstsponsor_obj.hm_salary > 0.0:
                    returnbackfromfirstsponsor_obj.hm_salary_move = \
                        accounting_integration.return_back_move_hm_salary(
                            returnbackfromfirstsponsor_obj)
                    returnbackfromfirstsponsor_obj.hm_salary_payment = \
                        accounting_integration.return_back_post_hm_salary(returnbackfromfirstsponsor_obj)



                if returnbackfromfirstsponsor_obj.insurance == 'insurance' or \
                        returnbackfromfirstsponsor_obj.insurance == 'insurance-greater' or \
                        returnbackfromfirstsponsor_obj.insurance == 'insurance-smaller':

                    post_discount_amount = returnbackfromfirstsponsor_obj.previouse_discount \
                        if returnbackfromfirstsponsor_obj.previouse_discount else 0.0

                    post_invoice_total_after_discount = returnbackfromfirstsponsor_obj.invoice_total - post_discount_amount
                    post_refund_amount_after_total_sale = returnbackfromfirstsponsor_obj.refund_amount - post_invoice_total_after_discount


                    reservation = self.env['housemaidsystem.applicant.reservations']. \
                        search([('application_id', '=', returnbackfromfirstsponsor_obj.application_id.id)], limit=1)

                    # =============================== NEW===================================
                    # 2- Post refund payment by down payment amount
                    # ----------------------------------------------------------------------
                    # Cr: Cash
                    # Dr: Acc Rec
                    # Amount: Down Amount
                    # ======================================================================
                    returnbackfromfirstsponsor_obj.refund_down_payment = accounting_integration.reservation_refund_down_payment(reservation,
                                                                           reservation.down_payment_invoice)
                    # 3- Post refund payment by complete payment amount
                    # ----------------------------------------------------------------------
                    # Cr: Cash
                    # Dr: Acc Rec
                    # Amount: Complete payment amount
                    # ======================================================================
                    deliver = self.env['housemaidsystem.applicant.deliver']. \
                        search([('application_id', '=', returnbackfromfirstsponsor_obj.application_id.id)], limit=1)

                    if deliver.paid_payment_invoice:
                        returnbackfromfirstsponsor_obj.refund_complete_payment=accounting_integration.deliver_refund_complete_payment(deliver,
                                                                               deliver.paid_payment_invoice)
                        accounting_integration.deliver_sales_invoice_unlink_payment(deliver, deliver.invoice_id)


                    # 4- Reverse sales invoice
                    # ------------------------
                    # Cr: Acc Rec
                    # Dr: Sales first sponsor
                    # Amount: Sales Amount
                    # =================================================================
                    returnbackfromfirstsponsor_obj.reverse_move_sales_recongnized = accounting_integration.reverse_move(reservation, reservation.invoice_sales_id,
                                                        'cancel','Return Back From First Sponsor')


                    # 5- Reverse recognized sales income "similar to unlink arrival"
                    # ---------------------------------------------------------------
                    # Cr: Sales Deferred - arrival
                    # Dr: Sales Recognized - arrival
                    # Amount: Sales Amount
                    # ==============================================================
                    arrival = self.env['housemaidsystem.applicant.arrival']. \
                        search([('application_id', '=', returnbackfromfirstsponsor_obj.application_id.id)], limit=1)
                    returnbackfromfirstsponsor_obj.reverse_move_sales_deferred = accounting_integration.reverse_move(arrival, arrival.sales_move, 'cancel',
                                                        'Return Back From First Sponsor')

                    # 6- Refund discount "If Any"
                    # ---------------------------------------------------------------
                    # Dr: Ac rec.
                    # Cr: Sales Discount expense
                    # Amount: Discount Amount
                    # ==============================================================
                    if deliver.discount_amount > 0.0:
                        returnbackfromfirstsponsor_obj.refund_discount_payment_first = \
                            accounting_integration.return_back_refund_discount(deliver, deliver.discount_amount)

                    # 7- Move housemaid sales amount to return office GL in order to re-sell later
                    # -----------------------------------------------------------------------------
                    # Cr: Sales Recognized - arrival
                    # Dr: Return Office management
                    # Amount: Sales amount
                    # ======================================================================
                    returnbackfromfirstsponsor_obj.reverse_transfer_sales_to_return = accounting_integration.return_back_transfer_sales_to_return(deliver)


                    if returnbackfromfirstsponsor_obj.insurance == 'insurance-greater':
                        returnbackfromfirstsponsor_obj.pay_extra_less = accounting_integration.return_back_pay_extra(returnbackfromfirstsponsor_obj, post_refund_amount_after_total_sale)
                        returnbackfromfirstsponsor_obj.register_gain_loss = accounting_integration.return_back_move_register_gain_loss(returnbackfromfirstsponsor_obj, post_refund_amount_after_total_sale, 'loss')

                    if returnbackfromfirstsponsor_obj.insurance == 'insurance-smaller':
                        returnbackfromfirstsponsor_obj.pay_extra_less = accounting_integration.return_back_pay_less(returnbackfromfirstsponsor_obj, abs(post_refund_amount_after_total_sale))
                        returnbackfromfirstsponsor_obj.register_gain_loss = accounting_integration.return_back_move_register_gain_loss(returnbackfromfirstsponsor_obj, abs(post_refund_amount_after_total_sale), 'gain')



                return returnbackfromfirstsponsor_obj
        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)


    def write(self, vals):
        try:
            returnbackfromfirstsponsor_obj = super(ReturnBackFromFirstSponsor, self).write(vals)
            return returnbackfromfirstsponsor_obj
        except Exception as e:
            logger.exception("Return Back From First Sponsor write Method")
            raise ValidationError(e)


    def unlink(self):
        try:
            if self.hm_salary_move:
                accounting_integration.reverse_move(self, self.hm_salary_move,
                                                    'cancel', 'cancel return back from first sponsor.')

            if self.hm_salary_payment:
                self.hm_salary_payment.action_draft()
                self.hm_salary_payment.action_cancel()

            if self.refund_down_payment:
                self.refund_down_payment.action_draft()
                self.refund_down_payment.action_cancel()

            if self.refund_complete_payment:
                self.refund_complete_payment.action_draft()
                self.refund_complete_payment.action_cancel()

            if self.reverse_move_sales_recongnized:
                accounting_integration.reverse_move(self, self.reverse_move_sales_recongnized,
                                                    'cancel', 'cancel return back from first sponsor.')
            if self.reverse_move_sales_deferred:
                accounting_integration.reverse_move(self, self.reverse_move_sales_deferred,
                                                    'cancel', 'cancel return back from first sponsor.')

            if self.refund_discount_payment_first:
                self.refund_discount_payment_first.action_draft()
                self.refund_discount_payment_first.action_cancel()

            if self.pay_extra_less:
                self.pay_extra_less.action_draft()
                self.pay_extra_less.action_cancel()

            if self.register_gain_loss:
                accounting_integration.reverse_move(self, self.register_gain_loss,
                                                    'cancel', 'cancel return back from first sponsor.')

            if self.reverse_transfer_sales_to_return:
                accounting_integration.reverse_move(self, self.reverse_transfer_sales_to_return,
                                                    'cancel', 'cancel return back from first sponsor.')

            # Tb do it later, link available payments to current inoice
            # accounting_integration.deliver_sales_invoice_link_payments(self, self.invoice_id)




            return super(ReturnBackFromFirstSponsor, self).unlink()
        except Exception as e:
            logger.exception("Return Back From First Sponsor unlink Method")
            raise ValidationError(e)