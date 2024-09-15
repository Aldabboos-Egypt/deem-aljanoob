from datetime import datetime
import time

from odoo import models, api


class ApplicationDetailsReport(models.AbstractModel):
    _name = "report.housemaidsystem.application_details_report"
    _description = "Application Details Report"

    def get_reservations_trans(self, id):
        reservations = self.env['housemaidsystem.applicant.reservations'].search([('application_id', '=', id)], limit=1)
        reservations_lines = []
        for reservation in reservations:
            res = {
                'reservation_date': reservation.reservation_date,
                'sponsor': reservation.customer_id.name_ar,
                'sponsor_mobile': reservation.customer_id.mobile,
                'sponsor_tel': reservation.customer_id.phone,
                'sponsor_civilid': reservation.customer_id.civil_id,
                'sponsor_address': reservation.customer_id.street,
                'deal_amount': reservation.deal_amount,
                'down_payment_amount': reservation.down_payment_amount,
                'remain_amount': reservation.deal_amount - (reservation.down_payment_amount if reservation.down_payment_amount else 0.0),
            }
            reservations_lines.append(res)
        return reservations_lines

    def get_visa_trans(self, id):
        visa = self.env['housemaidsystem.applicant.visa'].search([('application_id', '=', id)], limit=1)
        visa_lines = []
        for myvisa in visa:
            res = {
                'transaction_date': myvisa.transaction_date,
                'visa_no': myvisa.visa_no,
                'unified_no': myvisa.unified_no,
                'visa_issue_date': myvisa.visa_issue_date,
                'visa_exp_date': myvisa.visa_exp_date,
                'visa_rec_date': myvisa.visa_rec_date,
                'visa_snd_date': myvisa.visa_snd_date,
            }
            visa_lines.append(res)
        return visa_lines

    def get_expectedarrival_trans(self, doc):
        expectedarrival = self.env['housemaidsystem.applicant.expectedarrival'].search([('application_id', '=', doc)], limit=1)
        expectedarrival_lines = []
        for myexpectedarrival in expectedarrival:
            res = {
                'expected_arrival_date': myexpectedarrival.expected_arrival_date,
            }
            expectedarrival_lines.append(res)
        return expectedarrival_lines

    def get_arrival_trans(self, id):
        arrival = self.env['housemaidsystem.applicant.arrival'].search([('application_id', '=', id)], limit=1)
        arrival_lines = []
        for myarrival in arrival:
            res = {
                'arrival_date': myarrival.arrival_date,
            }
            arrival_lines.append(res)
        return arrival_lines

    def get_deliver_trans(self, id):
        deliver = self.env['housemaidsystem.applicant.deliver'].search([('application_id', '=', id)], limit=1)
        deliver_lines = []
        for mydeliver in deliver:
            res = {
                'deliver_date': mydeliver.deliver_date,
                'sponsor': mydeliver.customer_id.name_ar,
                'sponsor_mobile': mydeliver.customer_id.mobile,
                'sponsor_tel': mydeliver.customer_id.phone,
                'sponsor_civilid': mydeliver.customer_id.civil_id,
                'sponsor_address': mydeliver.customer_id.street,
                'deal_amount': mydeliver.invoice_total,
                'paid_amount': mydeliver.paid_amount,
                'discount_amount': mydeliver.discount_amount,
                'remain_amount': mydeliver.invoice_due,
            }
            deliver_lines.append(res)
        return deliver_lines

    def get_selltest_trans(self, docs):
        selltest = self.env['housemaidsystem.applicant.selltest'].search([('application_id', '=', docs.id)])
        selltest_lines = []
        for myselltest in selltest:
            if myselltest.test_status == 'selectaction':
                res = {
                    'action': 'Sell As test',
                    'test_date': myselltest.test_date,
                    'sponsor': myselltest.new_customer_id.name_ar,
                    'sponsor_mobile': myselltest.new_customer_id.mobile,
                    'sponsor_tel': myselltest.new_customer_id.phone,
                    'sponsor_civilid': myselltest.new_customer_id.civil_id,
                    'sponsor_address': myselltest.new_customer_id.street,
                    'deal_amount': myselltest.deal_amount,
                    'paid_amount': myselltest.down_payment_amount,
                    'discount_amount': myselltest.sepecial_discount_amount,
                    'remain_amount': myselltest.deal_amount - (myselltest.down_payment_amount if myselltest.down_payment_amount else 0.0),
                }
                selltest_lines.append(res)
            if myselltest.test_status == 'accepted':
                res = {
                    'action': 'Test Accepted',
                    'test_date': myselltest.accept_date,
                    'sponsor': myselltest.new_customer_id.name_ar,
                    'sponsor_mobile': myselltest.new_customer_id.mobile,
                    'sponsor_tel': myselltest.new_customer_id.phone,
                    'sponsor_civilid': myselltest.new_customer_id.civil_id,
                    'sponsor_address': myselltest.new_customer_id.street,
                    'deal_amount': myselltest.deal_amount,
                    'paid_amount': myselltest.complete_payment_amount + myselltest.down_payment_amount,
                    'discount_amount': myselltest.sepecial_discount_amount,
                    'remain_amount': 0,
                }
                selltest_lines.append(res)
            if myselltest.test_status == 'rejected':
                res = {
                    'action': 'Test Rejected',
                    'test_date': myselltest.reject_date,
                    'sponsor': myselltest.new_customer_id.name_ar,
                    'sponsor_mobile': myselltest.new_customer_id.mobile,
                    'sponsor_tel': myselltest.new_customer_id.phone,
                    'sponsor_civilid': myselltest.new_customer_id.civil_id,
                    'sponsor_address': myselltest.new_customer_id.street,
                    'deal_amount': myselltest.deal_amount,
                    'paid_amount': myselltest.down_payment_amount,
                    'discount_amount': 0,
                    'remain_amount': 0,
                }
                selltest_lines.append(res)
        return selltest_lines

    def get_external_office_trans(self, docs):
        external_office_ids = self.env['housemaidsystem.configuration.externalofficetrans'].search([('application_id', '=', docs.id)])

        external_office_ids_lines = []
        for external_office_id in external_office_ids:
            res = {
                'tran_date': external_office_id.tran_date,
                'tran_name': external_office_id.tran_name.name,
                'notes': external_office_id.notes,
            }
            external_office_ids_lines.append(res)
        return external_office_ids_lines

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['housemaidsystem.applicant.applications'].browse(docids)

        docargs = {
            'doc_model': 'report.housemaidsystem.application_details_report',
            'docs': docs,
            'time': time,
            'reservations': self.get_reservations_trans,
            'visa': self.get_visa_trans,
            'expectedarrival': self.get_expectedarrival_trans,
            'arrivals': self.get_arrival_trans,
            'delivers': self.get_deliver_trans,
            'selltests': self.get_selltest_trans,
            'external_office_ids': self.get_external_office_trans,
        }
        print(docargs)
        print(self.get_selltest_trans)
        return docargs
