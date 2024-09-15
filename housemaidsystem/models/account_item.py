# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging

logger = logging.getLogger(__name__)


class AccountItems(models.Model):
    _name = 'housemaidsystem.configuration.accountitems'
    _rec_name = 'name'
    _description = 'Accounting Items'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char(string="Item Name", required=True, size=120)

    @api.model
    def create(self, vals):
        try:
            obj = super(AccountItems, self).create(vals)
            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>New Item Added at : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""</ul>"""
            obj.message_post(body=body_msg)

        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)
        return obj


    def write(self, vals):
        try:
            obj = super(AccountItems, self).write(vals)
        except Exception as e:
            logger.exception("Write Method")
            raise ValidationError(e)
        return obj


    def unlink(self):
        try:
            return super(AccountItems, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)


