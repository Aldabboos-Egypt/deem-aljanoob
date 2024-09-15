from odoo import models, api


class ApplicationActivationRep(models.AbstractModel):
    _name = "report.housemaidsystem.application_activation_rep"
    _description = "Application Activation Report"


    @api.model
    def _get_report_values(self, docids, data=None):
        invoice_domain = [('id', '!=', 0)]

        rep_head_line1 = ''
        rep_head_line2 = 'Invoice Status: All Status'
        rep_head_line3 = 'External Office: All'

        # =====================================================
        # 1) From Date
        if data['from_date']:
            invoice_domain.append(
                ('activate_date', '>=', data['from_date']),
            )
            rep_head_line1 = 'From Date: ' + data['from_date']
        # =====================================================
        # 2) To Date
        if data['to_date']:
            invoice_domain.append(
                ('activate_date', '<=', data['to_date']),
            )
            rep_head_line1 += ' - To Date: ' + data['to_date']
        # =====================================================
        # 3) External Offices
        if data['external_office']:
            invoice_domain.append(
                ('application_id.office_code.id', '=', data['external_office'])
            )
            external_office_obj = self.env['housemaidsystem.configuration.externaloffices'].search([('id', '=', data['external_office'])])
            if external_office_obj:
                rep_head_line3 = 'External Office: ' + external_office_obj.name

        # =====================================================

        docs = self.env['housemaidsystem.applicant.activateapplication'].search(invoice_domain)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'housemaidsystem.applicant.activateapplication',
            'docs': docs,
            'rep_head_line1': rep_head_line1,
            'rep_head_line3': rep_head_line3
        }
        return docargs
