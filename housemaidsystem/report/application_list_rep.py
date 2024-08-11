from odoo import models, api


class ReservationsListRep(models.AbstractModel):
    _name = "report.housemaidsystem.application_list_rep"
    _description = "Applications List Report"

    @api.model
    def _get_report_values(self, docids, data=None):

        application_domain = [('id', '!=', 0)]
        rep_head_line1 = ''
        # rep_head_line2 = 'Invoice Status: All Status'
        rep_head_line3 = 'External Office: All'

        # 1) From Date
        if data['from_date']:
            application_domain.append(
                ('applicant_date', '>=', data['from_date']),
            )
            rep_head_line1 = 'From Date: ' + data['from_date']
        # 2) To Date
        if data['to_date']:
            application_domain.append(
                ('applicant_date', '<=', data['to_date']),
            )
            rep_head_line1 += ' - To Date: ' + data['to_date']
        # 3) External Offices
        if data['external_office']:
            application_domain.append(
                ('office_code', '=', data['external_office'])
            )
            external_office_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
                [('id', '=', data['external_office'])])
            if external_office_obj:
                rep_head_line3 = 'External Office: ' + external_office_obj.name
        # 4) Invoice Status
        # if data['invoice_status']:
        #     if data['invoice_status'] == 'not_paid':
        #         invoice_domain.append(
        #             ('invoice_sales_id.payment_state', '!=', 'paid')
        #         )
        #         rep_head_line2 = 'Invoice Status: Not Paid or Partial Paid'
        #     if data['invoice_status'] != 'not_paid':
        #         invoice_domain.append(
        #             ('invoice_sales_id.payment_state', '=', 'paid')
        #         )
        #         rep_head_line2 = 'Invoice Status: Fully Paid'


        docs = self.env['housemaidsystem.applicant.applications'].search(application_domain)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'housemaidsystem.applicant.applications',
            'docs': docs,
            'accumulated': data['accumulated'],
            'rep_head_line1': rep_head_line1,
            # 'rep_head_line2': rep_head_line2,
            'rep_head_line3': rep_head_line3
        }
        return docargs
