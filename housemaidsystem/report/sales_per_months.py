# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class SalesPerMonths(models.Model):

    _name = "housemaidsystem.report.salespermonths"
    _auto = False
    _description = "Sales Per Months"
    _rec_name = 'salse_man'

    sales_count = fields.Float(string="Sales Count", readonly=True)
    salse_man = fields.Char(string="Sales Man", readonly=True)
    sales_date = fields.Char(string="Sales Date", readonly=True)
    sales_tot = fields.Float(string="Total Sales", readonly=True)
    sales_rem = fields.Float(string="Total Dues", readonly=True)


    def _select(self):
        return """
            SELECT
              housemaid_applicant_applications.id as id,
              res_partner.name as salse_man,
              Count(housemaid_applicant_applications.ID) as "sales_count",
              to_char(account_invoice.date_invoice, 'Month-YYYY') as "sales_date",
              sum(account_invoice.amount_total) as "sales_tot",
              sum(account_invoice.residual) as "sales_rem"

        """

    def _from(self):
        return """
            From
            account_invoice , housemaid_applicant_applications , housemaid_applicant_reservations, res_partner, res_users
        """

    def _where(self):
        return """
            WHERE
              housemaid_applicant_applications.id = housemaid_applicant_reservations.application_id AND
              housemaid_applicant_reservations.invoice_sales_id = account_invoice.id AND
              housemaid_applicant_reservations.sales_man = res_users.id AND
              res_users.partner_id = res_partner.id AND
              DATE_PART('year', CURRENT_TIMESTAMP::date) - DATE_PART('year', account_invoice.date_invoice::date) = 0
        """

    def _group_by(self):
        group_by_str = """
            GROUP BY
            housemaid_applicant_applications.id, res_partner.name, to_char(account_invoice.date_invoice, 'Month-YYYY')

        """
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where(),self._group_by() )
        )
