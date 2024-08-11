# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime

from . import accounting_integration
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging

logger = logging.getLogger(__name__)


class ExternalOfficeTrans(models.Model):
    _name = 'housemaidsystem.configuration.externalofficetrans'
    _description = 'External Office Transactions'

    enter_date = fields.Date(string="Enter Date", required=True, default=fields.Date.context_today)
    name = fields.Char(related="tran_name.name", string="Transaction Name")
    tran_name = fields.Many2one(comodel_name="housemaidsystem.configuration.externalofficetransdet",
                                string="Transaction Details Name", required="True")
    tran_date = fields.Date(string="Transaction Date", default=fields.Date.context_today, required=True, )
    created_by = fields.Char(string="Created By", size=80)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications list")
    notes = fields.Text(string="Notes", required=False)

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:

            ExternalOfficeTrans_obj = super(ExternalOfficeTrans, self).create(vals)
            application_obj = ExternalOfficeTrans_obj.application_id

            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""

            body_msg += u"""<li>Enter Date : <span>""" + (ExternalOfficeTrans_obj.enter_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Transaction Date : <span>""" + (ExternalOfficeTrans_obj.tran_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Transaction Name : <span>""" + ExternalOfficeTrans_obj.tran_name.name + u"""</span></li>"""
            body_msg += u"""<li>Notes : <span>""" + ExternalOfficeTrans_obj.notes \
                if ExternalOfficeTrans_obj.notes else '' + u"""</span></li>"""

            body_msg += u"""</ul>"""
            application_obj.message_post(body=body_msg)

            # ==============================================================
            # Send whatsApp
            company_obj = self.env['res.company'].search([('id', '!=', 0)], limit=1)
            reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
                [('application_id', '=', ExternalOfficeTrans_obj.application_id.id)], limit=1)
            if reservation_obj:
                sponsor = self.env['res.partner'].search([('id', '=', reservation_obj.customer_id.id)], limit=1)
                message = 'Thank you Mr/Mrs: %s for selecting %s office, Please be informed, housemaid %s - %s completed %s successfully at %s' % (
                    sponsor.name, company_obj.name, application_obj.external_office_id, application_obj.full_name,
                    ExternalOfficeTrans_obj.tran_name.name, (ExternalOfficeTrans_obj.enter_date).strftime('%Y-%m-%d'))
                accounting_integration.send_whatsapp(self, sponsor, message)
            # ==============================================================

            return ExternalOfficeTrans_obj
        except Exception as e:
            logger.exception("Create Method")
            raise ValidationError(e)

    def unlink(self):
        try:
            self.ensure_one()
            applications_obj = self.application_id
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li> External Offices Transactions is deleted at : <span>""" + datetime.date.today().strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Enter Date : <span>""" + (self.enter_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Transaction Date : <span>""" + (self.tran_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Transaction Name : <span>""" + self.tran_name.name + u"""</span></li>"""
            body_msg += u"""<li>Notes : <span>""" + self.notes \
                if self.notes else '' + u"""</span></li>"""

            body_msg += u"""</ul>"""
            applications_obj.message_post(body=body_msg)

            return super(ExternalOfficeTrans, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)

    def write(self, vals):
        try:
            self.ensure_one()
            applications_obj = self.application_id
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li> External Offices Transactions is Changed at : <span>""" + datetime.date.today().strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            if vals.get('tran_date', False):
                body_msg += u"""<li>Transaction Date : <span> Old value (""" + (self.tran_date).strftime(
                    '%Y-%m-%d') + """) New Value (""" + vals['tran_date'] + """)""" + u"""</span></li>"""
            if vals.get('tran_name', False):
                tran_name_obj = self.env['housemaidsystem.configuration.externalofficetransdet'].search(
                    [('id', '=', vals['tran_name'])], limit=1)
                if tran_name_obj:
                    body_msg += u"""<li>Transaction Name : <span> Old value (""" + self.tran_name.name + """) New Value (""" + tran_name_obj.name + """)""" + u"""</span></li>"""
            if vals.get('notes', False):
                body_msg += u"""<li>New Notes : <span>""" + vals['notes'] + u"""</span></li>"""

            body_msg += u"""</ul>"""
            applications_obj.message_post(body=body_msg)

            ExternalOfficeTrans_obj = super(ExternalOfficeTrans, self).write(vals)

            return ExternalOfficeTrans_obj
        except Exception as e:
            logger.exception("write Method")
            raise ValidationError(e)
