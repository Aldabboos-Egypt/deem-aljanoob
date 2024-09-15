from odoo import fields
from datetime import datetime
from odoo import _
from odoo.exceptions import ValidationError
import datetime
import logging
from num2words import num2words

logger = logging.getLogger(__name__)


# =========================================== MAIN FUNCTIONS ============================================================
def _get_default_account_chart(self):
    try:
        account_chart_template = self.env['account.chart.template'].search([], limit=1)
        return account_chart_template
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def _get_currency_id(self):
    try:
        company = self.env['res.company'].search([], limit=1)
        return company.currency_id.id
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def _get_cash_journal(self):
    try:
        journal = self.env['account.journal'].search([('name', '=', 'Cash')], limit=1)
        return journal.id
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def _get_forign_currency_id(self):
    try:
        forign_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        return forign_currency.id
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def _update_account_journal_by_code(self, code, name):
    try:
        journal = self.env['account.journal'].search([('code', '=', code)], limit=1)
        if journal:
            journal.write({'name': name})

        return journal
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def _create_account_journal(self, name, code, type, currency_id):
    try:
        journal = self.env['account.journal'].search([('name', '=', name)], limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': name,
                'code': code,
                'type': type,
                'currency_id': currency_id,
            })
        return journal
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def _generate_account_code(self, internal_type, internal_group):
    try:
        accounts_list = self.env['account.account'].search(
            [('internal_type', '=', internal_type), ('internal_group', '=', internal_group)])
        codes = []
        for account in accounts_list:
            codes.append(int(account.code))
        next_code = max(codes) + 1

        return str(next_code)
    except Exception as e:
        logger.exception("get_next_code method")
        raise ValidationError(e)
def _create_account(self, name, type, internal_type, internal_group, reconcile, currency_id):
    try:
        account = self.env['account.account'].search(
            [('name', '=', name), ('internal_type', '=', internal_type), ('internal_group', '=', internal_group)],
            limit=1)
        if not account:
            code = _generate_account_code(self, internal_type, internal_group)
            user_type_id = self.env['account.account.type'].search([('name', '=', type)], limit=1)
            account = self.env['account.account'].create({
                'name': name,
                'code': code,
                'user_type_id': user_type_id.id,
                'internal_type': internal_type,
                'internal_group': internal_group,
                'reconcile': reconcile,
                'currency_id': currency_id,
            })
        return account
    except Exception as e:
        logger.exception("_create_account")
        raise ValidationError(e)
# =========================================== COMMON FUNCTIONS ==========================================================
def create_journals_for_system(self, currency_id, forign_currency_id):
    try:
        global direct_journal_deferred_income,direct_journal_recognized_income,journal_deliver_reject,journal_reject_after_deliver
        global return_journal_deferred,return_journal_recognized,return_reject_after_testing

        direct_journal_deferred_income = _update_account_journal_by_code(self, 'INV', 'المبيعات المستحقه - خدم الوصول')
        direct_journal_recognized_income = _create_account_journal(self, 'المبيعات المحققه - خدم الوصول', 'SALRC', 'general', currency_id)

        journal_deliver_reject = _create_account_journal(self, 'رفض استلام الخادمه قبل الاستلام', 'SALRJ', 'general',
                                                currency_id)
        journal_reject_after_deliver = _create_account_journal(self, 'رفض استلام الخادمه بعد الاستلام', 'SALRF', 'general',
                                                currency_id)

        return_journal_deferred = _create_account_journal(self, 'المبيعات المستحقه - خدم المرجع', 'SALDF', 'sale', currency_id)
        return_journal_recognized = _create_account_journal(self, 'المبيعات المحققه - خدم المرجع', 'SALRN', 'general', currency_id)

        return_reject_after_testing = _create_account_journal(self, 'الرجوع من الكفيل الثاني', 'SALTS', 'general',
                                                currency_id)

    except Exception as e:
        logger.exception("Error Title")
        raise ValidationError(e)
def create_accounts_for_system(self, currency_id, forign_currency_id):
    try:
        global direct_deferred_income,direct_deferred_purchase,direct_arrival_purchase,direct_recognized_income,direct_discount_expense
        global reject_after_deliver,return_sales_hm_dues,return_pay_extra_loss,direct_sales_returned, direct_purchase_returned
        global return_sales_deferred,return_re_sales_profit_loss,return_sales_unrecognized_profit_loss,direct_recognized_purchase

        direct_deferred_income = _create_account(self, 'المبيعات المستحقه - خدم الوصول', 'Current Liabilities', 'other', 'liability',False, currency_id)
        direct_recognized_income = _create_account(self, 'المبيعات المحققه - خدم الوصول', 'Income','other', 'income',False, currency_id)
        return_sales_deferred = _create_account(self, 'المبيعات المستحقه - خدم المرجع', 'Current Liabilities','other', 'liability',False, currency_id)
        direct_sales_returned = _create_account(self, 'المبيعات المحققه - خدم المرجع', 'Income','other', 'income',False, currency_id)
        direct_deferred_purchase = _create_account(self, 'خدم بالطريق', 'Current Assets', 'other', 'asset', False, forign_currency_id)
        direct_arrival_purchase = _create_account(self, 'خدم الوصول', 'Current Assets','other', 'asset',False, forign_currency_id)
        direct_discount_expense = _create_account(self, 'خصم مسموح - خدم الوصول', 'Expenses','other', 'expense', False, currency_id)
        return_sales_hm_dues = _create_account(self, 'مستحقات الخدم', 'Payable','payable', 'liability',True, currency_id)
        reject_after_deliver = _create_account(self, 'اداره مكتب الخدم المرجع', 'Current Assets','other', 'asset',False, currency_id)
        direct_recognized_purchase = _create_account(self, 'مردوات المبيعات', 'Expenses','other', 'expense',False, currency_id)
        return_pay_extra_loss = _create_account(self, 'أرباح وخسائر - الخدم المرجع من الكفيل الأول', 'Income','other', 'income',False, currency_id)

        direct_purchase_returned = _create_account(self, 'مردوات المشتريات', 'Expenses','other', 'expense',False, currency_id)
        return_sales_unrecognized_profit_loss = _create_account(self, 'أرباح وخسائر - الخدم المسافر الي بلده', 'Income', 'other',
                                            'income', False, currency_id)

        return_re_sales_profit_loss = _create_account(self, 'أرباح وخسائر - أعاده البيع الخدم المرجع', 'Income', 'other',
                                            'income', False, currency_id)

    except Exception as e:
        logger.exception("Error Title")
        raise ValidationError(e)

