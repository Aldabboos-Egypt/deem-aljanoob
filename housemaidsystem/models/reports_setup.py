# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from dateutil import parser
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
import logging

logger = logging.getLogger(__name__)


class SystemReports(models.Model):
    _name = 'housemaidsystem.configuration.systemreports'
    _description = 'System Reports'
    _rec_name = 'name'


    # ================ Fields =================================
    name = fields.Char(string="Report Name", required=True)
    report_parameters = fields.One2many(comodel_name="housemaidsystem.configuration.systemreportparameters",
                                        string="System Report Parameters", inverse_name="systemreports_id",)

    _sql_constraints = [
        ('report_name_uniqe', 'unique (name)', "Report Name is exists !")
    ]
    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        obj = super(SystemReports, self).create(vals)
        return obj


    def unlink(self):
        return super(SystemReports, self).unlink()


    def write(self, vals):
        obj = super(SystemReports, self).write(vals)
        return obj


class SystemReportParameters(models.Model):
    _name = 'housemaidsystem.configuration.systemreportparameters'
    _description = 'System Report Parameters'
    _rec_name = 'name'

    # ================ Fields =================================
    name = fields.Char(string="Parameter Name", required=True)
    parameter_type = fields.Selection(string="", selection=[('string', 'String'), ('account', 'Account'), ('journal', 'Journal'),
                                                            ('number', 'Number'), ('boolean', 'Boolean'), ],
                                      required=True, default='string', )
    parameter_value_str = fields.Char(tring="String")
    parameter_value_account = fields.Many2one(comodel_name="account.account",
                                              string="Account")
    parameter_value_number = fields.Integer(tring="Number")
    parameter_value_boolean = fields.Boolean(tring="Boolean")
    parameter_value_journal = fields.Many2one(comodel_name="account.journal",
                                              string="Journal")

    systemreports_id = fields.Many2one(comodel_name="housemaidsystem.configuration.systemreports", string="System Reports", ondelete="cascade",)
    notes = fields.Char(string="Notes", required=False, size=250 )

    # _sql_constraints = [
    #     ('report_parameter_name_uniqe', 'unique (name)', "Report Paramter Name is exists !")
    # ]
    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        obj = super(SystemReportParameters, self).create(vals)
        return obj


    def unlink(self):
        return super(SystemReportParameters, self).unlink()


    def write(self, vals):
        obj = super(SystemReportParameters, self).write(vals)
        return obj



