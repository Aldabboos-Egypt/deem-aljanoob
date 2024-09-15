# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
import logging
from odoo.exceptions import ValidationError
import datetime

logger = logging.getLogger(__name__)


class ExternalOfficeTransDet(models.Model):
    _name = 'housemaidsystem.configuration.externalofficetransdet'
    _description = 'External Office Transactions Details'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char(string="Transaction Name", required=True)

    @api.model
    def create(self, vals):
        try:
            externalofficetransdet_obj = super(ExternalOfficeTransDet, self).create(vals)

            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>New External Office Transactions Details added at : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Transaction name : <span>""" + vals['name'] + """</span></li>"""
            body_msg += u"""</ul>"""

            externalofficetransdet_obj.message_post(body=body_msg)

            return externalofficetransdet_obj
        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)

