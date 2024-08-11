# -*- coding: utf-8 -*-
###############################################################################
# Create new folder called wizard
# add python file __init__.py
# add file name to file __init__.py
# make sure

###############################################################################
from odoo import models, fields, api


class DeliverListWz(models.TransientModel):
    _name = "housemaidsystem.wizard.deliver_list_wz"
    _description = "Deliver List Wizard"

    from_date = fields.Date(string="Transactions From Date")
    to_date = fields.Date(string="Transactions To Date")
    external_office = fields.Many2one(comodel_name="housemaidsystem.configuration.externaloffices",
                                            string="External Office", required=False, )
    invoice_status = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),], string='Status',)

    accumulated = fields.Boolean(string="Accumulated", default=False,)


    def print_report(self):
        data = {}

        data['from_date'] = self.from_date
        data['to_date'] = self.to_date
        data['external_office'] = self.external_office.id
        data['invoice_status'] = self.invoice_status
        data['accumulated'] = self.accumulated

        report = self.env.ref('housemaidsystem.deliver_list_rep_wiz_action')
        return report.report_action(self, data=data)
