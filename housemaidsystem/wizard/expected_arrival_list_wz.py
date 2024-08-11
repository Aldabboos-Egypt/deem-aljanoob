# -*- coding: utf-8 -*-
###############################################################################
# Create new folder called wizard
# add python file __init__.py
# add file name to file __init__.py
# make sure

###############################################################################
from odoo import models, fields, api


class ExpectedArrivalListWz(models.TransientModel):
    _name = "housemaidsystem.wizard.expected_arrival_list_wz"
    _description = "Expected Arrival List Wizard"

    from_date = fields.Date(string="Expected Arrival From Date")
    to_date = fields.Date(string="Expected Arrival To Date")
    external_office = fields.Many2one(comodel_name="housemaidsystem.configuration.externaloffices",
                                      string="External Office", required=False, )
    accumulated = fields.Boolean(string="Accumulated", default=False, )

    def print_report(self):
        data = {}

        data['from_date'] = self.from_date
        data['to_date'] = self.to_date
        data['external_office'] = self.external_office.id
        data['accumulated'] = self.accumulated

        report = self.env.ref('housemaidsystem.expected_arrival_list_rep_wiz_action')
        return report.report_action(self, data=data)
