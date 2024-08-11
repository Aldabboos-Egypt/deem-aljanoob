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


class activate_application(models.Model):
    _name = 'housemaidsystem.applicant.activateapplication'
    _description = 'Activate Applications History'

    activate_date = fields.Date(string="Activation Date", required=True, default=fields.Date.context_today)
    activate_reason = fields.Char(string="Activate Details", size=80)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications list")
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

    # ============================= Apply / Skip ===============================================

    def apply(self):
        try:
            application_obj=self.application_id
            if self.activate_reason == False:
                raise ValidationError("Activate Details is Required.")

            application_obj.message_post(body='Activation Reason is Required.')
            application_obj.state = 'application'
            application_obj.message_post(body='Activation Reason : ' + self.activate_reason)
        except Exception as e:
            logger.exception("apply Method")
            raise ValidationError(e)





