from odoo import models, api
import datetime
import logging
from odoo.exceptions import ValidationError
logger = logging.getLogger(__name__)


class HousemaidSalariesDuesRep(models.AbstractModel):
    _name = "report.housemaidsystem.housemaid_salaries_dues_rep"
    _description = "Housemaid Salaries Dues Report"

    def get_salary_gl(self, gl_type):
        try:
            gl_id = journal_id = num = 0
            str_value = parameter_type = ''
            bool_value = False

            sql = (""" select 
                b.parameter_value_account, 
                b.parameter_value_str, 
                b.parameter_value_journal, 
                b.parameter_value_number, 
                b.parameter_value_boolean,
                b.parameter_type
             FROM 
                housemaid_configuration_systemreports a, housemaid_configuration_systemreportparameters b
             where 
                 a.id = b.systemreports_id 
                 and a.name = 'Housemaid Dues'
                 and b.name =  '%s' """ % gl_type)

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                gl_id = row[0] if row[0] else 0.0
                str_value = row[1] if row[1] else ''
                journal_id = row[2] if row[2] else 0.0
                num = row[3] if row[3] else 0.0
                bool_value = row[4] if row[4] else False
                parameter_type = row[5] if row[5] else ''

            if parameter_type == 'account':
                return gl_id
            elif parameter_type == 'string':
                return str_value
            elif parameter_type == 'journal':
                return journal_id
            elif parameter_type == 'number':
                return num
            elif parameter_type == 'boolean':
                return bool_value

        except Exception as e:
            logger.exception("get_salary_gl Method")
            raise ValidationError(e)

    def get_returnbackfromfirstsposnor_trans(self, from_date, to_date, application_id):
        try:
            application_list = []
            #application_id = 0

            sql = (""" select 
                        a.application_id,
                        b.external_office_id,
                        b.full_name,
                        c.id,
                        c.name,
                        a.create_date::date,
                        a.hm_salary_move,
                        a.hm_salary,
                        e.name
                    from 
                        housemaid_applicant_returnbackfromfirstsponsor a,
                        housemaid_applicant_applications b,
                        res_partner c,
                        res_users d,
                        res_partner e
                    where
                        a.application_id = b.id
                        and a.customer_id = c.id
                        and a.create_uid = d.id
                        and d.partner_id = e.id
                        and a.application_id = (case when %i = 0 then a.application_id else %i end)
                        and a.create_date::date between '%s' and '%s'
                        and a.hm_salary > 0
                        order by a.create_date asc""" % (application_id, application_id, from_date, to_date))

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                res = {
                    'application_id': row[0] if row[0] else 0.0,
                    'code': row[1] if row[1] else '',
                    'name': row[2] if row[2] else '',
                    'sponsor_id': row[3] if row[3] else 0.0,
                    'sponsor_name': row[4] if row[4] else '',
                    'tran_date': row[5] if row[5] else '',
                    'move_id': row[6] if row[6] else 0.0,
                    'hm_salary': row[7] if row[7] else 0.0,
                    'sales_man': row[8] if row[8] else '',
                    'action_name': 'Return Back From First Sponsor',
                }
                application_list.append(res)

            return application_list
        except Exception as e:
            logger.exception("get_list_of_applications Method")
            raise ValidationError(e)

    def get_sellastest_trans(self, from_date, to_date, application_id):
        try:
            application_list = []
            #application_id = 0

            sql = (""" select 
                        a.application_id,
                        b.external_office_id,
                        b.full_name,
                        c.id,
                        c.name,
                        a.create_date::date,
                        a.hm_salary_move,
                        a.hm_salary,
                        e.name
                    from 
                        housemaid_applicant_selltest a,
                        housemaid_applicant_applications b,
                        res_partner c,
                        res_users d,
                        res_partner e
                    where
                        a.application_id = b.id
                        and a.new_customer_id = c.id
                        and a.create_uid = d.id
                        and d.partner_id = e.id
                        and a.test_status = 'rejected'
                        and a.application_id = (case when %i = 0 then a.application_id else %i end)
                        and a.create_date::date between '%s' and '%s'
                        and a.hm_salary > 0
                        order by a.create_date asc""" % (application_id, application_id, from_date, to_date))

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                res = {
                    'application_id': row[0] if row[0] else 0.0,
                    'code': row[1] if row[1] else '',
                    'name': row[2] if row[2] else '',
                    'sponsor_id': row[3] if row[3] else 0.0,
                    'sponsor_name': row[4] if row[4] else '',
                    'tran_date': row[5] if row[5] else '',
                    'move_id': row[6] if row[6] else 0.0,
                    'hm_salary': row[7] if row[7] else 0.0,
                    'sales_man': row[8] if row[8] else '',
                    'action_name': 'Return Back From First Sponsor',
                }
                application_list.append(res)

            return application_list
        except Exception as e:
            logger.exception("get_sellastest_trans Method")
            raise ValidationError(e)

    def get_returnbackfromlastsposnor_trans(self, from_date, to_date, application_id):
        try:
            application_list = []
            #application_id = 0

            sql = (""" select 
                        a.application_id,
                        b.external_office_id,
                        b.full_name,
                        c.id,
                        c.name,
                        a.create_date::date,
                        a.hm_salary_move,
                        a.hm_salary,
                        e.name
                    from 
                        housemaid_applicant_returnbackfromlastsponsor a,
                        housemaid_applicant_applications b,
                        res_partner c,
                        res_users d,
                        res_partner e
                    where
                        a.application_id = b.id
                        and a.old_customer_id = c.id
                        and a.create_uid = d.id
                        and d.partner_id = e.id
                        and a.application_id = (case when %i = 0 then a.application_id else %i end)
                        and a.create_date::date between '%s' and '%s'
                        and a.hm_salary > 0
                        order by a.create_date asc""" % (application_id, application_id, from_date, to_date))

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                res = {
                    'application_id': row[0] if row[0] else 0.0,
                    'code': row[1] if row[1] else '',
                    'name': row[2] if row[2] else '',
                    'sponsor_id': row[3] if row[3] else 0.0,
                    'sponsor_name': row[4] if row[4] else '',
                    'tran_date': row[5] if row[5] else '',
                    'move_id': row[6] if row[6] else 0.0,
                    'hm_salary': row[7] if row[7] else 0.0,
                    'sales_man': row[8] if row[8] else '',
                    'action_name': 'Return Back From First Sponsor',
                }
                application_list.append(res)

            return application_list
        except Exception as e:
            logger.exception("get_list_of_applications Method")
            raise ValidationError(e)

    def get_collection_trans(self, application_id, sponsor_id):
        try:
            results = []
            amt = 0

            gl_id = self.get_salary_gl('Liability GL')
            sql = ("""SELECT
                        a.date, 
                        a.name, 
                        COALESCE(a.credit, 0.0), 
                        c.name 
                    FROM 
                        account_move_line a, res_users b, res_partner c, account_move_line d, account_account e, account_move aa, account_move dd
                    WHERE 
                        a.create_uid = b.id 
                        and b.partner_id = c.id 
                        and a.account_id = 201
                        and a.move_id = aa.id
                        and d.move_id = dd.id
                        and COALESCE(a.credit, 0.0) > 0
                        and a.move_id = d.move_id
                        and d.account_id = e.id
                        and e.internal_type = 'liquidity'
                        and a.account_id = %i 
                        and a.partner_id = %i
                        and aa.state = 'posted'
                        and dd.state = 'posted'
                        and a.application_id = (case when %i = 0 then a.application_id else %i end) """ %(gl_id, sponsor_id, application_id, application_id))

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                amt += row[2] if row[2] else 0.0
                res = {
                    'date': row[0] if row[0] else '',
                    'tran_desc': row[1] if row[1] else '',
                    'amt': amt,
                    'sales_man': row[3] if row[3] else '',
                }
                results.append(res)

            # Get The posted transactions from ACC. Rec.
            # ==========================================
            gl_id = self.get_salary_gl('Receivable')
            tran_ref = self.get_salary_gl('Salary Paid By Sponsor')

            sql = ("""SELECT
                           a.date, 
                           a.name, 
                           COALESCE(a.credit, 0.0), 
                           c.name 
                       FROM 
                           account_move_line a, res_users b, res_partner c, account_move_line d, account_account e, account_move aa, account_move dd
                       WHERE 
                           a.create_uid = b.id 
                           and b.partner_id = c.id 
                           and COALESCE(a.credit, 0.0) > 0
                           and a.move_id = d.move_id
                           and a.move_id = aa.id
                           and d.move_id = dd.id
                           and d.account_id = e.id
                           and aa.state = 'posted'
                           and dd.state = 'posted'
                           and e.internal_type = 'liquidity'
                           and a.account_id = %i 
                           and a.partner_id = %i
                           and a.name = '%s'
                           and a.application_id = (case when %i = 0 then a.application_id else %i end) """ % (
                gl_id, sponsor_id, tran_ref, application_id, application_id))

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                amt += row[2] if row[2] else 0.0
                res = {
                    'date': row[0] if row[0] else '',
                    'tran_desc': row[1] if row[1] else '',
                    'amt': amt,
                    'sales_man': row[3] if row[3] else '',
                }
                results.append(res)

            return results
        except Exception as e:
            logger.exception("get_collection_trans Method")
            raise ValidationError(e)

    def get_paid_trans(self, application_id, sponsor_id):
        try:
            results = []
            amt = 0
            tran_ref = self.get_salary_gl('Salary Paid By Office')

            # Get The posted transactions from cash.
            # ==========================================
            gl_id = self.get_salary_gl('Liability GL')
            sql = ("""SELECT
                        a.date, 
                        a.name, 
                        COALESCE(a.debit, 0.0), 
                        c.name 
                    FROM 
                        account_move_line a, res_users b, res_partner c, account_move_line d, account_account e, account_move aa, account_move dd
                    WHERE 
                        a.create_uid = b.id 
                        and b.partner_id = c.id 
                        and a.account_id = 201
                        and a.move_id = aa.id
                        and d.move_id = dd.id
                        and COALESCE(a.debit, 0.0) > 0
                        and a.move_id = d.move_id
                        and d.account_id = e.id
                        and aa.state = 'posted'
                        and dd.state = 'posted'
                        and e.internal_type = 'liquidity'   
                        and a.account_id = %i 
                        and a.partner_id = %i
                        and a.name = '%s'
                        and a.application_id = (case when %i = 0 then a.application_id else %i end) """ %(gl_id, sponsor_id, tran_ref, application_id, application_id))

            self.env.cr.execute(sql)
            for row in self.env.cr.fetchall():
                amt += row[2] if row[2] else 0.0
                res = {
                    'date': row[0] if row[0] else '',
                    'tran_desc': row[1] if row[1] else '',
                    'amt': amt,
                    'sales_man': row[3] if row[3] else '',
                }
                results.append(res)

            return results
        except Exception as e:
            logger.exception("get_paid_trans Method")
            raise ValidationError(e)

    def get_recognized_trans(self, data):
        try:
            all_trans = returnbackfromfirstsposnor_trans = returnbackfromlastsposnor_trans = sellastest_trans = []

            returnbackfromfirstsposnor_trans = self.get_returnbackfromfirstsposnor_trans(data['from_date'],
                                                                                         data['to_date'], data['application_id'])
            returnbackfromlastsposnor_trans = self.get_returnbackfromlastsposnor_trans(data['from_date'],
                                                                                         data['to_date'],
                                                                                         data['application_id'])
            sellastest_trans = self.get_sellastest_trans(data['from_date'],data['to_date'], data['application_id'])

            for returnbackfromfirstsposnor_tran in returnbackfromfirstsposnor_trans:
                res = {
                    'application_id': returnbackfromfirstsposnor_tran.get('application_id', ''),
                    'code': returnbackfromfirstsposnor_tran.get('code', ''),
                    'name': returnbackfromfirstsposnor_tran.get('name', ''),
                    'sponsor_id': returnbackfromfirstsposnor_tran.get('sponsor_id', ''),
                    'sponsor_name': returnbackfromfirstsposnor_tran.get('sponsor_name', ''),
                    'tran_date': returnbackfromfirstsposnor_tran.get('tran_date', ''),
                    'move_id': returnbackfromfirstsposnor_tran.get('move_id', ''),
                    'hm_salary': returnbackfromfirstsposnor_tran.get('hm_salary', ''),
                    'sales_man': returnbackfromfirstsposnor_tran.get('sales_man', ''),
                    'action_name': 'Return Back From First Sponsor',
                }
                all_trans.append(res)

            for returnbackfromlastsposnor_tran in returnbackfromlastsposnor_trans:
                res = {
                    'application_id': returnbackfromlastsposnor_tran.get('application_id', ''),
                    'code': returnbackfromlastsposnor_tran.get('code', ''),
                    'name': returnbackfromlastsposnor_tran.get('name', ''),
                    'sponsor_id': returnbackfromlastsposnor_tran.get('sponsor_id', ''),
                    'sponsor_name': returnbackfromlastsposnor_tran.get('sponsor_name', ''),
                    'tran_date': returnbackfromlastsposnor_tran.get('tran_date', ''),
                    'move_id': returnbackfromlastsposnor_tran.get('move_id', ''),
                    'hm_salary': returnbackfromlastsposnor_tran.get('hm_salary', ''),
                    'sales_man': returnbackfromlastsposnor_tran.get('sales_man', ''),
                    'action_name': 'Return Back From Last Sponsor',
                }
                all_trans.append(res)

            for sellastest_tran in sellastest_trans:
                res = {
                    'application_id': sellastest_tran.get('application_id', ''),
                    'code': sellastest_tran.get('code', ''),
                    'name': sellastest_tran.get('name', ''),
                    'sponsor_id': sellastest_tran.get('sponsor_id', ''),
                    'sponsor_name': sellastest_tran.get('sponsor_name', ''),
                    'tran_date': sellastest_tran.get('tran_date', ''),
                    'move_id': sellastest_tran.get('move_id', ''),
                    'hm_salary': sellastest_tran.get('hm_salary', ''),
                    'sales_man': sellastest_tran.get('sales_man', ''),
                    'action_name': 'Sell As Test',
                }
                all_trans.append(res)



            return all_trans


        except Exception as e:
            logger.exception("get_recognized_trans Method")
            raise ValidationError(e)

    @api.model
    def _get_report_values(self, docids, data=None):
        try:
            def SortList(e):
                return e['code']

            docs = self.get_recognized_trans(data)
            docs.sort(key=SortList)



            report_title = "(From Date: " + data['from_date'] + " To Date: " + data['to_date'] + ")"


            docargs = {
                'doc_ids': docids,
                'doc_model': 'account.move.line',
                'docs': docs,
                'from_date':data['from_date'],
                'to_date': data['to_date'],
                'title': report_title,
                'get_collection_trans': self.get_collection_trans,
                'get_paid_trans': self.get_paid_trans,
            }
            return docargs
        except Exception as e:
            logger.exception("Get Report Values Method")
            raise ValidationError(e)


