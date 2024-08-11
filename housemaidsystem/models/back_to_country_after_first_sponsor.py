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


class BackToCountryAfterFirstSponsor(models.Model):
    _name = 'housemaidsystem.applicant.backtocountryafterfirstsponsor'
    _description = 'Back To Country After First Sponsor'

    name = fields.Char(string="Name", compute='_compute_name')
    back_to_country_date = fields.Date(string="Back To Country Date", required=True, default=fields.Date.context_today)
    return_date = fields.Date(string="Return Back Date")
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True)
    action = fields.Selection(string="Action Taken",
                              selection=[('insurance-back-to-country',
                                          'Insurance - (Back to country during insurance period of external office.)'),
                                         ('out-insurance',
                                          'No Insurance - (Back to country after insurance period of external office)'),],
                              required=True, default='insurance-back-to-country', )
    refund_amount = fields.Float(string="Refunded Amount")
    net_amount = fields.Float(string="Net Amount", onchange="_calc_refund_amount", )
    notes = fields.Text(string="Notes")
    previouse_discount = fields.Float(string="Invoice Discount", default=0)
    previouse_discount_inv_id = fields.Many2one('account.move', 'Purchase Recognized Move', store='True')
    sales_reverse_move = fields.Many2one('account.move', 'Sales Returned', store='True')
    sales_diff_move = fields.Many2one('account.move', 'Sales Diff', store='True')
    purchase_reverse_move = fields.Many2one('account.move', 'Purchase Returned', store='True')
    refund_payment_invoice = fields.Many2one('account.payment', 'Refund Payment Invoice')
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor")
    invoice_id = fields.Many2one('account.move', 'Invoice No.', store='True')
    invoice_state = fields.Selection(related="invoice_id.state", string="Invoice Status")
    invoice_total = fields.Monetary(related="invoice_id.amount_total", string="Invoice Amount",
                                    currency_field='currency_id')
    invoice_due = fields.Monetary(related="invoice_id.amount_residual", string="Sales Invoice Due Amount",
                                  currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related="invoice_id.currency_id")


    # ================ constraints =================================
    # _sql_constraints = [
    #         ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
    #   ]

    def apply(self):
        self.ensure_one()
        application_obj = self.application_id

        application_obj.state = 'backtocountry'
        application_obj.previouse_state = 'returnback'


        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
        body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Back to Country Date : <span>""" + (self.back_to_country_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Action Taken : <span>""" + self.action + u"""</span></li>"""
        body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""

        body_msg += u"""</ul>"""
        application_obj.message_post(body=body_msg)

    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name
            
    @api.onchange('action')
    @api.depends('notes', 'action')
    def _calc_refund_amount(self):
        try:
            self.ensure_one()

            if self.action == 'insurance-back-to-country':
                self.notes = 'Back to country during insurance period of External Office: The cost of housemaidsystem will ' \
                             'deducted from external office and sales amount will not recognized.'


            if self.action == 'out-insurance':
                self.notes = 'Back to country after insurance period of External Office (Back to country): refund amount to sponsor is zero, ' \
                             'office accountant will purchase ticket for housemaidsystem later, ' \
                             'housemaidsystem status will change to Back To Country.'


        except Exception as e:
            logger.exception("onchange_calc_refund_amount Method")
            raise ValidationError(e)

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            None
            # backtocountryafterfirstsponsor_obj = super(BackToCountryAfterFirstSponsor, self).create(vals)
            #
            # if backtocountryafterfirstsponsor_obj.action == 'insurance-back-to-country':
            #
            #     # 1) Create new movement for closing Housemaid Returned Office Management in Sales returned Items
            #     #  {Cr: Housemaid Returned Office Management / Dr: Acc Rec >> Sales returned Items}
            #     # ===============================================================================================
            #     backtocountryafterfirstsponsor_obj.sales_reverse_move = \
            #         accounting_integration.back_to_country_after_first_sponsor_move_reverse_sales_in_sales_retun(
            #             backtocountryafterfirstsponsor_obj)
            #
            #     # 2) Create new movement for closing the different between actual refunded amount and Sales Returned Fund
            #     #  Greater Than >> {Cr: Housemaid Returned Office Management / Dr: Acc Rec >> Sales returned Items}
            #     # ===============================================================================================
            #     returnbackfromfirstsponsor_obj = self.env['housemaidsystem.applicant.returnbackfromfirstsponsor'].\
            #         search([('application_id', '=', backtocountryafterfirstsponsor_obj.application_id.id)], limit=1)
            #     if returnbackfromfirstsponsor_obj:
            #         posting_amount = returnbackfromfirstsponsor_obj.refund_amount + returnbackfromfirstsponsor_obj.previouse_discount
            #         if posting_amount:
            #             backtocountryafterfirstsponsor_obj.sales_diff_move = \
            #                 accounting_integration.back_to_country_after_first_diff_posting\
            #                     (backtocountryafterfirstsponsor_obj, posting_amount,
            #                      returnbackfromfirstsponsor_obj.insurance)
            #
            #     # 3) Create new movement for reversing purchase (without canceling Purchase Invoice)
            #     #  {Cr: Purchases Returned Items Account  / Dr: Main External Office Account >> sales amount}
            #     # ===============================================================================================
            #     backtocountryafterfirstsponsor_obj.purchase_reverse_move = \
            #         accounting_integration.back_to_country_after_first_sponsor_move_reverse_purchase(
            #             backtocountryafterfirstsponsor_obj)
            #
            # if backtocountryafterfirstsponsor_obj.action == 'out-insurance':
            #     # 1) Create new movement for closing Housemaid Returned Office Management in Sales Arrival
            #     #  {Cr: Housemaid Returned Office Management / Dr: Sales Arrival}
            #     # ===============================================================================================
            #     backtocountryafterfirstsponsor_obj.sales_reverse_move = \
            #         accounting_integration.back_to_country_after_first_sponsor_move_reverse_sales_in_retun_office(
            #             backtocountryafterfirstsponsor_obj)
            #
            #     # 2) Create new movement for closing the different between actual refunded amount and Sales Returned Fund
            #     #  Greater Than >> {Cr: Housemaid Returned Office Management / Dr: Acc Rec >> Sales returned Items}
            #     # ===============================================================================================
            #     returnbackfromfirstsponsor_obj = self.env['housemaidsystem.applicant.returnbackfromfirstsponsor']. \
            #         search([('application_id', '=', backtocountryafterfirstsponsor_obj.application_id.id)], limit=1)
            #     if returnbackfromfirstsponsor_obj:
            #         posting_amount = returnbackfromfirstsponsor_obj.refund_amount + returnbackfromfirstsponsor_obj.previouse_discount
            #         if posting_amount:
            #             backtocountryafterfirstsponsor_obj.sales_diff_move = \
            #                 accounting_integration.back_to_country_after_first_diff_posting \
            #                     (backtocountryafterfirstsponsor_obj, posting_amount,
            #                      returnbackfromfirstsponsor_obj.insurance)
            #
            # return backtocountryafterfirstsponsor_obj

        except Exception as e:
            logger.exception("Back to country create Method")
            raise ValidationError(e)


    def write(self, vals):
        try:
            backtocountryafterfirstsponsor_obj = super(BackToCountryAfterFirstSponsor, self).write(vals)
            return backtocountryafterfirstsponsor_obj
        except Exception as e:
            logger.exception("Back to country write Method")
            raise ValidationError(e)


    def unlink(self):
        try:
            None

            # if self.sales_reverse_move:
            #     self.sales_reverse_move.reverse_moves()
            # if self.sales_diff_move:
            #     self.sales_diff_move.reverse_moves()
            # if self.purchase_reverse_move:
            #     self.purchase_reverse_move.reverse_moves()

            return super(BackToCountryAfterFirstSponsor, self).unlink()
        except Exception as e:
            logger.exception("Back To Country unlink Method")
            raise ValidationError(e)