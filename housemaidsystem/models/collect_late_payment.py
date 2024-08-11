# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
import datetime
from dateutil import parser
import logging
from . import accounting_integration

logger = logging.getLogger(__name__)


class CollectLatePayment(models.Model):
    _name = 'housemaidsystem.applicant.collect_payment_late'
    _description = 'Collect Payment Late After Reservation Process'

    def _get_type_id(self):
        return self.env['housemaidsystem.configuration.settings'].search([],
                                                                         limit=1).direct_journal_arrival_cash or False

    transaction_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications", )
    invoice_sales_id = fields.Many2one('account.move', 'Sales Invoice')
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor", required=True, )
    down_payment_amount = fields.Float(string="DP Amount", required=False, )
    due_amount = fields.Float(string="Due Amount", required=False, )
    down_payment_invoice = fields.Many2one('account.payment', 'DP Ref#')
    deal_amount = fields.Float(string="Deal Amount", required=True, default=0)
    payment_amount = fields.Float(string="Payment Amount", required=False, default=0)
    payment_invoice = fields.Many2one('account.payment', 'Down Payment Invoice')
    notes = fields.Text(string="Notes")
    journal = fields.Many2one('account.journal', string="Payment Method", default=_get_type_id, required=True,
                              domain="['|', ('type', '=', 'cash'), ('type', '=', 'bank')]", )

    # ============================= Apply / Skip ===============================================

    def apply(self):
        try:
            if not self.payment_amount:
                raise ValidationError("Payment is missing.")
            else:
                application_obj = self.application_id
                body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
                body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""
                body_msg += u"""<li>Payment Date : <span>""" + (self.transaction_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""
                body_msg += u"""<li>Sponsor Name : <span>""" + self.customer_id.name + u"""</span></li>"""
                body_msg += u"""<li>Deal Amount : <span>""" + str(self.deal_amount) + u"""</span></li>"""
                body_msg += u"""<li>DP Amount : <span>""" + str(
                    self.down_payment_amount if self.down_payment_amount else 0) + u"""</span></li>"""
                body_msg += u"""<li>New Payment Amount : <span>""" + str(
                    self.payment_amount if self.payment_amount else 0) + u"""</span></li>"""
                body_msg += u"""<li>Application Status : <span>""" + self.application_id.state.capitalize() + u"""</span></li>"""
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

        except Exception as e:
            logger.exception("apply Method")
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        try:
            collect_payment_late_obj = super(CollectLatePayment, self).create(vals)

            reservations_obj = self.env['housemaidsystem.applicant.reservations'].search(
                [('application_id', '=', collect_payment_late_obj.application_id.id)],
                limit=1)

            if collect_payment_late_obj.due_amount < collect_payment_late_obj.payment_amount:
                raise ValidationError(
                    "invoice %s due amount is less than total sponsor payments paid (DP first payment + new payment)." % (
                        reservations_obj.display_name))


            # if reservations_obj.additional_payment_invoice:
            #     raise ValidationError(
            #         "invoice %s currently has 2 DP payments, sorry you cannot add more payments." % (
            #             reservations_obj.display_name))


            if reservations_obj.down_payment_invoice:
                # There is down payment then reverse it and add new
                # new_payment = reservations_obj.down_payment_amount + collect_payment_late_obj.payment_amount
                # accounting_integration.reservation_refund_down_payment(reservations_obj, reservations_obj.down_payment_invoice)

                reservations_obj.additional_payment_amount = collect_payment_late_obj.payment_amount
                reservations_obj.additional_payment_invoice = accounting_integration. \
                    reservation_sales_invoice_payment(self, collect_payment_late_obj.application_id, collect_payment_late_obj.payment_amount,
                                                      reservations_obj.invoice_sales_id.id,collect_payment_late_obj.journal.id)




            else:
                # there is not down payment then add new down payment
                reservations_obj.down_payment_amount = collect_payment_late_obj.payment_amount
                reservations_obj.down_payment_invoice = accounting_integration. \
                    reservation_sales_invoice_payment(self, collect_payment_late_obj.application_id,
                                                      collect_payment_late_obj.payment_amount,
                                                      reservations_obj.invoice_sales_id.id,collect_payment_late_obj.journal.id)



            # if collect_payment_late_obj.down_payment_amount > collect_payment_late_obj.down_payment_amount:
            #     raise ValidationError("Down Payment is wrong, it is greater than deal amount.")
            #
            # collect_payment_late_obj.down_payment_invoice = accounting_integration.\
            #     reservation_sales_invoice_payment(self, collect_payment_late_obj.down_payment_amount,
            #                                       collect_payment_late_obj.invoice_sales_id.id,
            #                                       collect_payment_late_obj.application_id,
            #                                       collect_payment_late_obj.customer_id.id)
            #
            # reservations_obj.down_payment_amount = collect_payment_late_obj.down_payment_amount
            # reservations_obj.down_payment_invoice = collect_payment_late_obj.down_payment_invoice
            # accounting_integration.add_sponsor_payment(reservations_obj, 'reservation', 'Payment')


            return collect_payment_late_obj

        except Exception as e:
            logger.exception("Create Method")
            raise ValidationError(e)

