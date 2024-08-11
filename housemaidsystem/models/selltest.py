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


class SellTest(models.Model):
    _name = 'housemaidsystem.applicant.selltest'
    _description = 'Deliver Housemaid To New Sponsor As Test'

    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    test_date = fields.Date(string="Sell Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True)
    notes = fields.Text(string="Notes")
    down_payment_amount = fields.Float(string="Down Payment", required=False, default=0)
    down_payment_invoice = fields.Many2one('account.payment', 'Down Payment Invoice')
    complete_payment_amount = fields.Float(string="Remaining Payment", required=False, default=0)
    complete_payment_invoice = fields.Many2one('account.payment', 'Remaining Payment Invoice')
    old_customer_id = fields.Many2one(comodel_name="res.partner", string="Current Sponsor")
    new_customer_id = fields.Many2one(comodel_name="res.partner", string="New Sponsor", required=True, domain=[('customer_rank','>', 0)])
    old_invoice_id = fields.Many2one('account.move', 'Old Invoice', store='True')
    new_invoice_id = fields.Many2one('account.move', 'New Invoice', store='True')
    deal_amount = fields.Float(string="Deal Amount", required=True, default=0)
    sales_man = fields.Many2one(comodel_name="res.users", string="Sales Man", required=True,
                                default=lambda self: self.env.user)
    old_invoice_state = fields.Selection(related="old_invoice_id.state", string="Old Invoice Status")
    old_invoice_total = fields.Monetary(related="old_invoice_id.amount_total", string="Old Invoice Total Amount",
                                        currency_field='currency_id')
    old_invoice_due = fields.Monetary(related="old_invoice_id.amount_residual", string="Old Invoice Due Amount",
                                      currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related="old_invoice_id.currency_id")
    rec_status = fields.Selection(string='Record Status', selection=[('active', 'Active'), ('inactive', 'In-Active')],
                                  default='inactive')
    invoice_sales_recong_id = fields.Many2one('account.move', 'Sales Recognized Move', store='True')
    close_deliver_reject_balance_move = fields.Many2one('account.move', 'Purchase Recognized Move', store='True')
    previous_refund = fields.Float(string="Previous Refund Amount", required=False, default=0)
    reject_date = fields.Date(string="Rejection Date", required=True, default=fields.Date.context_today)
    accept_date = fields.Date(string="Acceptance Date", required=True, default=fields.Date.context_today)
    rejection_refund_amount = fields.Float(string="Refund Amount", required=False, default=0,
                                           onchange="_calc_hm_salary", )
    rejection_refund_amount_payment = fields.Many2one('account.payment', 'Refund Amount Payment', store='True')
    sepecial_discount_amount = fields.Float(string="Special Discount", required=False, default=0)
    sepecial_discount_amount_move = fields.Many2one('account.move', 'Special Discount Move', store='True')
    test_status = fields.Selection(string='Test Status',
                                   selection=[('selectaction', 'Select Action'), ('accepted', 'Test Accepted'),
                                              ('rejected', 'Test Rejected')
                                              ], default='selectaction')
    sell_as_test_down_payment_refund = fields.Many2one('account.payment', 'Down Payment Invoice Refund')
    hm_salary_move = fields.Many2one('account.move', 'Housemaid Salary Move', store='True')
    hm_salary_payment = fields.Many2one('account.payment', 'Housemaid Salary Move', store='True')
    hm_salary = fields.Float(string="Salary Amount", default=0.0, )
    sell_reject_profit_loss_move = fields.Many2one('account.move', 'Re-Sell Testing Rejecting - Profit & Loss', store='True')

    # ==================  Main Functions ==========================
    def apply(self):
        self.ensure_one()
        application_obj = self.application_id


        if not self.new_customer_id:
            raise ValidationError("Sponsor is missing.")
        else:
            # if not self.new_customer_id.civil_id:
            #     raise ValidationError("New Sponsor Civil ID is missing.")
            # elif not len(self.new_customer_id.civil_id) == 12:
            #     raise ValidationError("New Sponsor Civil ID is wrong.")
            # elif not self.new_customer_id.mobile:
            #     raise ValidationError("New Sponsor Mobile is missing.")
            # elif self.new_customer_id.mobile.startswith('1') or self.new_customer_id.mobile.startswith('2'):
            #     raise ValidationError("Sponsor Mobile is wrong.")
            if self.new_customer_id.is_black_list:
                raise ValidationError("New Sponsor is black listed.")

        if application_obj.state == 'returnback' or application_obj.state == 'returnbackagain' or application_obj.state == 'resell':
            if application_obj.state == 'returnback':
                application_obj.state = 'sellastest'
                application_obj.previouse_state = 'returnback'
            elif application_obj.state == 'returnbackagain':
                application_obj.state = 'sellastest'
                application_obj.previouse_state = 'returnbackagain'
            else:
                application_obj.state = 'sellastest'
                application_obj.previouse_state = 'resell'

            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Sell As Test Date : <span>""" + (self.test_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Old Sponsor : <span>""" + self.old_customer_id.name + u"""</span></li>"""
            body_msg += u"""<li>Old Sponsor Invoice ID : <span>""" + self.old_invoice_id.name + u"""</span></li>"""
            body_msg += u"""<li>Old Invoice Status : <span>""" + self.old_invoice_state + u"""</span></li>"""
            body_msg += u"""<li>Old Deal Amount : <span>""" + str(self.old_invoice_total) + u"""</span></li>"""
            body_msg += u"""<li>Old Due Amount : <span>""" + str(self.old_invoice_due) + u"""</span></li>"""

            body_msg += u"""<li>Previous Refund Amount : <span>""" + str(
                self.previous_refund if self.previous_refund else 0) + u"""</span></li>"""

            body_msg += u"""<li>New Sponsor : <span>""" + self.new_customer_id.name + u"""</span></li>"""
            body_msg += u"""<li>New Sponsor Invoice ID : <span>""" + self.new_invoice_id.name if self.new_invoice_id.name else '' + u"""</span></li>"""
            body_msg += u"""<li>New Deal Amount : <span>""" + str(
                self.deal_amount if self.deal_amount else 0) + u"""</span></li>"""
            body_msg += u"""<li>Down Payment Amount : <span>""" + str(
                self.down_payment_amount if self.down_payment_amount else 0) + u"""</span></li>"""
            body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
            body_msg += u"""</ul>"""
            application_obj.message_post(body=body_msg)
            partner_obj = self.old_customer_id
            if partner_obj:
                partner_obj.message_post(body=body_msg)
            partner_obj = self.new_customer_id
            if partner_obj:
                partner_obj.message_post(body=body_msg)
            print(self.new_customer_id)
            contracts_print = self.env['housemaidsystem.configuration.contracts_print']
            contracts_print_data = {
                'name': 'Contract of customer# ' + self.new_customer_id.name + ' For Housemaid #' + application_obj.full_name,
                'application_id': application_obj.id,
                'customer_id': self.new_customer_id.id,
            }
            contracts_print.create(contracts_print_data)
        else:
            if application_obj.state == 'sellastest' and self.test_status == 'rejected':
                application_obj.state = application_obj.previouse_state

                body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
                body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""
                body_msg += u"""<li>Sell As Test Rejection Date : <span>""" + (self.reject_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""
                body_msg += u"""<li>Test Action : <span> New customer is rejected.</span></li>"""
                body_msg += u"""<li>Refund Amount : <span>""" + str(
                    self.rejection_refund_amount if self.rejection_refund_amount else 0) + u"""</span></li>"""
                body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
                body_msg += u"""</ul>"""
                application_obj.message_post(body=body_msg)
                partner_obj = self.old_customer_id
                if partner_obj:
                    partner_obj.message_post(body=body_msg)
                partner_obj = self.new_customer_id
                if partner_obj:
                    partner_obj.message_post(body=body_msg)

            if application_obj.state == 'sellastest' and self.test_status == 'accepted':
                application_obj.state = 'sellasfinall'

                body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
                body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""
                body_msg += u"""<li>Sell As Test Accepted Date : <span>""" + (self.accept_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""
                body_msg += u"""<li>Test Action : <span> New customer is accepted.</span></li>"""
                body_msg += u"""<li>Paid Amount : <span>""" + str(
                    self.complete_payment_amount if self.complete_payment_amount else 0) + u"""</span></li>"""
                body_msg += u"""<li>Discount Amount : <span>""" + str(
                    self.sepecial_discount_amount if self.sepecial_discount_amount else 0) + u"""</span></li>"""
                body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
                body_msg += u"""</ul>"""
                application_obj.message_post(body=body_msg)

                partner_obj = self.old_customer_id
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

    @api.onchange('test_status')
    @api.depends('rejection_refund_amount', 'down_payment_amount')
    def _calc_refund_amount(self):
        try:
            self.ensure_one()
            self.rejection_refund_amount = self.down_payment_amount

        except Exception as e:
            logger.exception("_calc_refund_amount Method")
            raise ValidationError(e)

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):

        if vals.get('deal_amount') == 0:
            raise ValidationError(_('Deal amount is Missing.'))

        selltest_obj = super(SellTest, self).create(vals)
        if selltest_obj.old_customer_id == selltest_obj.new_customer_id:
            raise ValidationError("New sponsor is same of old sponsor.")

        # 1- Create new sales invoice
        # -----------------------------
        #  Cr: Sales Deferred - Return
        #  Dr: Acc Rec
        #  Amount: Sales Amount
        # ===================================================================
        selltest_obj.new_invoice_id = accounting_integration.selltest_invoice_inoice_creation(selltest_obj)

        # 2- Register invoice Down Payment
        # ---------------------------------
        #  Cr: Acc Rec
        #  Dr: Cash Return
        #  Amount: Down Payment Amount
        # ========================================================
        if selltest_obj.down_payment_amount != 0:
            selltest_obj.down_payment_invoice = accounting_integration.selltest_sales_invoice_payment \
                (selltest_obj, selltest_obj.down_payment_amount, selltest_obj.new_invoice_id)



        # 3) Update current sponsor in table Application
        # ----------------------------------------------
        selltest_obj.application_id.customer_id = selltest_obj.new_customer_id.id


        return selltest_obj

    def write(self, vals):
        try:
            selltest_obj = super(SellTest, self).write(vals)

            if vals.get('test_status') and vals.get('test_status') == 'rejected':

                # 1- Refund down payment (without housemaidsystem salary)
                # ---------------------------------------------------------
                #  Cr: Cash Return
                #  Dr: Acc Rec
                #  Amount: Down Payment
                # ===================================================================
                if self.down_payment_amount and self.down_payment_amount > 0.0:
                    self.rejection_refund_amount_payment = \
                        accounting_integration.selltest_rejection_sales_invoice_reverse_payment(self)

                # 2- Post the diff between down payment & actual refund amount
                # ---------------------------------------------------------
                #  Cr: Acc Rec
                #  Dr: Sales Deferred Return
                #  Amount: down_payment_amount - rejection_refund_amount
                # ===================================================================
                if self.down_payment_amount and self.down_payment_amount > 0.0:
                    if self.rejection_refund_amount and self.rejection_refund_amount > 0.0:
                        action = 'match'
                        if self.rejection_refund_amount > self.down_payment_amount:
                            action = 'loss'
                        elif self.rejection_refund_amount < self.down_payment_amount:
                            action = 'profit'
                        else:
                            action = 'match'
                        if action != 'match':
                            self.sell_reject_profit_loss_move = \
                                accounting_integration.selltest_rejection_move_diff_posting(self, action)

                # 3- Create new movement to record housemaidsystem salary - Part 1
                # ----------------------------------------------------------------
                #  Cr: Housemaid Salary Dues (Liability)
                #  Dr: Account Rec.
                #  Amount: Housemaid Salary
                # ================================================================
                if self.hm_salary and self.hm_salary > 0.0:
                    self.hm_salary_move = \
                        accounting_integration.selltest_rejection_move_hm_salary(self)

                # 4- Create new movement to record housemaidsystem salary - Part 2
                # -----------------------------------------------------------------
                #  Cr: Account Rec.
                #  Dr: Cash Box (Cash In)
                #  Amount: Housemaid Salary
                # ================================================================
                if self.hm_salary and self.hm_salary > 0.0:
                    self.hm_salary_payment = \
                        accounting_integration.selltest_post_hm_salary(self)

                # 5- Cancel Sell Invoice
                # ----------------------
                #  Cr: Acc Rec
                #  Dr: Sales Deferred Return
                #  Amount: invoice Amount
                # ===================================================================
                accounting_integration.reverse_move(self, self.new_invoice_id,
                                                    'cancel', 'Sponsor reject after test.')
                # self.new_invoice_id.action_invoice_cancel()

                # 6- Change record status to active
                # =====================================
                self.rec_status = 'active'

                # 7- Update current sponsor in table Application to previous sponsor
                # ==================================================================
                self.application_id.customer_id = self.old_customer_id.id



            if vals.get('test_status') and vals.get('test_status') == 'accepted':

                # 1- Create movement to recognized the sale action
                # ------------------------------------------------
                #  Cr: Sales Recognized - Return
                #  Dr: Sales Deferred - Return
                #  Amount: Sales Amount
                # ===================================================================
                self.invoice_sales_recong_id = accounting_integration.selltest_accept_move_sales_recongnized(self)

                # 2- Create movement to recognized the sale action
                # ------------------------------------------------
                # Cr: Return Office Management
                # Dr: Return Purchase Office
                # Amount: Purchase Amount
                # ====================================================================
                self.close_deliver_reject_balance_move = accounting_integration.selltest_accept_maove_sales_close_deliver(
                    self)

                # 3- Post sponsor full payment
                # ------------------------------
                #  Cr: Acc Rec.
                #  Dr: Cash Return
                #  Amount: Complete payment = sales amount - (Down payment - Discount Amount)
                # ===============================================================================================
                self.complete_payment_amount = self.deal_amount - \
                                               self.down_payment_amount - self.sepecial_discount_amount
                if self.complete_payment_amount > 0.0:
                    self.complete_payment_invoice = \
                        accounting_integration.selltest_accept_sales_invoice_complete_payment(self)




                self.rec_status = 'active'
                self.application_id.customer_id = self.new_customer_id.id

            return selltest_obj
        except Exception as e:
            logger.exception("Sell As Test Write Method")
            raise ValidationError(e)


    def unlink(self):
        if self.test_status == 'rejected':
            self.rec_status = 'active'

        # app = self.env['housemaidsystem.applicant.applications'].search([('id', '=', self.application_id.id)], limit=1)
        # if app and self.old_customer_id:
        #     app.customer_id = self.old_customer_id.id
        return super(SellTest, self).unlink()
