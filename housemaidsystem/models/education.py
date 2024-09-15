# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError
import datetime

logger = logging.getLogger(__name__)


class education(models.Model):
    _name = 'housemaidsystem.configuration.education'
    _description = 'education'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    # ================== Fields====================================================
    name = fields.Char(string="Name", size=60, requireed=True,)

    @api.model
    def create(self, vals):
        try:
            obj = super(education, self).create(vals)

            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>New education added at : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Setup name : <span>""" + obj.name + """</span></li>"""
            body_msg += u"""</ul>"""
            obj.message_post(body=body_msg)

        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)
        return obj


    def write(self, vals):
        try:
            obj = super(education, self).write(vals)
        except Exception as e:
            logger.exception("Write Method")
            raise ValidationError(e)
        return obj


    def unlink(self):
        try:
            return super(education, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)






