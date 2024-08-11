# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import time
import logging
from . import accounting_integration

logger = logging.getLogger(__name__)


class Reservations(models.Model):
    _name = 'housemaidsystem.applicant.reservations'
    _description = 'Reservations'

    def _get_type_id(self):
        return self.env['housemaidsystem.configuration.settings'].search([],
                                                                         limit=1).direct_journal_arrival_cash or False

    # ================== Main Fields====================================================
    name = fields.Char(string="Name", compute='_compute_name')
    reservation_date = fields.Date(string="Reservation Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'application')])
    sales_man = fields.Many2one(comodel_name="res.users", string="Sales Man", required=True,
                                default=lambda self: self.env.user)
    deal_amount = fields.Float(string="Deal Amount", required=True, )
    down_payment_amount = fields.Float(string="Down Payment Amount", required=False, )
    additional_payment_amount = fields.Float(string="Additional Down Payment Amount", required=False, )
    notes = fields.Text(string="Notes")
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor", required=True,
                                  domain=[('customer_rank', '>', 0)])
    customer_name_ar = fields.Char(related='customer_id.name_ar')
    state = fields.Selection(string='Application Status', readonly=True, default='reservation',
                             related='application_id.state')
    invoice_sales_id = fields.Many2one('account.move', 'Sales Invoice')
    invoice_purchase_id = fields.Many2one('account.move', 'Purchase Invoice')
    purchase_move = fields.Many2one('account.move', 'Purchase deffered Move', store='True')
    down_payment_invoice = fields.Many2one('account.payment', 'Down Payment Invoice')
    additional_payment_invoice = fields.Many2one('account.payment', 'Additional Down Payment Invoice')
    reservation_days = fields.Integer(string="Reservation Days", compute='_calc_days')
    rec_status = fields.Selection(string='Record Status', selection=[('active', 'Active'), ('canceled', 'Canceled')],
                                  default='active')

    paid_immediately = fields.Boolean(string="Collected From Sponsor", default=True, )
    pay_due_date = fields.Date(string="Expected Date", required=True, default=fields.Date.context_today)
    paid_immediately_move = fields.Many2one('account.move', 'Suspend Payment Move', store='True')
    deal_confirmation = fields.Selection(string="Ticket Deal",
                                         selection=[('employer', 'Employer'),
                                                    ('agency', 'Agency'), ], default='employer', required=False, )
    # ================== Related Fields====================================================
    labor_image = fields.Binary("Photo", compute='_get_labor_dtl')
    full_name = fields.Char(string="Full Name", compute='_get_labor_dtl')
    code = fields.Char(string="Code", compute='_get_labor_dtl')
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)
    journal = fields.Many2one('account.journal', string="Payment Method", default=_get_type_id, required=True,
                              domain="['|', ('type', '=', 'cash'), ('type', '=', 'bank')]", )

    # ================== Constraints ==========================
    # This example for making field value is unique for field name is (name) please ensure field type string \ char.
    _sql_constraints = [
        ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
    ]

    # ============================= Apply / Skip ===============================================

    def apply(self):
        try:
            if not self.customer_id:
                raise ValidationError("Sponsor is missing.")
            else:
                # if not self.customer_id.civil_id:
                #     raise ValidationError("Sponsor Civil ID is missing.")
                # elif not len(self.customer_id.civil_id) == 12:
                #     raise ValidationError("Sponsor Civil ID is wrong.")
                # elif not self.customer_id.mobile:
                #     raise ValidationError("Sponsor Mobile is missing.")
                # elif self.customer_id.mobile.startswith('1') or self.customer_id.mobile.startswith('2'):
                #     raise ValidationError("Sponsor Mobile is wrong.")
                if self.customer_id.is_black_list:
                    raise ValidationError("Sponsor is black listed.")
                else:
                    application_obj = self.application_id
                    application_obj.state = 'reservation'

                    body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
                    body_msg += u"""<li>Transaction Date : <span>""" + (datetime.date.today()).strftime(
                        '%Y-%m-%d') + u"""</span></li>"""
                    body_msg += u"""<li>Reservation Date : <span>""" + (self.reservation_date).strftime(
                        '%Y-%m-%d') + u"""</span></li>"""

                    if self.customer_id.name:
                        body_msg += u"""<li>Sponsor Name (En) : <span>""" + self.customer_id.name  + u"""</span></li>"""

                    if self.customer_id.name_ar:
                        body_msg += u"""<li>Sponsor Name (Ar) : <span>""" + self.customer_id.name_ar + u"""</span></li>"""

                    body_msg += u"""<li>Deal Amount : <span>""" + str(self.deal_amount) + u"""</span></li>"""
                    body_msg += u"""<li>Down Payment Amount : <span>""" + str(
                        self.down_payment_amount if self.down_payment_amount else 0) + u"""</span></li>"""

                    if self.journal.type == 'cash':
                        body_msg += u"""<li>Cash\K-Net : <span> Cash </span></li>"""
                    else:
                        body_msg += u"""<li>Cash\K-Net : <span> K-Net </span></li>"""

                    body_msg += u"""<li>Journal Name : <span>""" + self.journal.name + u"""</span></li>"""

                    body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""

                    if self.paid_immediately:
                        body_msg += u"""<li>Collected From Sponsor : Yes </li>"""
                    else:
                        body_msg += u"""<li>Collected From Sponsor : No </li>"""
                        body_msg += u"""<li>Expected Collection Date : <span>""" + (self.pay_due_date).strftime(
                            '%Y-%m-%d') + u"""</span></li>"""

                    body_msg += u"""</ul>"""
                    application_obj.message_post(body=body_msg)

                    partner_obj = self.customer_id
                    partner_obj.message_post(body=body_msg)

        except Exception as e:
            logger.exception("apply Method")
            raise ValidationError(e)

    # ================== Compute Functions========================================

    @api.depends('customer_id')
    def _compute_name(self):
        try:
            for record in self:
                self.name = self.customer_id.name
        except Exception as e:
            logger.exception("_compute_name Method")
            raise ValidationError(e)

    def _calc_days(self):
        try:
            for rec in self:
                elapsed_timedelta = fields.datetime.now() - fields.Datetime.from_string(rec.reservation_date)
                rec.reservation_days = elapsed_timedelta.days
        except Exception as e:
            logger.exception("_calc_days Method")
            raise ValidationError(e)

    # @api.depends('application_id')
    def _get_labor_dtl(self):
        try:
            for record in self:
                if record:
                    self.labor_image = record.application_id.labor_image
                    self.full_name = record.application_id.full_name
                    self.office_code = record.application_id.office_code
        except Exception as e:
            logger.exception("_get_labor_dtl Method")
            raise ValidationError(e)

    # ================== Create - unlink - write Methods ==========================
    @api.model
    def create(self, vals):
        try:
            sponsor = self.env['res.partner'].search([('id', '=', vals.get('customer_id'))], limit=1)
            if sponsor.is_black_list:
                raise ValidationError(
                    _('This Sponsor is black list.'))

            if vals.get('deal_amount') == 0:
                raise ValidationError(_('Deal amount is Missing.'))

            if vals.get('deal_amount') < vals.get('down_payment_amount'):
                raise ValidationError(_('Down payment should be less than deal amount.'))

            application_obj = self.env['housemaidsystem.applicant.applications'].search([('id', '=',
                                                                                          vals.get('application_id'))],
                                                                                        limit=1)

            # ==============================================================
            # Send whatsApp
            company_obj = self.env['res.company'].search([('id', '!=', 0)], limit=1)

            message = 'Thank you Mr/Mrs: %s for selecting %s, Please be informed, housemaid %s - %s is ' \
                      'selected successfully, you paid %.0f KWD from %.0f KWD' % (
                          sponsor.name, company_obj.name, application_obj.external_office_id, application_obj.full_name,
                          vals.get('down_payment_amount'),
                          vals.get('deal_amount'))

            message = "شكرا جزيلا {0} لاختيارك {1} لقد تم حجز الخادمه {2} : {3} بنجاح وقمتم بدفع مبلغ {4} دينار كويتي " \
                      "من اصل مبلغ {5} دينار كويتي يمكنمك التواصل معنا من خلال هذا الرقم ومرحبا بكم اي وقت".format(
                sponsor.name, company_obj.name,
                application_obj.external_office_id,
                application_obj.full_name, vals.get(
                    'down_payment_amount'), vals.get('deal_amount'))

            accounting_integration.send_whatsapp(self, sponsor, message)

            # ==============================================================
            # Add Contract Data
            accounting_integration.add_contract(self, application_obj, sponsor)
            # ==============================================================
            # 1- Create new sales invoice
            #  Cr: Sales Deferred first sponsor
            #  Dr: Acc Rec
            #  Amount: Sales Amount
            # --------------------------------------------------
            vals['invoice_sales_id'] = accounting_integration.reservation_sales_invoice(self, application_obj,
                                                                                        vals.get('deal_amount'),
                                                                                        vals.get('customer_id'))
            # ==============================================================
            # 2- Create purchase movement
            #  Cr: External office - Susp
            #  Dr: Goods on trans
            #  Amount: Purchase Amount USD
            # --------------------------------------------------
            vals['purchase_move'] = accounting_integration.reservation_purchases_move(self, application_obj)
            # ==============================================================
            # 3- Register down payment
            #  Cr: Acc Rec
            #  Dr: Cash Arrival
            #  Amount: Down Amount
            # --------------------------------------------------
            if vals.get('down_payment_amount') != 0:
                vals['down_payment_invoice'] = accounting_integration. \
                    reservation_sales_invoice_payment(self, application_obj, vals.get('down_payment_amount'),
                                                      vals['invoice_sales_id'], vals['journal'])

            # ==============================================================
            # 4- Suspend down payment {To be cancel in this version}
            # Dr: Acc Rec
            # Cr: Cash Arrival
            # Amount: Down Amount}
            # --------------------------------------------------
            # if vals.get('down_payment_amount') != 0 and vals.get('paid_immediately', False) is False:
            #     vals['paid_immediately_move'] = accounting_integration.\
            #         reservation_move_dr_cash_cr_acctred(self, vals.get('down_payment_amount'),
            #                                             vals.get('pay_due_date'), vals.get('customer_id'),
            #                                             vals.get('application_id'))

            # ==============================================================

            if application_obj and sponsor:
                application_obj.customer_id = sponsor.id

            reservations_obj = super(Reservations, self).create(vals)

            # 4- Add new sponsor payment (if down payment greater than zero) {Not used in this version}
            # ========================================================================================
            # if reservations_obj.down_payment_amount > 0:
            #     accounting_integration.add_sponsor_payment(reservations_obj, 'reservation', 'Payment')

            return reservations_obj

        except Exception as e:
            logger.exception("Create Method")
            raise ValidationError(e)

    def unlink(self):
        try:
            for record in self:
                # 1- Get application object then access application history object in order to add new record
                # =============================================================================================
                applications_obj = record.application_id
                # if record.down_payment_amount != 0:
                # reverse down payment
                # {Cr: Cash Arrival / Dr: Acc Rec  >> Down Amount}
                # =================================================
                # applications_obj.reservation_down_payment_refund = \
                #     accounting_integration.reservation_sales_invoice_refund_payment(self)

                # 2- Reverse sales invoice
                # Cr: Acc Rec
                # Dr: Sales Deferred first sponsor
                # Amount: Sales Amount
                # =================================================================
                reversed_sales_invoice_move = accounting_integration.reverse_move(record, record.invoice_sales_id,
                                                                                  'cancel', 'Based on customer request')

                # reversal = move_reversal.reverse_moves()
                # reverse_move = self.env['account.move'].browse(reversal['res_id'])

                # accounting_integration.unreconcile_invoice_move_lines(record, record.invoice_sales_id)
                # record.invoice_sales_id.button_cancel_posted_moves()

                # 3- Reverse purchase move
                # Cr: Goods on trans
                # Dr: External office - Susp
                # Amount: Purchase Amount
                # ======================================================================
                reversed_purchase_invoice_move = accounting_integration.reverse_move(record, record.purchase_move,
                                                                                     'cancel',
                                                                                     'Based on customer request')

                # record.purchase_move.action_view_reverse_entry()
                # record.purchase_move.reverse_moves()

                # credit_note_wizard = self.env['account.move.reversal'].with_context(
                #     {'active_ids': record.purchase_move.ids, 'active_id': record.purchase_move,
                #      'active_model': 'account.move'}).create({
                #     'refund_method': 'cancel',
                #     'reason': 'reason test cancel',
                # })
                # invoice_refund = self.env['account.move'].browse(credit_note_wizard.reverse_moves()['res_id'])

                # 4- post refund payment by down payment amount {down_payment_invoice}
                # Dr: Cash Arrival
                # Cr: Acc Rec
                # Amount: Down Amount
                # ======================================================================
                accounting_integration.reservation_refund_down_payment(record, record.down_payment_invoice)

                # Add new sponsor Refund payment
                # ===============================
                # if record.down_payment_amount > 0:
                #     accounting_integration.add_sponsor_payment(record, 'reservation', 'Refund')

                applications_obj.state = 'application'
                applications_obj.customer_id = None

                cancel_reservations_obj = self.env['housemaidsystem.applicant.cancel_reservations'].create({
                    'name': record.name,
                    'reservation_date': record.reservation_date,
                    'application_id': record.application_id.id,
                    'sales_man': record.sales_man.id,
                    'deal_amount': record.deal_amount,
                    'down_payment_amount': record.down_payment_amount,
                    'notes': record.notes,
                    'customer_id': record.customer_id.id,
                    'invoice_sales_id': record.invoice_sales_id.id,
                    'invoice_purchase_id': record.invoice_purchase_id.id,
                    'purchase_move': record.purchase_move.id,
                    'down_payment_invoice': record.down_payment_invoice.id,
                    'paid_immediately': record.paid_immediately,
                    'pay_due_date': record.pay_due_date,
                    'paid_immediately_move': record.paid_immediately_move.id,
                    'office_code': record.office_code.id,
                })
                # ==============================================================
                # Remove Contract Data
                accounting_integration.remove_contract(self, record.application_id)

            return super(Reservations, self).unlink()
        except Exception as e:
            logger.exception("Unlink Method")
            raise ValidationError(e)


