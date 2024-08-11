# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class LateReservations(models.Model):

    _name = "housemaidsystem.report.latereservations"
    _auto = False
    _description = "Housemaid Late Reservation"
    _rec_name = 'full_name'

    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", readonly=True)
    full_name = fields.Char(string="Name", readonly=True)
    deal_amount = fields.Float(string="Deal Amount", readonly=True)
    reservation_date = fields.Date(string="Reservation Date", readonly=True)
    late_days = fields.Float(string="Late Days",readonly=True)
    customer = fields.Char(strin="Customer", readonly=True)


    def _select(self):
        return """
            SELECT
            A.id,
            A.application_id,
            B.full_name,
            A.deal_amount,
            A.reservation_date,
            DATE_PART('day', now()::date) - DATE_PART('day', A.reservation_date::date) as late_days,
            C.name || ' ( Mobile: ' || (case when C.mobile isnull then 'no mbile' else C.mobile end) || ' )' As customer

        """


    def _from(self):
        return """
            From
            housemaid_applicant_reservations  A,housemaid_applicant_applications  B,res_partner  C
        """

    # def _join(self):
    #     return """
    #         JOIN crm_lead AS l ON m.res_id = l.id
    #     """

    def _where(self):
        return """
            WHERE
                A.application_id = B.id
                And A.customer_id = C.id
                AND B.state = 'reservation' 
                And DATE_PART('day', now()::date) - DATE_PART('day', A.reservation_date::date) > 3
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where())
        )
