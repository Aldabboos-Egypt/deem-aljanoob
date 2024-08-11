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


class cancel_application(models.Model):
    _name = 'housemaidsystem.applicant.cancelapplication'
    _description = 'Cancel Applications History'

    cancel_date = fields.Date(string="Cancellation Date", required=True, default=fields.Date.context_today)
    cancel_reason = fields.Char(string="Cancellation Details", size=80)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications")
    application_state = fields.Selection(related='application_id.state')
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl', store=True)


    def _get_labor_dtl(self):
        try:
            for record in self:
                if not record.application_id == None:
                    self.office_code = record.application_id.office_code
        except Exception as e:
            logger.exception("_get_labor_dtl Method")
            raise ValidationError(e)

    # ============================= Create ===============================================

    def apply(self):
        application_obj=self.application_id
        if self.cancel_reason == False:
            application_obj.message_post(body='Cancel Details is Required.')
            raise ValidationError("Cancel Details is Required.")
        else:
            application_obj.state = 'cancelapplication'
            application_obj.message_post(body='Cancelation Reason : ' + self.cancel_reason)








