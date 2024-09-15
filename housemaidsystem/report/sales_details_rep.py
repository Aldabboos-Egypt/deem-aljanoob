from odoo import models, api
import logging
from odoo.exceptions import ValidationError
import datetime

logger = logging.getLogger(__name__)


class SalesDetailsRep(models.AbstractModel):
    _name = "report.housemaidsystem.sales_details_rep"
    _description = "Sales Details Report"


    def get_reservations_invoices(self, from_date, to_date):
        try:
            results = []
            date_between = None

            if from_date and to_date:
                from_date_obj = datetime.datetime.strptime(from_date, '%Y-%m-%d')
                to_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d')
                date_between = ' And a.date between \'' + str(from_date_obj) + '\' and \'' + str(to_date_obj) + '\''

            sql = 'select Distinct a.move_name, a.name, a.amount_total, a.residual, d.down_payment_amount, a.state, a.vendor_display_name, c.state, a.date, c.external_office_id '
            sql += 'from account_invoice a, account_move_line b, housemaid_applicant_applications c, housemaid_applicant_reservations d '
            sql += 'Where  a.id = b.invoice_id and b.application_id = c.id and c.id = d.application_id and d.application_id = b.application_id  and a.journal_id = 8 '
            sql += 'and c.state in (\'reservation\', \'visa\', \'expectedarrival\') '
            if date_between:
                sql += date_between + ' '
            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                res = {
                    'move_name': row[0] if row[0] else '',
                    'name': row[1] if row[1] else '',
                    'amount_total': row[2] if row[2] else 0.0,
                    'residual': row[3] if row[3] else 0.0,
                    'down_payment_amount': row[4] if row[4] else 0.0,
                    'invoice_state': row[5] if row[5] else '',
                    'vendor_display_name': row[6] if row[6] else '',
                    'application_state': row[7] if row[7] else '',
                    'invoice_date': row[8] if row[8] else '',
                    'external_office_id': row[9] if row[9] else '',
                }
                results.append(res)
                return results
        except Exception as e:
            logger.exception("get_reservations_invoices Method")
            raise ValidationError(e)

    def get_arrival_invoices(self, from_date, to_date):
        try:
            results = []
            date_between = None

            if from_date and to_date:
                from_date_obj = datetime.datetime.strptime(from_date, '%Y-%m-%d')
                to_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d')
                date_between = ' And a.date between \'' + str(from_date_obj) + '\' and \'' + str(to_date_obj) + '\''

            sql = 'select a.move_name, a.name, a.amount_total, a.residual, d.down_payment_amount, a.state, a.vendor_display_name, c.state, a.date '
            sql += 'from account_invoice a, account_move_line b, housemaid_applicant_applications c, housemaid_applicant_reservations d '
            sql += 'Where  a.id = b.invoice_id and b.application_id = c.id and c.id = d.application_id and d.application_id = b.application_id  and a.journal_id = 8 '
            sql += 'and c.state in (''arrival'') '
            if date_between:
                sql += date_between + ' '
            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                res = {
                    'move_name': row[0] if row[0] else '',
                    'name': row[1] if row[1] else '',
                    'amount_total': row[2] if row[2] else 0.0,
                    'residual': row[3] if row[3] else 0.0,
                    'down_payment_amount': row[4] if row[4] else 0.0,
                    'invoice_state': row[5] if row[5] else '',
                    'vendor_display_name': row[6] if row[6] else '',
                    'application_state': row[7] if row[7] else '',
                    'invoice_date': row[8] if row[8] else '',
                }
                results.append(res)
        except Exception as e:
            logger.exception("get_reservations_invoices Method")
            raise ValidationError(e)



    def get_trans(self, docs, scope, ):
        trans_lines=[]
        res =[]
        try:

            # Reservations
            if scope == 'reservation' or scope == 'all':
               # trans_lines.append(get_reservations_invoices())

                reservations = self.env['housemaidsystem.applicant.reservations'].search([('invoice_sales_id', '=', docs.id)],
                                                                                   limit = 1)
                for reservation in reservations:
                    if reservation.invoice_sales_id:
                        res = {
                            'date_invoice': reservation.invoice_sales_id.date_invoice,
                            'number': reservation.invoice_sales_id.number,
                            'vendor_display_name': reservation.invoice_sales_id.vendor_display_name,
                            'amount_untaxed': reservation.invoice_sales_id.amount_untaxed,
                            'residual': reservation.invoice_sales_id.residual,
                            'state': reservation.invoice_sales_id.state,
                            'tran_desc': 'New Arraival',
                            'app_state': reservation.application_id.state,
                            'HM_Code': reservation.application_id.name,
                        }
                    trans_lines.append(res)

            # Sell as test
            if scope == 'return' or scope == 'all':
                selltests = self.env['housemaidsystem.applicant.selltest'].search([('new_invoice_id', '=', docs.id)],
                                                                                   limit = 1)
                #selltests.application_id.external_office_id
                for selltest in selltests:
                    if selltest.new_invoice_id:
                        res = {
                            'date_invoice': selltest.new_invoice_id.date_invoice,
                            'number': selltest.new_invoice_id.number,
                            'vendor_display_name': selltest.new_invoice_id.vendor_display_name,
                            'amount_untaxed': selltest.new_invoice_id.amount_untaxed,
                            'residual': selltest.new_invoice_id.residual,
                            'state': selltest.new_invoice_id.state,
                            'tran_desc': 'Return Back',
                            'app_state': selltests.application_id.state,
                            'HM_Code': selltests.application_id.name,
                        }
                    trans_lines.append(res)

            return trans_lines

        except Exception as e:
            logger.exception("Get Trans Method : Error details " + str(e))
            raise ValidationError(e)



    @api.model
    def _get_report_values(self, docids, data=None):
        try:
            trans_lines = []
            from_date='1900-01-01'
            to_date = '1900-01-01'

            if data['from_date']:
                from_date = data['from_date']

            if data['to_date']:
                to_date = data['to_date']

            # Report Title

            report_title1 = "Report Scope: "
            if data['transaction_type'] == 'All Status':
                report_title1 += ' All'
            if data['transaction_type'] == 'reservation':
                report_title1 += ' Reservations - Visa - Expected Arrival'
            if data['transaction_type'] == 'arrival':
                report_title1 += ' Arrival Only'
            if data['transaction_type'] == 'return':
                report_title1 += ' Sell As Test Only'


            report_title2 = "From Date: " + data['from_date'] + " To Date: " + data['to_date']

            docs = self.env['account.invoice']

            # Reservations
            if data['transaction_type'] == 'reservation' or data['transaction_type'] == 'all':
                trans_lines.append(self.get_reservations_invoices(from_date, to_date))


            docargs = {
                'doc_ids': docids,
                'doc_model': 'account.invoice',
                'docs': docs,
                'scope': data['transaction_type'],
                'title1': report_title1,
                'title2': report_title2,
                'trans': trans_lines,
            }
            return docargs
        except Exception as e:
            logger.exception("Get Report Values Method")
            raise ValidationError(e)






