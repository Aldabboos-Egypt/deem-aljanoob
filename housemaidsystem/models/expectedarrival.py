# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime
import logging

from odoo.tools.safe_eval import pytz
from . import accounting_integration

from datetime import datetime


logger = logging.getLogger(__name__)

class ExpectedArrival(models.Model):
    _name = 'housemaidsystem.applicant.expectedarrival'
    _description = 'Expected Arrival'
    _order = 'expected_arrival_date asc'

    # ================ fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    expected_arrival_date = fields.Datetime(string="Expected Arrival Date", required=True, default=lambda self: datetime.now())
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state','=','visa')])
    customer_id = fields.Many2one(related="application_id.customer_id", string="Sponsor Name (En)")
    customer_name_ar = fields.Char(related='application_id.customer_id.name_ar', string="Sponsor Name (Ar)")
    flight_no = fields.Char(string="Flight No", required=False, )
    flight_name = fields.Char(string="Flight Agent Name", required=False, )
    email_date = fields.Date(string="Email Date", default=fields.Date.context_today)
    notes = fields.Text(string="Notes")
    # ================ Related fields =================================
    #customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor", compute='_sponsor_name', store=True)
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)
    # ================ constraints =================================
    _sql_constraints = [
            ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
      ]

    # ================ Compute functions=================================
    def apply(self):
        application_obj = self.application_id
        application_obj.state = 'expectedarrival'
        body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
        body_msg += u"""<li>Expected Arrival Enter Date : <span>""" + (self.transaction_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Expected Arrival Date : <span>""" + (self.expected_arrival_date.astimezone(pytz.timezone(self.env.context.get('tz')))).strftime(
            '%Y-%m-%d %H:%M:%S') + u"""</span></li>"""
        body_msg += u"""<li>Flight No : <span>""" + (self.flight_no if self.flight_no else 'No flight number entered') + u"""</span></li>"""
        body_msg += u"""<li>Flight Agent Name : <span>""" + (self.flight_name if self.flight_name else 'No flight name entered') + u"""</span></li>"""
        body_msg += u"""<li>Email Date : <span>""" + (self.email_date).strftime(
            '%Y-%m-%d') + u"""</span></li>"""
        body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
        body_msg += u"""</ul>"""
        application_obj.message_post(body=body_msg)

        partner_obj = self.customer_id
        partner_obj.message_post(body=body_msg)



    @api.depends('application_id')
    def _sponsor_name(self):
        for record in self:
            if record.application_id:
                reservation_id = self.env['housemaidsystem.applicant.reservations'].\
                    search([('application_id', '=', record.application_id.id)], limit=1)
                if reservation_id:
                    self.customer_id = reservation_id.customer_id


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
            expectedarrival_obj = super(ExpectedArrival, self).create(vals)
            applications_obj = expectedarrival_obj.application_id
            applications_obj.state = 'expectedarrival'

            # ==============================================================
            # Send whatsApp
            company_obj = self.env['res.company'].search([('id', '!=', 0)], limit=1)
            reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
                [('application_id', '=', expectedarrival_obj.application_id.id)], limit=1)
            if reservation_obj:
                sponsor = self.env['res.partner'].search([('id', '=', reservation_obj.customer_id.id)], limit=1)
                message = 'Thank you Mr/Mrs: %s for selecting %s office, Please be informed, housemaid %s - %s will come on %s' % (
                    sponsor.name, company_obj.name, expectedarrival_obj.application_id.external_office_id, expectedarrival_obj.application_id.full_name,
                     (expectedarrival_obj.expected_arrival_date).strftime('%Y-%m-%d %H:%M:%S'))
                accounting_integration.send_whatsapp(self, sponsor, message)
            # ==============================================================


            return expectedarrival_obj

        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)



    def unlink(self):
        try:
            for record in self:
                if record.application_id:
                    # get application object then access application history object in order to add new record
                    applications_obj = record.application_id
                    applications_obj.state = 'visa'

                cancel_expectedarrival_obj = self.env['housemaidsystem.applicant.cancel_expectedarrival'].create({
                    'name': record.name,
                    'transaction_date': record.transaction_date,
                    'application_id': record.application_id.id,
                    'customer_id': record.customer_id.id,
                    'expected_arrival_date': record.expected_arrival_date,
                    'flight_no': record.flight_no,
                    'flight_name': record.flight_name,
                    'email_date': record.email_date,
                    'notes': record.notes,
                    'office_code': record.office_code.id,
                })

            return super(ExpectedArrival, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)



    def write(self, vals):
        try:
            applications_obj = self.application_id
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""

            if vals.get('flight_no', False):
                body_msg += u"""<li>New Flight No : <span>""" + vals['flight_no'] + u"""</span></li>"""

            if vals.get('flight_name', False):
                body_msg += u"""<li>New Flight Agent Name : <span>""" + vals['flight_name'] + u"""</span></li>"""

            if vals.get('expected_arrival_date', False):
                body_msg += u"""<li>New Expected Arrival Date : <span>""" + vals[
                    'expected_arrival_date'] + u"""</span></li>"""

            body_msg += u"""</ul>"""
            applications_obj.message_post(body=body_msg)
            res = super(ExpectedArrival, self).write(vals)
            return res
        except Exception as e:
            logger.exception("write Method")
            raise ValidationError(e)





class CancelExpectedArrival(models.Model):
    _name = 'housemaidsystem.applicant.cancel_expectedarrival'
    _description = 'Cancel Expected Arrival'
    _order = 'expected_arrival_date asc'

    # ================ fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    cancelation_date = fields.Date(string="Cancellation Date", required=True, default=fields.Date.context_today)
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    expected_arrival_date = fields.Datetime(string="Expected Arrival Date", required=True, default=datetime.now())
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state','=','visa')])
    customer_id = fields.Many2one(related="application_id.customer_id", string="Sponsor Name (En)")
    customer_name_ar = fields.Char(related='application_id.customer_id.name_ar', string="Sponsor Name (Ar)")
    flight_no = fields.Char(string="Flight No", required=False)
    flight_name = fields.Char(string="Flight Agent Name", required=False)
    email_date = fields.Date(string="Email Date", default=fields.Date.context_today)
    notes = fields.Text(string="Notes")
    # ================ Related fields =================================
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", )



