# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging

logger = logging.getLogger(__name__)

class OfficeBranches(models.Model):
    _name = 'housemaidsystem.configuration.officebranches'
    _rec_name = 'name'
    _description = 'OfficeBranches'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char(string="English Name", required=True, size=120)
    name_ar = fields.Char(string="Name (Ar)", required=False, size=120)
    address = fields.Char(string="Address", required=False, size=500)
    address_ar = fields.Char(string="Address (Ar)", required=False, size=500)
    telephones = fields.Char(string="Telephones", required=False, size=30)
    telephone1 = fields.Char(string="Telephone 1", required=False, size=30)
    telephone2 = fields.Char(string="Telephone 2", required=False, size=30)
    telephone3 = fields.Char(string="Telephone 3", required=False, size=30)
    telephone4 = fields.Char(string="Telephone 4", required=False, size=30)
    telephone5 = fields.Char(string="Telephone 5", required=False, size=30)
    reg_number = fields.Char(string="Commercial Reg", required=False, size=30)
    unique_num = fields.Char(string="Unique Number", required=False, size=30)
    unified_num = fields.Char(string="Unified Number", required=False, size=30)
    presenter = fields.Char(string="Presenter (En)", required=False, size=120)
    presenter_ar = fields.Char(string="Presenter (Ar)", required=False, size=120)
    email = fields.Char(string="Email", required=False,)


    @api.model
    def create(self, vals):
        try:
            obj = super(OfficeBranches, self).create(vals)
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>New branch added at : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Branch English name : <span>""" + obj.name + """</span></li>"""
            body_msg += u"""<li>Branch Arabic name : <span>""" + obj.name_ar if obj.name_ar else '' + """</span></li>"""
            body_msg += u"""<li>Branch address : <span>""" + obj.address if obj.address else '' + """</span></li>"""
            body_msg += u"""<li>Branch telephones : <span>""" + obj.telephones if obj.telephones else '' + """</span></li>"""
            body_msg += u"""<li>Branch Registration Number : <span>""" + obj.reg_number if obj.reg_number else '' + """</span></li>"""
            body_msg += u"""</ul>"""
            obj.message_post(body=body_msg)

        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)
        return obj


    def write(self, vals):
        try:
            obj = super(OfficeBranches, self).write(vals)
        except Exception as e:
            logger.exception("Write Method")
            raise ValidationError(e)
        return obj


    def unlink(self):
        try:
            return super(OfficeBranches, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)


