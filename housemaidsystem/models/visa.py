# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging

logger = logging.getLogger(__name__)


class Visa(models.Model):
    _name = 'housemaidsystem.applicant.visa'
    _description = 'visa'

    # ================ fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'reservation')])
    customer_id = fields.Many2one(related="application_id.customer_id", string="Sponsor")
    customer_name_ar = fields.Char(related='application_id.customer_id.name_ar')
    visa_no = fields.Char(string="Visa no", required=True, )
    unified_no = fields.Char(string="Unified No.", )
    applicant_no = fields.Char(string="Application No.", )
    visa_issue_date = fields.Date(string="Visa Issue Date", required=False, default=fields.Date.context_today)
    visa_exp_date = fields.Date(string="Visa Expiry Date", required=False, default=fields.Date.context_today)
    visa_rec_date = fields.Date(string="Visa Received Date", required=False, default=fields.Date.context_today)
    visa_snd_date = fields.Date(string="Visa Send Date", required=False, default=fields.Date.context_today)
    notes = fields.Text(string="Notes")
    visa_days = fields.Integer(string="Visa Issue Days", store=False, compute='_calc_days_visa_issue_date', )
    visa_rec_days = fields.Integer(string="Visa Received Days", store=False, compute='_calc_days_visa_rec_date', )
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)

    # =====================================================================================================
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self._default_country_id())
    state_id = fields.Many2one(comodel_name="res.country.state", string="States", required=False, )
    area_id = fields.Many2one(comodel_name="housemaidsystem.configuration.area", string="Areas", required=False, )
    sponsor_block = fields.Char(string="Block", required=False, )
    sponsor_street = fields.Char(string="Street", required=False, )
    sponsor_avenue = fields.Char(string="Avenue", required=False, )
    sponsor_building = fields.Char(string="Building", required=False, )
    sponsor_zip = fields.Char(string="Zip", required=False, )
    visa_mobile = fields.Char(string="Mobile", required=False)
    visa_sponsor_name = fields.Char(string="Sponsor Name", required=False)

    # ================ constraints =================================
    _sql_constraints = [
        ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
    ]

    # ==================  Main Functions ==========================
    def _default_country_id(self):
        return self.env.ref('base.kw').id

    def _calc_days_visa_issue_date(self):
        try:
            # self.ensure_one()
            for rec in self:
                elapsed_timedelta = fields.datetime.now() - fields.Datetime.from_string(rec.visa_issue_date)
                rec.visa_days = elapsed_timedelta.days
        except Exception as e:
            logger.exception("_calc_days_visa_issue_date Method")
            raise ValidationError(e)

    def _calc_days_visa_rec_date(self):
        try:
            # self.ensure_one()
            for rec in self:
                elapsed_timedelta = fields.datetime.now() - fields.Datetime.from_string(rec.visa_rec_date)
                rec.visa_rec_days = elapsed_timedelta.days
        except Exception as e:
            logger.exception("_calc_days_visa_rec_date Method")
            raise ValidationError(e)

    def _get_labor_dtl(self):
        try:
            for record in self:
                if not record.application_id == None:
                    self.office_code = record.application_id.office_code
        except Exception as e:
            logger.exception("_get_labor_dtl Method")
            raise ValidationError(e)

    def apply(self):
        try:
            self.ensure_one()
            application_obj = self.application_id
            application_obj.state = 'visa'
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>Visa Enter Date : <span>""" + (self.transaction_date).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Visa No : <span>""" + self.visa_no + u"""</span></li>"""
            if self.unified_no:
                body_msg += u"""<li>Unified no : <span>""" + self.unified_no + u"""</span></li>"""
            else:
                body_msg += u"""<li>Unified no : </li>"""
            if self.visa_issue_date:
                body_msg += u"""<li>Visa Issue Date : <span>""" + (self.visa_issue_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""

            if self.visa_exp_date:
                body_msg += u"""<li>Visa Expiry Date : <span>""" + (self.visa_exp_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""

            if self.visa_rec_date:
                body_msg += u"""<li>Visa Received Date : <span>""" + (self.visa_rec_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""

            if self.visa_snd_date:
                body_msg += u"""<li>Visa Send Date : <span>""" + (self.visa_snd_date).strftime(
                    '%Y-%m-%d') + u"""</span></li>"""

            body_msg += u"""<li>Notes : <span>""" + self.notes if self.notes else '' + u"""</span></li>"""
            body_msg += u"""</ul>"""
            application_obj.message_post(body=body_msg)

            partner_obj = self.customer_id
            partner_obj.message_post(body=body_msg)


        except Exception as e:
            logger.exception("Apply Method")
            raise ValidationError(e)

    def save(self):
        try:
            self.write
        except Exception as e:
            logger.exception("Save Method")
            raise ValidationError(e)

    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        try:
            for record in self:
                record.name = self.application_id.name
        except Exception as e:
            logger.exception("_compute_name Method")
            raise ValidationError(e)

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            if vals.get('application_id', False):
                if not (vals.get('customer_id', False) or vals.get('invoice_id', False)):
                    domain = [('application_id', '=', vals['application_id'])]
                    reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(domain)
                    if reservation_obj:
                        vals['customer_id'] = reservation_obj.customer_id.id
                        vals['invoice_id'] = reservation_obj.invoice_sales_id.id
            visa_obj = super(Visa, self).create(vals)

            # attachment_obj = self.env['ir.attachment'].search([('res_field', '=', 'visa_image'),
            #                                                    ('res_model', '=', 'visa'),
            #                                                    ('res_id', '=', visa_obj.id)], limit=1)
            # if attachment_obj:
            #     new_attachment = {'name': attachment_obj.name,
            #                       'datas': attachment_obj.datas,
            #                       'datas_fname': attachment_obj.datas_fname,
            #                       'res_name': visa_obj.application_id.name,
            #                       'res_model': 'housemaidsystem.applicant.applications',
            #                       'res_model': 'Applications',
            #                       'type': attachment_obj.type,
            #                       'public': attachment_obj.public,
            #                       'store_fname': attachment_obj.store_fname,
            #                       'file_size': attachment_obj.file_size,
            #                       'checksum': attachment_obj.checksum,
            #                       'mimetype': attachment_obj.mimetype,
            #                       'index_content': attachment_obj.index_content,
            #                       'active': attachment_obj.active,
            #                       'res_id': visa_obj.application_id.id}
            #     self.env['ir.attachment'].create(new_attachment)

            if vals.get('application_id'):
                applications_obj = self.env['housemaidsystem.applicant.applications'].browse(vals.get('application_id'))
                applications_obj.state = 'visa'

            return visa_obj
        except Exception as e:
            logger.exception("Create Method")
            raise ValidationError(e)

    @property
    def unlink(self):
        try:
            for record in self:
                if record.application_id:
                    # get application object then access application history object in order to add new record
                    applications_obj = record.application_id
                    applications_obj.state = 'reservation'

                self.env['housemaidsystem.applicant.cancel_visa'].create({
                    'name': record.name if record.name else '',
                    'transaction_date': record.transaction_date if record.transaction_date else None,
                    'application_id': record.application_id.id if record.application_id.id else None,
                    'customer_id': record.customer_id.id if record.customer_id.id else None,
                    'visa_no': record.visa_no if record.visa_no else '',
                    'unified_no': record.unified_no if record.unified_no else '',
                    'visa_issue_date': record.visa_issue_date if record.visa_issue_date else None,
                    'visa_exp_date': record.visa_exp_date if record.visa_exp_date else None,
                    'visa_rec_date': record.visa_rec_date if record.visa_rec_date else None,
                    'visa_snd_date': record.visa_snd_date if record.visa_snd_date else None,
                    'notes': record.notes if record.notes else '',
                    'office_code': record.office_code.id if record.office_code.id else None,
                })

            return super(Visa, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)

    def write(self, vals):
        try:
            self.ensure_one()
            applications_obj = self.application_id
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""

            if vals.get('visa_no', False):
                body_msg += u"""<li>New Visa No : <span>""" + vals['visa_no'] + u"""</span></li>"""

            if vals.get('unified_no', False):
                body_msg += u"""<li>New Unified no : <span>""" + vals['unified_no'] + u"""</span></li>"""

            if vals.get('visa_issue_date', False):
                body_msg += u"""<li>New Visa Issue Date : <span>""" + vals['visa_issue_date'] + u"""</span></li>"""

            if vals.get('visa_exp_date', False):
                body_msg += u"""<li>New Visa Expiry Date : <span>""" + vals['visa_exp_date'] + u"""</span></li>"""

            if vals.get('visa_rec_date', False):
                body_msg += u"""<li>New Visa Received Date : <span>""" + vals['visa_rec_date'] + u"""</span></li>"""

            if vals.get('visa_snd_date', False):
                body_msg += u"""<li>New Visa Send Date : <span>""" + vals['visa_snd_date'] + u"""</span></li>"""

            body_msg += u"""</ul>"""
            applications_obj.message_post(body=body_msg)
            visa = super(Visa, self).write(vals)

            # if self.visa_image:
            #     attachment_obj = self.env['ir.attachment'].search([('res_field', '=', 'visa_image'),
            #                                                        ('res_model', '=', 'visa'),
            #                                                        ('res_id', '=', self.id)], limit=1)
            #     if attachment_obj:
            #         old_attachment_obj = self.env['ir.attachment'].search([('name', '=', attachment_obj.name),
            #                                                            ('res_model', '=', 'Applications'),
            #                                                            ('res_id', '=', self.application_id.id)], limit=1)
            #         if old_attachment_obj:
            #             old_attachment_obj.unlink()
            #
            #         new_attachment = {'name': attachment_obj.name,
            #                           'datas': attachment_obj.datas,
            #                           'datas_fname': attachment_obj.datas_fname,
            #                           'res_name': self.application_id.name,
            #                           'res_model': 'housemaidsystem.applicant.applications',
            #                           # 'res_model': 'Applications',
            #                           'type': attachment_obj.type,
            #                           'public': attachment_obj.public,
            #                           'store_fname': attachment_obj.store_fname,
            #                           'file_size': attachment_obj.file_size,
            #                           'checksum': attachment_obj.checksum,
            #                           'mimetype': attachment_obj.mimetype,
            #                           'index_content': attachment_obj.index_content,
            #                           'active': attachment_obj.active,
            #                           'res_id': self.application_id.id}
            #         self.env['ir.attachment'].create(new_attachment)

            return visa
        except Exception as e:
            logger.exception("write Method")
            raise ValidationError(e)

    # ================ On Change Functions =================================

    @api.onchange('application_id')
    @api.depends('customer_id')
    def onchange_get_customer_name(self):
        try:
            for record in self:
                if record.application_id:
                    domain = [('application_id', '=', record.application_id.id)]
                    reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(domain)
                    if reservation_obj:
                        record.customer_id = reservation_obj.customer_id.id
                        # record.invoice_id = reservation_obj.invoice_sales_id.id
        except Exception as e:
            logger.exception("onchange_get_customer_name Method")
            raise ValidationError(e)


class CancelVisa(models.Model):
    _name = 'housemaidsystem.applicant.cancel_visa'
    _description = 'Cancel Visa'

    # ================ fields =================================
    cancelation_date = fields.Date(string="Cancellation Date", required=True, default=fields.Date.context_today)
    name = fields.Char(string="Name", )
    # visa_image = fields.Binary("Visa Image", attachment=True, store="True",
    #                       help="This field holds the image used as photo for "
    #                            "the housemaidsystem visa image, limited to 1024x1024px.")
    transaction_date = fields.Date(string="Transaction Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'reservation')])
    customer_id = fields.Many2one(related="application_id.customer_id", string="Sponsor Name (En)")
    customer_name_ar = fields.Char(related='application_id.customer_id.name_ar', string="Sponsor Name (Ar)")
    visa_no = fields.Char(string="Visa no", required=True)
    unified_no = fields.Char(string="Unified no")
    visa_issue_date = fields.Date(string="Visa Issue Date", required=True, default=fields.Date.context_today)
    visa_exp_date = fields.Date(string="Visa Expiry Date", required=True, default=fields.Date.context_today)
    visa_rec_date = fields.Date(string="Visa Received Date", required=True, default=fields.Date.context_today)
    visa_snd_date = fields.Date(string="Visa Send Date", required=True, default=fields.Date.context_today)
    notes = fields.Text(string="Notes")
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", )
    states = fields.Many2one(comodel_name="res.country.state",
                             string="States", required=False, )
    areas = fields.Many2one(comodel_name="housemaidsystem.configuration.area", string="Areas", required=False, )
    sponsor_block = fields.Char(string="Block", required=False, )
    sponsor_street = fields.Char(string="Street", required=False, )
    sponsor_avenue = fields.Char(string="Avenue", required=False, )
    sponsor_building = fields.Char(string="Building", required=False, )
    sponsor_zip = fields.Char(string="Zip", required=False, )
