from odoo import models, api
import datetime
import logging
from odoo.exceptions import ValidationError
logger = logging.getLogger(__name__)


class StaffDuesRep(models.AbstractModel):
    _name = "report.housemaidsystem.staff_dues_rep"
    _description = "Staff Dues Report"


    def get_sum_per_account_employee(self, account_id, staff_id, signal, from_date, to_date):
        balance = 0.0
        sql = ''
        from_date_obj = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        to_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d')
        date_between = ' and date between \'' + str(from_date_obj) + '\' and \'' + str(to_date_obj) + '\''


        if signal == 'DR':
            sql = ("""select SUM(COALESCE(debit, 0.0))
            from account_move_line where employee = %s and account_id = %s %s
            group by account_id,employee """ % (staff_id, account_id, date_between))

        if signal == 'CR':
            sql = ("""select SUM(COALESCE(credit, 0.0))
            from account_move_line where employee = %s and account_id = %s %s
            group by account_id,employee """ % (staff_id, account_id, date_between))

        self.env.cr.execute(sql)
        for row in self.env.cr.fetchall():
            balance = row[0] if row[0] else 0.0

        return balance

    def get_trans(self, employee, from_date, to_date):
        trans_lines=[]
        res =[]
        try:
            emp_details = self.env['hr.employee'].search([('id', '=', employee.id)])
            if emp_details:
                system_reports = self.env['housemaidsystem.configuration.systemreports'].search([('report_name', '=', 'Staff Dues')])
                if system_reports:
                    system_report_parameters = self.env['housemaidsystem.configuration.systemreportparameters'].search(
                        [('systemreports_id', '=', system_reports.id)])
                    if system_report_parameters:
                        salary_payable = salary_expense = salary_paid_advance = bounce = 0

                        for rec in system_report_parameters:
                            if rec.parameter_name == 'Salary Payable GL':
                                salary_payable = rec.parameter_value_account.id
                            if rec.parameter_name == 'Salary Expense GL':
                                salary_expense = rec.parameter_value_account.id
                            if rec.parameter_name == 'Salary Paid in Advance GL':
                                salary_paid_advance = rec.parameter_value_account.id

                        res = {
                            'col1': self.get_sum_per_account_employee(salary_payable, emp_details.id, 'CR', from_date, to_date)
                            if self.get_sum_per_account_employee(salary_payable, emp_details.id, 'CR', from_date, to_date) else 0.0,

                            'col2': self.get_sum_per_account_employee(salary_expense, emp_details.id, 'DR', from_date, to_date)
                            if self.get_sum_per_account_employee(salary_expense, emp_details.id, 'DR', from_date, to_date) else 0.0,

                            'col3': self.get_sum_per_account_employee(salary_paid_advance, emp_details.id, 'DR', from_date, to_date)
                            if self.get_sum_per_account_employee(salary_paid_advance, emp_details.id, 'DR', from_date, to_date) else 0.0,

                            'col4': self.get_sum_per_account_employee(salary_paid_advance, emp_details.id, 'CR', from_date, to_date)
                            if self.get_sum_per_account_employee(salary_paid_advance, emp_details.id, 'CR', from_date, to_date) else 0.0,
                        }
                        trans_lines.append(res)




            return trans_lines

        except Exception as e:
            logger.exception("Get Trans Method : Error details " + str(e))
            raise ValidationError(e)

    @api.model
    def _get_report_values(self, docids, data=None):
        try:
            docargs = []
            domain = []
            report_title = ''
            if data['employee'] != 0:
                domain = [
                    ('id', '=', data['employee']),
                ]
            else:
                domain = [
                    ('id', '!=', 0),
                ]

            report_title = "(From Date: " + data['from_date'] + " To Date: " + data['to_date'] + " - Staff: "
            if data['employee'] != 0:
                report_title = report_title + data['employee_name']
            else:
                report_title = report_title + 'All'
            report_title = report_title + ')'


            docs = self.env['hr.employee'].search(domain, order='name')

            docargs = {
                'doc_ids': docids,
                'doc_model': 'hr.hr_employee',
                'docs': docs,
                'from_date':data['from_date'],
                'to_date': data['to_date'],
                'title': report_title,
                'trans': self.get_trans,
            }
            return docargs
        except Exception as e:
            logger.exception("Get Report Values Method")
            raise ValidationError(e)