# class HousemaidSalariesDuesRepExcel(models.AbstractModel):
#     _name = "report.housemaidsystem.housemaid_salaries_dues_rep_excel"
#     _inherit = 'report.report_xlsx.abstract'
#     _description = "Housemaid Salaries Dues Excel Report"
#
#     def get_salary_gl(self, gl_type):
#         try:
#             gl_id = journal_id = num = 0
#             str_value = parameter_type = ''
#             bool_value = False
#
#             sql = (""" select
#                 b.parameter_value_account,
#                 b.parameter_value_str,
#                 b.parameter_value_journal,
#                 b.parameter_value_number,
#                 b.parameter_value_boolean,
#                 b.parameter_type
#              FROM
#                 housemaid_configuration_systemreports a, housemaid_configuration_systemreportparameters b
#              where
#                  a.id = b.systemreports_id
#                  and a.name = 'Housemaid Dues'
#                  and b.name =  '%s' """ % gl_type)
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 gl_id = row[0] if row[0] else 0.0
#                 str_value = row[1] if row[1] else ''
#                 journal_id = row[2] if row[2] else 0.0
#                 num = row[3] if row[3] else 0.0
#                 bool_value = row[4] if row[4] else False
#                 parameter_type = row[5] if row[5] else ''
#
#             if parameter_type == 'account':
#                 return gl_id
#             elif parameter_type == 'string':
#                 return str_value
#             elif parameter_type == 'journal':
#                 return journal_id
#             elif parameter_type == 'number':
#                 return num
#             elif parameter_type == 'boolean':
#                 return bool_value
#
#         except Exception as e:
#             logger.exception("get_salary_gl Method")
#             raise ValidationError(e)
#
#     def get_returnbackfromfirstsposnor_trans(self, from_date, to_date, application_id):
#         try:
#             application_list = []
#             #application_id = 0
#
#             sql = (""" select
#                         a.application_id,
#                         b.external_office_id,
#                         b.full_name,
#                         c.id,
#                         c.name,
#                         a.create_date::date,
#                         a.hm_salary_move,
#                         a.hm_salary,
#                         e.name
#                     from
#                         housemaid_applicant_returnbackfromfirstsponsor a,
#                         housemaid_applicant_applications b,
#                         res_partner c,
#                         res_users d,
#                         res_partner e
#                     where
#                         a.application_id = b.id
#                         and a.customer_id = c.id
#                         and a.create_uid = d.id
#                         and d.partner_id = e.id
#                         and a.application_id = (case when %i = 0 then a.application_id else %i end)
#                         and a.create_date::date between '%s' and '%s'
#                         and a.hm_salary > 0
#                         order by a.create_date asc""" % (application_id, application_id, from_date, to_date))
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 res = {
#                     'application_id': row[0] if row[0] else 0.0,
#                     'code': row[1] if row[1] else '',
#                     'name': row[2] if row[2] else '',
#                     'sponsor_id': row[3] if row[3] else 0.0,
#                     'sponsor_name': row[4] if row[4] else '',
#                     'tran_date': row[5] if row[5] else '',
#                     'move_id': row[6] if row[6] else 0.0,
#                     'hm_salary': row[7] if row[7] else 0.0,
#                     'sales_man': row[8] if row[8] else '',
#                     'action_name': 'Return Back From First Sponsor',
#                 }
#                 application_list.append(res)
#
#             return application_list
#         except Exception as e:
#             logger.exception("get_list_of_applications Method")
#             raise ValidationError(e)
#
#     def get_sellastest_trans(self, from_date, to_date, application_id):
#         try:
#             application_list = []
#             #application_id = 0
#
#             sql = (""" select
#                         a.application_id,
#                         b.external_office_id,
#                         b.full_name,
#                         c.id,
#                         c.name,
#                         a.create_date::date,
#                         a.hm_salary_move,
#                         a.hm_salary,
#                         e.name
#                     from
#                         housemaid_applicant_selltest a,
#                         housemaid_applicant_applications b,
#                         res_partner c,
#                         res_users d,
#                         res_partner e
#                     where
#                         a.application_id = b.id
#                         and a.new_customer_id = c.id
#                         and a.create_uid = d.id
#                         and d.partner_id = e.id
#                         and a.test_status = 'rejected'
#                         and a.application_id = (case when %i = 0 then a.application_id else %i end)
#                         and a.create_date::date between '%s' and '%s'
#                         and a.hm_salary > 0
#                         order by a.create_date asc""" % (application_id, application_id, from_date, to_date))
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 res = {
#                     'application_id': row[0] if row[0] else 0.0,
#                     'code': row[1] if row[1] else '',
#                     'name': row[2] if row[2] else '',
#                     'sponsor_id': row[3] if row[3] else 0.0,
#                     'sponsor_name': row[4] if row[4] else '',
#                     'tran_date': row[5] if row[5] else '',
#                     'move_id': row[6] if row[6] else 0.0,
#                     'hm_salary': row[7] if row[7] else 0.0,
#                     'sales_man': row[8] if row[8] else '',
#                     'action_name': 'Sell As test',
#                 }
#                 application_list.append(res)
#
#             return application_list
#         except Exception as e:
#             logger.exception("get_sellastest_trans Method")
#             raise ValidationError(e)
#
#     def get_returnbackfromlastsposnor_trans(self, from_date, to_date, application_id):
#         try:
#             application_list = []
#             #application_id = 0
#
#             sql = (""" select
#                         a.application_id,
#                         b.external_office_id,
#                         b.full_name,
#                         c.id,
#                         c.name,
#                         a.create_date::date,
#                         a.hm_salary_move,
#                         a.hm_salary,
#                         e.name
#                     from
#                         housemaid_applicant_returnbackfromlastsponsor a,
#                         housemaid_applicant_applications b,
#                         res_partner c,
#                         res_users d,
#                         res_partner e
#                     where
#                         a.application_id = b.id
#                         and a.old_customer_id = c.id
#                         and a.create_uid = d.id
#                         and d.partner_id = e.id
#                         and a.application_id = (case when %i = 0 then a.application_id else %i end)
#                         and a.create_date::date between '%s' and '%s'
#                         and a.hm_salary > 0
#                         order by a.create_date asc""" % (application_id, application_id, from_date, to_date))
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 res = {
#                     'application_id': row[0] if row[0] else 0.0,
#                     'code': row[1] if row[1] else '',
#                     'name': row[2] if row[2] else '',
#                     'sponsor_id': row[3] if row[3] else 0.0,
#                     'sponsor_name': row[4] if row[4] else '',
#                     'tran_date': row[5] if row[5] else '',
#                     'move_id': row[6] if row[6] else 0.0,
#                     'hm_salary': row[7] if row[7] else 0.0,
#                     'sales_man': row[8] if row[8] else '',
#                     'action_name': 'Return Back From Last Sponsor',
#                 }
#                 application_list.append(res)
#
#             return application_list
#         except Exception as e:
#             logger.exception("get_list_of_applications Method")
#             raise ValidationError(e)
#
#     def get_collection_trans(self, application_id, sponsor_id):
#         try:
#             results = []
#             amt = 0
#
#             gl_id = self.get_salary_gl('Liability GL')
#             sql = ("""SELECT
#                         a.date,
#                         a.name,
#                         COALESCE(a.credit, 0.0),
#                         c.name
#                     FROM
#                         account_move_line a, res_users b, res_partner c, account_move_line d, account_account e, account_move aa, account_move dd
#                     WHERE
#                         a.create_uid = b.id
#                         and b.partner_id = c.id
#                         and a.account_id = 201
#                         and a.move_id = aa.id
#                         and d.move_id = dd.id
#                         and COALESCE(a.credit, 0.0) > 0
#                         and a.move_id = d.move_id
#                         and d.account_id = e.id
#                         and e.internal_type = 'liquidity'
#                         and a.account_id = %i
#                         and a.partner_id = %i
#                         and aa.state = 'posted'
#                         and dd.state = 'posted'
#                         and a.application_id = (case when %i = 0 then a.application_id else %i end) """ %(gl_id, sponsor_id, application_id, application_id))
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 amt += row[2] if row[2] else 0.0
#                 res = {
#                     'date': row[0] if row[0] else '',
#                     'tran_desc': row[1] if row[1] else '',
#                     'amt': amt,
#                     'sales_man': row[3] if row[3] else '',
#                 }
#                 results.append(res)
#
#             # Get The posted transactions from ACC. Rec.
#             # ==========================================
#             gl_id = self.get_salary_gl('Receivable')
#             tran_ref = self.get_salary_gl('Salary Paid By Sponsor')
#
#             sql = ("""SELECT
#                            a.date,
#                            a.name,
#                            COALESCE(a.credit, 0.0),
#                            c.name
#                        FROM
#                            account_move_line a, res_users b, res_partner c, account_move_line d, account_account e, account_move aa, account_move dd
#                        WHERE
#                            a.create_uid = b.id
#                            and b.partner_id = c.id
#                            and COALESCE(a.credit, 0.0) > 0
#                            and a.move_id = d.move_id
#                            and a.move_id = aa.id
#                            and d.move_id = dd.id
#                            and d.account_id = e.id
#                            and aa.state = 'posted'
#                            and dd.state = 'posted'
#                            and e.internal_type = 'liquidity'
#                            and a.account_id = %i
#                            and a.partner_id = %i
#                            and a.name = '%s'
#                            and a.application_id = (case when %i = 0 then a.application_id else %i end) """ % (
#                 gl_id, sponsor_id, tran_ref, application_id, application_id))
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 amt += row[2] if row[2] else 0.0
#                 res = {
#                     'date': row[0] if row[0] else '',
#                     'tran_desc': row[1] if row[1] else '',
#                     'amt': amt,
#                     'sales_man': row[3] if row[3] else '',
#                 }
#                 results.append(res)
#
#             return results
#         except Exception as e:
#             logger.exception("get_collection_trans Method")
#             raise ValidationError(e)
#
#     def get_paid_trans(self, application_id, sponsor_id):
#         try:
#             results = []
#             amt = 0
#             tran_ref = self.get_salary_gl('Salary Paid By Office')
#
#             # Get The posted transactions from cash.
#             # ==========================================
#             gl_id = self.get_salary_gl('Liability GL')
#             sql = ("""SELECT
#                         a.date,
#                         a.name,
#                         COALESCE(a.debit, 0.0),
#                         c.name
#                     FROM
#                         account_move_line a, res_users b, res_partner c, account_move_line d, account_account e, account_move aa, account_move dd
#                     WHERE
#                         a.create_uid = b.id
#                         and b.partner_id = c.id
#                         and a.account_id = 201
#                         and a.move_id = aa.id
#                         and d.move_id = dd.id
#                         and COALESCE(a.debit, 0.0) > 0
#                         and a.move_id = d.move_id
#                         and d.account_id = e.id
#                         and aa.state = 'posted'
#                         and dd.state = 'posted'
#                         and e.internal_type = 'liquidity'
#                         and a.account_id = %i
#                         and a.partner_id = %i
#                         and a.name = '%s'
#                         and a.application_id = (case when %i = 0 then a.application_id else %i end) """ %(gl_id, sponsor_id, tran_ref, application_id, application_id))
#
#             self.env.cr.execute(sql)
#             for row in self.env.cr.fetchall():
#                 amt += row[2] if row[2] else 0.0
#                 res = {
#                     'date': row[0] if row[0] else '',
#                     'tran_desc': row[1] if row[1] else '',
#                     'amt': amt,
#                     'sales_man': row[3] if row[3] else '',
#                 }
#                 results.append(res)
#
#             return results
#         except Exception as e:
#             logger.exception("get_paid_trans Method")
#             raise ValidationError(e)
#
#     def get_recognized_trans(self, data):
#         try:
#             all_trans = returnbackfromfirstsposnor_trans = returnbackfromlastsposnor_trans = sellastest_trans = []
#             returnbackfromfirstsposnor_trans = self.get_returnbackfromfirstsposnor_trans(data['from_date'],
#                                                                                          data['to_date'], data['application_id'])
#             returnbackfromlastsposnor_trans = self.get_returnbackfromlastsposnor_trans(data['from_date'],
#                                                                                          data['to_date'],
#                                                                                          data['application_id'])
#             sellastest_trans = self.get_sellastest_trans(data['from_date'],data['to_date'], data['application_id'])
#
#             for returnbackfromfirstsposnor_tran in returnbackfromfirstsposnor_trans:
#                 res = {
#                     'application_id': returnbackfromfirstsposnor_tran.get('application_id', ''),
#                     'code': returnbackfromfirstsposnor_tran.get('code', ''),
#                     'name': returnbackfromfirstsposnor_tran.get('name', ''),
#                     'sponsor_id': returnbackfromfirstsposnor_tran.get('sponsor_id', ''),
#                     'sponsor_name': returnbackfromfirstsposnor_tran.get('sponsor_name', ''),
#                     'tran_date': returnbackfromfirstsposnor_tran.get('tran_date', ''),
#                     'move_id': returnbackfromfirstsposnor_tran.get('move_id', ''),
#                     'hm_salary': returnbackfromfirstsposnor_tran.get('hm_salary', ''),
#                     'sales_man': returnbackfromfirstsposnor_tran.get('sales_man', ''),
#                     'action_name': 'Return Back From First Sponsor',
#                 }
#                 all_trans.append(res)
#
#             for returnbackfromlastsposnor_tran in returnbackfromlastsposnor_trans:
#                 res = {
#                     'application_id': returnbackfromlastsposnor_tran.get('application_id', ''),
#                     'code': returnbackfromlastsposnor_tran.get('code', ''),
#                     'name': returnbackfromlastsposnor_tran.get('name', ''),
#                     'sponsor_id': returnbackfromlastsposnor_tran.get('sponsor_id', ''),
#                     'sponsor_name': returnbackfromlastsposnor_tran.get('sponsor_name', ''),
#                     'tran_date': returnbackfromlastsposnor_tran.get('tran_date', ''),
#                     'move_id': returnbackfromlastsposnor_tran.get('move_id', ''),
#                     'hm_salary': returnbackfromlastsposnor_tran.get('hm_salary', ''),
#                     'sales_man': returnbackfromlastsposnor_tran.get('sales_man', ''),
#                     'action_name': 'Return Back From Last Sponsor',
#                 }
#                 all_trans.append(res)
#
#             for sellastest_tran in sellastest_trans:
#                 res = {
#                     'application_id': sellastest_tran.get('application_id', ''),
#                     'code': sellastest_tran.get('code', ''),
#                     'name': sellastest_tran.get('name', ''),
#                     'sponsor_id': sellastest_tran.get('sponsor_id', ''),
#                     'sponsor_name': sellastest_tran.get('sponsor_name', ''),
#                     'tran_date': sellastest_tran.get('tran_date', ''),
#                     'move_id': sellastest_tran.get('move_id', ''),
#                     'hm_salary': sellastest_tran.get('hm_salary', ''),
#                     'sales_man': sellastest_tran.get('sales_man', ''),
#                     'action_name': 'Sell As Test',
#                 }
#                 all_trans.append(res)
#
#
#
#             return all_trans
#
#
#         except Exception as e:
#             logger.exception("get_recognized_trans Method")
#             raise ValidationError(e)
#
#     @api.model
#     def generate_xlsx_report(self, workbook, data, wizard):
#         try:
#             def get_date_format(date):
#                 if date:
#                     # date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
#                     date = date.strftime('%Y-%m-%d')
#                 return date
#
#             def SortList(e):
#                 return e['code']
#
#             def list_of_dict_search(mylist, mykey):
#                 found = False
#                 for mydict in mylist:
#                     if mydict["key"] == mykey:
#                         found = True
#                 return found
#
#             # Pre-Format
#             header_line_format_string = workbook.add_format(
#                 {'bold': True, 'left': 1, 'font_size': 12, 'text_wrap': 0, 'bg_color': '#e7e3e2'})
#             header_line_format_num = workbook.add_format(
#                 {'bold': True, 'right': 1, 'font_size': 12, 'text_wrap': 0, 'bg_color': '#e7e3e2'})
#
#             normal_line_format_string_nowrap = workbook.add_format(
#                 {'bold': False, 'left': 1, 'font_size': 10, 'text_wrap': 0})
#             normal_line_format_string_wrap = workbook.add_format(
#                 {'bold': False, 'left': 1, 'font_size': 10, 'text_wrap': 1})
#
#             normal_line_format_num_KWD = workbook.add_format(
#                 {'bold': False, 'right': 1, 'font_size': 10, 'text_wrap': 0, 'num_format': '#,##0.000'})
#             normal_line_format_num_USD = workbook.add_format(
#                 {'bold': False, 'right': 1, 'font_size': 10, 'text_wrap': 0, 'num_format': '#,##0.00'})
#
#
#             # Data Object
#             sponsor_trans = self.get_recognized_trans(data)
#             sponsor_trans.sort(key=SortList)
#
#             current_row = 0
#             sheet = workbook.add_worksheet("Housemaid Salaries")
#
#             sheet.write(current_row, 0, 'Tran Date', header_line_format_string)
#             sheet.set_column(0, 0, 13)
#
#             sheet.write(current_row, 1, 'Code', header_line_format_string)
#             sheet.set_column(1, 1, 10)
#
#             sheet.write(current_row, 2, 'Sponsor Name', header_line_format_string)
#             sheet.set_column(2, 2, 20)
#
#             sheet.write(current_row, 3, 'Tran Description', header_line_format_string)
#             sheet.set_column(3, 3, 25)
#
#             sheet.write(current_row, 4, 'Processed By', header_line_format_string)
#             sheet.set_column(4, 4, 17)
#
#             sheet.write(current_row, 5, 'Salary Recognized', header_line_format_num)
#             sheet.set_column(5, 5, 15)
#
#             sheet.write(current_row, 6, 'Salary Collected', header_line_format_num)
#             sheet.set_column(6, 6, 15)
#
#             sheet.write(current_row, 7, 'Salary Paid', header_line_format_num)
#             sheet.set_column(7, 7, 15)
#
#             sheet.autofilter('A1:H1')
#
#             application_sponsor_key1=application_sponsor_key2=[]
#
#             for sponsor_tran in sponsor_trans:
#                 current_row += 1
#                 sheet.write(current_row, 0, get_date_format(sponsor_tran.get('tran_date', '')), normal_line_format_string_nowrap)
#                 sheet.write(current_row, 1, sponsor_tran.get('code', ''), normal_line_format_string_nowrap)
#                 sheet.write(current_row, 2, sponsor_tran.get('sponsor_name', ''), normal_line_format_string_nowrap)
#                 sheet.write(current_row, 3, sponsor_tran.get('action_name', ''), normal_line_format_string_nowrap)
#                 sheet.write(current_row, 4, sponsor_tran.get('sales_man', ''), normal_line_format_string_nowrap)
#                 sheet.write(current_row, 5, sponsor_tran.get('hm_salary', ''), normal_line_format_num_KWD)
#
#                 key1 = key2 = str(sponsor_tran.get('code', '')) + '-' + str(sponsor_tran.get('sponsor_name', ''))
#
#                 index1 = list_of_dict_search(application_sponsor_key1, key1)
#                 index2 = list_of_dict_search(application_sponsor_key2, key2)
#
#                 if index1 == False:
#                     collection_trans = self.get_collection_trans(sponsor_tran.get('application_id', ''), sponsor_tran.get('sponsor_id', ''))
#                     res = {'key': key1}
#                     application_sponsor_key1.append(res)
#                     for collection_tran in collection_trans:
#                         current_row += 1
#                         sheet.write(current_row, 0, get_date_format(collection_tran.get('date', '')),
#                                     normal_line_format_string_nowrap)
#                         sheet.write(current_row, 1, sponsor_tran.get('code', ''), normal_line_format_string_nowrap)
#                         sheet.write(current_row, 2, sponsor_tran.get('sponsor_name', ''), normal_line_format_string_nowrap)
#                         sheet.write(current_row, 3, 'Collection From Sponsor', normal_line_format_string_nowrap)
#                         sheet.write(current_row, 4, collection_tran.get('sales_man', ''), normal_line_format_string_nowrap)
#                         sheet.write(current_row, 6, collection_tran.get('amt', ''), normal_line_format_num_KWD)
#
#
#                 if index2 == False:
#                     paid_trans = self.get_paid_trans(sponsor_tran.get('application_id', ''), sponsor_tran.get('sponsor_id', ''))
#                     res = {'key': key2}
#                     application_sponsor_key2.append(res)
#                     for paid_tran in paid_trans:
#                         current_row += 1
#                         sheet.write(current_row, 0, get_date_format(paid_tran.get('date', '')),
#                                     normal_line_format_string_nowrap)
#                         sheet.write(current_row, 1, sponsor_tran.get('code', ''), normal_line_format_string_nowrap)
#                         sheet.write(current_row, 2, sponsor_tran.get('sponsor_name', ''), normal_line_format_string_nowrap)
#                         sheet.write(current_row, 3, 'Paid To Housemaid', normal_line_format_string_nowrap)
#                         sheet.write(current_row, 4, paid_tran.get('sales_man', ''), normal_line_format_string_nowrap)
#                         sheet.write(current_row, 7, paid_tran.get('amt', ''), normal_line_format_num_KWD)
#
#
#         except Exception as e:
#             logger.exception("Get Report Values Method")
#             raise ValidationError(e)


