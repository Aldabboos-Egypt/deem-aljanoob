# -*- coding: utf-8 -*-
###############################################################################
# Create new folder called wizard
# add python file __init__.py
# add file name to file __init__.py
# make sure

###############################################################################
from odoo import models, fields, api


class ApplicationCancellationWz(models.TransientModel):
    _name = "housemaidsystem.wizard.application_cancellation_wz"
    _description = "Application Cancellation Wizard"

    from_date = fields.Date(string="Transactions From Date")
    to_date = fields.Date(string="Transactions To Date")
    external_office = fields.Many2one(comodel_name="housemaidsystem.configuration.externaloffices",
                                            string="External Office", required=False, )

    accumulated = fields.Boolean(string="Accumulated", default=False, )

    def print_report(self):
        data = {}

        data['from_date'] = self.from_date
        data['to_date'] = self.to_date
        data['external_office'] = self.external_office.id
        data['accumulated'] = self.accumulated

        report = self.env.ref('housemaidsystem.application_cancellation_rep_wiz_action')
        return report.report_action(self, data=data)
