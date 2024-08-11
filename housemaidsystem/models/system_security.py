# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import ValidationError
from . import accounting_integration
import logging

logger = logging.getLogger(__name__)


class SystemSecurity(models.Model):
    _name = 'housemaidsystem.system.security'


    def set_security(self, status):
        try:
            domain = [('login', '!=', 'kamforhousemaid@gmail.com')]
            users_list = self.env['res.users'].search(domain)
            for rec in users_list:
                rec.active = status
        except Exception as e:
            logger.exception("set_security Method")
            raise ValidationError(e)


    def payment_post(self, action):
        try:
            if action == 1:
                reservations_obj = self.env['housemaidsystem.applicant.reservations'].search([('id','!=', 0)])
                for reservation in reservations_obj:
                    sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments'].\
                        search([('application_id', '=', reservation.application_id.id),
                                ('payment_reason', 'like', 'New reservation%')])
                    for sponsorpayment in sponsorpayments_obj:
                        logger.info("payment % is deleted", sponsorpayment.id)
                        sponsorpayment.unlink()

                    accounting_integration.add_sponsor_payment(reservation, 'reservation', 'Payment')
                    logger.info("Reservation % is updated", reservation.id)

            if action == 2:
                deliver_obj = self.env['housemaidsystem.applicant.deliver'].search([('id', '!=', 0)])
                for deliver in deliver_obj:
                    accounting_integration.add_sponsor_payment(deliver, 'deliverpaidfull', 'Payment')


        except Exception as e:
            logger.exception("payment_post Method")
            raise ValidationError(e)




