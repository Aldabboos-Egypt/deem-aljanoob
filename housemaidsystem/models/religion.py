# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
import logging
from odoo.exceptions import ValidationError
import datetime

logger = logging.getLogger(__name__)

class religion(models.Model):
    _name = 'housemaidsystem.configuration.religion'
    _description = 'Religion'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char(string="Name", size=60)

    @api.model
    def create(self, vals):
        try:
            religion_obj = super(religion, self).create(vals)

            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>New Religion Applied added at : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Post applied name : <span>""" + vals['name'] + """</span></li>"""
            body_msg += u"""</ul>"""

            religion_obj.message_post(body=body_msg)

            return religion_obj
        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)





