# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from dateutil import parser
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
import logging
from . import accounting_integration

logger = logging.getLogger(__name__)


class Arrival(models.Model):
    _name = 'housemaidsystem.applicant.arrival'
    _description = 'Arrival'

    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    arrival_date = fields.Date(string="Arrival Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'expectedarrival')])
    customer_id = fields.Many2one(related="application_id.customer_id", string="Sponsor Name (En)")
    customer_name_ar = fields.Char(related='application_id.customer_id.name_ar', string="Sponsor Name (Ar)")
    notes = fields.Text(string="Notes")
    sales_move = fields.Many2one('account.move', 'Sales Move', store='True')
    invoice_sales_recong_id = fields.Many2one('account.move', 'Sales Recognized Move', store='True')
    purchase_move = fields.Many2one('account.move', 'Purchase Move', store='True')
    invoice_purchase_actual = fields.Many2one('account.move', 'PO Invoice')

    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)
    invoice_id = fields.Many2one('account.move', 'Invoice Sales', compute='_get_labor_dtl', store='True')
    invoice_state = fields.Selection(related="invoice_id.state", string="Invoice Status")
    invoice_total = fields.Monetary(related="invoice_id.amount_total", string="Total Amount",
                                    currency_field='currency_id')
    invoice_due = fields.Monetary(related="invoice_id.amount_residual", string="Due Amount",
                                  currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related="invoice_id.currency_id")
    # ================ constraints =================================
    _sql_constraints = [
        ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
    ]

    # ================ Compute functions=================================
    def apply(self):
        try:
            application_obj = self.application_id
            application_obj.state = 'arrival'
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>Arrival Enter Date : <span>""" + (self.transaction_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Arrival Date : <span>""" + (self.arrival_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
            body_msg += u"""</ul>"""
            application_obj.message_post(body=body_msg)

            partner_obj = self.customer_id
            partner_obj.message_post(body=body_msg)

        except Exception as e:
            logger.exception("Apply Method")
            raise ValidationError(e)

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name

    def _get_labor_dtl(self):
        try:
            for record in self:
                if not record.application_id == None:
                    self.office_code = record.application_id.office_code
                    reservation_obj = self.env['housemaidsystem.applicant.reservations']. \
                        search([('application_id', '=', record.application_id.id)], limit=1)
                    if reservation_obj:
                        self.invoice_id = reservation_obj.invoice_sales_id


        except Exception as e:
            logger.exception("_get_labor_dtl Method")
            raise ValidationError(e)

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        arrival_obj = super(Arrival, self).create(vals)
        application_obj = arrival_obj.application_id
        application_obj.state = 'arrival'

        # ==============================================================
        # Send whatsApp
        company_obj = self.env['res.company'].search([('id', '!=', 0)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', arrival_obj.application_id.id)], limit=1)
        if reservation_obj:
            sponsor = self.env['res.partner'].search([('id', '=', reservation_obj.customer_id.id)], limit=1)
            message = 'Thank you Mr/Mrs: %s for selecting %s office, Please be informed, housemaid %s - %s is arrived %s.' % (
                sponsor.name, company_obj.name, arrival_obj.application_id.external_office_id,
                arrival_obj.application_id.full_name, company_obj.country_id.name)
            accounting_integration.send_whatsapp(self, sponsor, message)
        # ==============================================================

        # 1- Reverse previous purchase movement that created at reservation
        # =================================================================
        #  Cr: Goods on trans
        #  Dr: External office - Susp
        #  Amount: Purchase Amount USD
        # --------------------------------------------------
        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', application_obj.id)], limit=1)
        # reservation_obj.purchase_move.reverse_moves()
        accounting_integration.reverse_move(reservation_obj, reservation_obj.purchase_move,
                                            'cancel', 'When housemaid arrived.')

        # 2- Create new recognized purchase invoice based on actual office account & purchase account
        # ===========================================================================================
        #  Cr: External office - Main Account
        #  Dr: Arrival Recognized Purchase Account
        #  Amount: Purchase Amount USD
        # --------------------------------------------------
        arrival_obj.invoice_purchase_actual = \
            accounting_integration.arrival_renew_purchase_invoice(self, application_obj)

        # 3- Create new move from deffered sales to sales to recongnized the sales
        # =========================================================================
        #  Cr: Sales
        #  Dr: Sales Deferred first sponsor
        #  Amount: Sales Amount
        # --------------------------------------------------
        arrival_obj.sales_move = accounting_integration.arrival_sales_move(arrival_obj)

        return arrival_obj

    def unlink(self):
        for record in self:
            if record.application_id:
                application_obj = record.application_id
                application_obj.state = 'expectedarrival'

                # 1- Cancel Reversed movement
                # =============================
                reservation_obj = self.env['housemaidsystem.applicant.reservations'].search \
                    ([('application_id', '=', application_obj.id)], limit=1)
                accounting_integration.reverse_move(reservation_obj, reservation_obj.purchase_move, 'cancel',
                                                    'Reverse Arrival Transaction')

                # reversed_movement_obj = self.env['account.move'].search \
                #     ([('id', '=', reservation_obj.purchase_move.reverse_entry_id.id)], limit=1)
                # if reversed_movement_obj:
                #     reversed_movement_obj.reverse_moves()

                # 2- Cancel purchase invoice of vendor main A/C
                # ==============================================
                record.invoice_purchase_actual.write({
                    'ref': record.invoice_purchase_actual.ref + '(Reverse:' + record.invoice_purchase_actual.name + ')'
                })
                accounting_integration.reverse_move(self, record.invoice_purchase_actual, 'cancel',
                                                    'Reverse Arrival Transaction')

                # 3- Cancel sales recognized movement
                # ====================================
                accounting_integration.reverse_move(record, record.sales_move, 'cancel',
                                                    'Reverse Arrival Transaction')

                self.env['housemaidsystem.applicant.cancel_arrival'].create({
                    'name': record.name,
                    'transaction_date': record.transaction_date,
                    'arrival_date': record.arrival_date,
                    'application_id': record.application_id.id,
                    'customer_id': record.customer_id.id,
                    'notes': record.notes,
                    'sales_move': record.sales_move.id,
                    'invoice_sales_recong_id': record.invoice_sales_recong_id.id,
                    'purchase_move': record.purchase_move.id,
                    'invoice_purchase_actual': record.invoice_purchase_actual.id,
                    'office_code': record.office_code.id,
                })

        return super(Arrival, self).unlink()

    def write(self, vals):
        applications_obj = self.application_id
        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""

        if vals.get('arrival_date', False):
            body_msg += u"""<li>New Arrival Date : <span>""" + vals['arrival_date'] + u"""</span></li>"""

        body_msg += u"""</ul>"""
        applications_obj.message_post(body=body_msg)
        res = super(Arrival, self).write(vals)
        return res


class CancelArrival(models.Model):
    _name = 'housemaidsystem.applicant.cancel_arrival'
    _description = 'Cancel Arrival'

    # ================ Fields =================================
    name = fields.Char(string="Name", )
    cancelation_date = fields.Date(string="Cancellation Date", required=True, default=fields.Date.context_today)
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    arrival_date = fields.Date(string="Arrival Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'expectedarrival')])
    customer_id = fields.Many2one(related="application_id.customer_id", string="Sponsor Name (En)")
    customer_name_ar = fields.Char(related='application_id.customer_id.name_ar', string="Sponsor Name (Ar)")
    notes = fields.Text(string="Notes")
    sales_move = fields.Many2one('account.move', 'Sales Move', store='True')
    invoice_sales_recong_id = fields.Many2one('account.move', 'Sales Recognized Move', store='True')
    purchase_move = fields.Many2one('account.move', 'Purchase Move', store='True')
    invoice_purchase_actual = fields.Many2one('account.move', 'Purchase Invoice')

    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", )