def update_housemaid_settings(self):
    try:
        global direct_journal_arrival_cash, direct_journal_deferred_income, direct_accounts_receivable
        global direct_deferred_income, direct_deferred_purchase, direct_arrival_purchase
        global direct_journal_recognized_income, direct_recognized_income, direct_discount_expense
        global direct_recognized_purchase, journal_deliver_reject, deliver_reject
        global return_journal_cash, journal_reject_after_deliver, reject_after_deliver
        global return_sales_hm_dues, return_hm_dues_contact, return_pay_extra_loss
        global direct_sales_returned, direct_purchase_returned, return_sales_unrecognized_profit_loss
        global return_journal_deferred, return_journal_recognized, return_reject_after_testing
        global return_accounts_receivable, return_sales_deferred, return_sales_recognized
        global return_recognized_purchase, return_re_sales_profit_loss


        config = self.env['res.config.settings'].search([], limit=1)

        config.direct_journal_arrival_cash = direct_journal_arrival_cash
        config.direct_journal_deferred_income = direct_journal_deferred_income
        config.direct_accounts_receivable = direct_accounts_receivable
        config.direct_deferred_income = direct_deferred_income
        config.direct_deferred_purchase = direct_deferred_purchase
        config.direct_arrival_purchase = direct_arrival_purchase
        config.direct_journal_recognized_income = direct_journal_recognized_income
        config.direct_recognized_income = direct_recognized_income
        config.direct_discount_expense = direct_discount_expense
        config.direct_recognized_purchase = direct_recognized_purchase
        config.journal_deliver_reject = journal_deliver_reject
        config.deliver_reject = deliver_reject
        config.return_journal_cash = return_journal_cash
        config.journal_reject_after_deliver = journal_reject_after_deliver
        config.reject_after_deliver = reject_after_deliver
        config.return_sales_hm_dues = return_sales_hm_dues
        config.return_hm_dues_contact = return_hm_dues_contact
        config.return_pay_extra_loss = return_pay_extra_loss
        config.direct_sales_returned = direct_sales_returned
        config.direct_purchase_returned = direct_purchase_returned
        config.return_sales_unrecognized_profit_loss = return_sales_unrecognized_profit_loss
        config.return_journal_deferred = return_journal_deferred
        config.return_journal_recognized = return_journal_recognized
        config.return_reject_after_testing = return_reject_after_testing
        config.return_accounts_receivable = return_accounts_receivable
        config.return_sales_deferred = return_sales_deferred
        config.return_sales_recognized = return_sales_recognized
        config.return_recognized_purchase = return_recognized_purchase
        config.return_re_sales_profit_loss = return_re_sales_profit_loss

        config.set_values()

        return config
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
def main_setup(self):
    try:

        global direct_journal_arrival_cash, direct_journal_deferred_income, direct_accounts_receivable
        global direct_deferred_income, direct_deferred_purchase, direct_arrival_purchase
        global direct_journal_recognized_income, direct_recognized_income, direct_discount_expense
        global direct_recognized_purchase, journal_deliver_reject, deliver_reject
        global return_journal_cash, journal_reject_after_deliver, reject_after_deliver
        global return_sales_hm_dues, return_hm_dues_contact, return_pay_extra_loss
        global direct_sales_returned, direct_purchase_returned, return_sales_unrecognized_profit_loss
        global return_journal_deferred, return_journal_recognized, return_reject_after_testing
        global return_accounts_receivable, return_sales_deferred, return_sales_recognized
        global return_recognized_purchase, return_re_sales_profit_loss

        direct_recognized_purchase = deliver_reject = return_recognized_purchase = None

        account_chart_template = _get_default_account_chart(self)
        direct_journal_arrival_cash = _get_cash_journal(self)
        return_journal_cash = _get_cash_journal(self)
        direct_accounts_receivable = account_chart_template.property_account_receivable_id.id
        return_accounts_receivable = account_chart_template.property_account_receivable_id.id

        # return_hm_dues_contact = _create_housemaid_contact_payable(self)
        return_hm_dues_contact = None

        return_sales_recognized = None
        direct_sales_returned = None

        currency_id = _get_currency_id(self)
        forign_currency_id = _get_forign_currency_id(self)

        create_journals_for_system(self, currency_id, forign_currency_id)
        create_accounts_for_system(self, currency_id, forign_currency_id)

        update_housemaid_settings(self)








    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