class CancelReservations(models.Model):
    _name = 'housemaidsystem.applicant.cancel_reservations'
    _description = 'Cancel Reservations'

    # ================== Main Fields====================================================
    name = fields.Char(string="Name", compute='_compute_name')
    cancelation_date = fields.Date(string="Cancelation Date", required=True, default=fields.Date.context_today)
    reservation_date = fields.Date(string="Reservation Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'application')])
    sales_man = fields.Many2one(comodel_name="res.users", string="Sales Man", required=True,
                                default=lambda self: self.env.user)
    deal_amount = fields.Float(string="Deal Amount", required=True, default=0)
    down_payment_amount = fields.Float(string="Down Payment Amount", required=False, default=0)
    notes = fields.Text(string="Notes")
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor", required=True, )
    customer_name_ar = fields.Char(related='customer_id.name_ar')
    invoice_sales_id = fields.Many2one('account.move', 'Invoice Sales')
    invoice_purchase_id = fields.Many2one('account.move', 'Invoice Purchase')
    purchase_move = fields.Many2one('account.move', 'Purchase deffered Move', store='True')
    down_payment_invoice = fields.Many2one('account.payment', 'Down Payment Invoice')
    paid_immediately = fields.Boolean(string="Collected From Sponsor", default=True, )
    pay_due_date = fields.Date(string="Expected Date", required=True, default=fields.Date.context_today)
    paid_immediately_move = fields.Many2one('account.move', 'Suspend Payment Move', store='True')
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", )
