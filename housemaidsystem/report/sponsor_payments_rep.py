from odoo import models, api


class SponsorPaymentsListRep(models.AbstractModel):
    _name = "report.housemaidsystem.sponsor_payments_rep"
    _description = "Sponsor Payments List Report"

    @api.model
    def _get_report_values(self, docids, data=None):

        invoice_domain = [('id', '!=', 0)]
        rep_head_line1 = ''
        rep_head_line2 = 'Transaction Type: All types'
        rep_head_line3 = 'Payment Type: All'
        rep_head_line4 = 'Confirmation Status: All'
        # ======================================================
        # 1) From Date
        if data['from_date']:
            invoice_domain.append(
                ('sposnor_payment_dt', '>=', data['from_date']),
            )
            rep_head_line1 = 'From Date: ' + data['from_date']
        # ======================================================
        # 2) To Date
        if data['to_date']:
            invoice_domain.append(
                ('sposnor_payment_dt', '<=', data['to_date']),
            )
            rep_head_line1 += ' - To Date: ' + data['to_date']
        # ======================================================
        # 3) Transaction Type (app_state)
        if data['app_state']:
            rep_head_line2 = 'Transaction Type: ' + data['app_state']
            if data['app_state'] != 'all':
                invoice_domain.append(
                    ('app_state', '=', data['app_state'])
                )

        # ======================================================
        # 4) Payment Type (payment_type)
        if data['payment_type']:
            rep_head_line3 = 'Payment Type: ' + data['payment_type']
            if data['payment_type'] != 'all':
                invoice_domain.append(
                    ('payment_type', '=', data['payment_type'])
                )

        # ======================================================
        # 4) Confirmation Status (state)
        if data['state']:
            rep_head_line4 = 'Confirmation Status: ' + data['state']
            if data['state'] != 'all':
                invoice_domain.append(
                    ('state', '=', data['state'])
                )




        docs = self.env['housemaidsystem.sponsorpayments'].search(invoice_domain)



        docargs = {
            'doc_ids': docids,
            'doc_model': 'housemaidsystem.sponsorpayments',
            'docs': docs,
            'accumulated': data['accumulated'],
            'rep_head_line1': rep_head_line1,
            'rep_head_line2': rep_head_line2,
            'rep_head_line3': rep_head_line3,
            'rep_head_line4': rep_head_line4
        }
        return docargs
