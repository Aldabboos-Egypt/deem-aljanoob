from . import accounting_integration
from odoo import models, fields, api



class CronJob(models.Model):
    _name = 'housemaidsystem.cron_job'
    _description = 'Housemaid System Cron Jobs'

    def add_to_contracts_print(self):
        print(self.env)
        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search([], )
        for rec in reservation_obj:
            application_obj = rec.application_id
            sponsor = rec.customer_id
            if application_obj and sponsor:
                print('start adding contract')
                accounting_integration.add_contract(reservation_obj, application_obj, sponsor)
