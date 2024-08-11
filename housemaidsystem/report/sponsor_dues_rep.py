from odoo import models, api
import datetime
import logging
from odoo.exceptions import ValidationError
logger = logging.getLogger(__name__)


class SponsorDuesRep(models.AbstractModel):
    _name = "report.housemaidsystem.sponsor_dues_rep"
    _description = "Sponsor Dues Report"

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
                        and a.old_customer_id = c.id
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
                        account_move_line a, res_users b, res_partner c, account_move_line d, account_account e
                    WHERE 
                        a.create_uid = b.id 
                        and b.partner_id = c.id 
                        and a.account_id = 201
                        and COALESCE(a.credit, 0.0) > 0
                        and a.move_id = d.move_id
                        and d.account_id = e.id
                        and e.internal_type = 'liquidity'
                        and a.account_id = %i 
                        and a.partner_id = %i
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
                           account_move_line a, res_users b, res_partner c, account_move_line d, account_account e
                       WHERE 
                           a.create_uid = b.id 
                           and b.partner_id = c.id 
                           and COALESCE(a.credit, 0.0) > 0
                           and a.move_id = d.move_id
                           and d.account_id = e.id
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
                        account_move_line a, res_users b, res_partner c, account_move_line d, account_account e
                    WHERE 
                        a.create_uid = b.id 
                        and b.partner_id = c.id 
                        and a.account_id = 201
                        and COALESCE(a.debit, 0.0) > 0
                        and a.move_id = d.move_id
                        and d.account_id = e.id
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

    @api.model
    def _get_report_values(self, docids, data=None):
        try:
            docs = []
            if data['action_type'] == 'all' or data['action_type'] == 'returnbackfromfirstsposnor':
                res = {
                    'id': 'returnbackfromfirstsposnor',
                    'name': 'Return Back From First Sponsor',
                    'from_date': data['from_date'],
                    'to_date': data['to_date'],
                    'application_id': data['application_id'],
                    'report_scope': data['report_scope'],
                }
                docs.append(res)
            if data['action_type'] == 'all' or data['action_type'] == 'sellastest':
                res = {
                    'id': 'sellastest',
                    'name': 'Sell As Test',
                    'from_date': data['from_date'],
                    'to_date': data['to_date'],
                    'application_id': data['application_id'],
                    'report_scope': data['report_scope'],
                }
                docs.append(res)
            if data['action_type'] == 'all' or data['action_type'] == 'returnbackfromlastsposnor':
                res = {
                    'id': 'returnbackfromlastsposnor',
                    'name': 'Return Back From Last Sponsor',
                    'from_date': data['from_date'],
                    'to_date': data['to_date'],
                    'application_id': data['application_id'],
                    'report_scope': data['report_scope'],
                }
                docs.append(res)



            report_title = "(From Date: " + data['from_date'] + " To Date: " + data['to_date'] + ")"


            docargs = {
                'doc_ids': docids,
                'doc_model': 'account.move.line',
                'docs': docs,
                'from_date':data['from_date'],
                'to_date': data['to_date'],
                'title': report_title,
                'get_returnbackfromfirstsposnor_trans': self.get_returnbackfromfirstsposnor_trans,
                'get_sellastest_trans': self.get_sellastest_trans,
                'get_returnbackfromlastsposnor_trans': self.get_returnbackfromlastsposnor_trans,
                'get_collection_trans': self.get_collection_trans,
                'get_paid_trans': self.get_paid_trans,
            }
            return docargs
        except Exception as e:
            logger.exception("Get Report Values Method")
            raise ValidationError(e)






