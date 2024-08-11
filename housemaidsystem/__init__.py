# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import report
from . import wizard
# from . import data_migration

from odoo import SUPERUSER_ID, api
from datetime import datetime
from odoo import _
from odoo.exceptions import ValidationError
import datetime
import logging
from num2words import num2words

logger = logging.getLogger(__name__)


# =========================================== MAIN FUNCTIONS ============================================================
def _get_default_account_chart(env):
    try:
        account_chart_template = env['account.chart.template'].search([], limit=1)
        return account_chart_template
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)


def _get_currency_id(env):
    try:
        company = env['res.company'].search([], limit=1)
        return company.currency_id.id
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)


def _get_cash_journal(env):
    try:
        journal = env['account.journal'].search([('name', '=', 'Cash')], limit=1)
        return journal.id
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)


def _get_forign_currency_id(env):
    try:
        forign_currency = env['res.currency'].search([('name', '=', 'USD')], limit=1)
        return forign_currency.id
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)


def _update_account_journal_by_code(env, code, name):
    try:
        journal = env['account.journal'].search([('code', '=', code)], limit=1)
        if journal:
            journal.write({'name': name})

        return journal
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)


def _create_account_journal(env, name, code, type, currency_id):
    try:
        journal = env['account.journal'].search([('name', '=', name)], limit=1)
        if not journal:
            journal = env['account.journal'].create({
                'name': name,
                'code': code,
                'type': type,
                'currency_id': currency_id,
            })
        return journal
    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)


def _generate_account_code(env, internal_type, internal_group):
    try:
        accounts_list = env['account.account'].search(
            [('internal_type', '=', internal_type), ('internal_group', '=', internal_group)])
        codes = []
        for account in accounts_list:
            codes.append(int(account.code))

        next_code = max(codes) + 1

        return str(next_code)
    except Exception as e:
        logger.exception("get_next_code method")
        raise ValidationError(e)


def _create_account(env, name, type, internal_type, internal_group, reconcile, currency_id):
    try:
        account = env['account.account'].search(
            [('name', '=', name), ('internal_type', '=', internal_type), ('internal_group', '=', internal_group)],
            limit=1)
        if not account:
            code = _generate_account_code(env, internal_type, internal_group)
            user_type_id = env['account.account.type'].search([('name', '=', type)], limit=1)
            account = env['account.account'].create({
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
def create_journals_for_system(env, currency_id, forign_currency_id):
    try:
        global direct_journal_deferred_income, direct_journal_recognized_income, journal_deliver_reject, journal_reject_after_deliver
        global return_journal_deferred, return_journal_recognized, return_reject_after_testing

        direct_journal_deferred_income = _update_account_journal_by_code(env, 'INV', 'المبيعات المستحقه - خدم الوصول')
        direct_journal_recognized_income = _create_account_journal(env, 'المبيعات المحققه - خدم الوصول', 'SALRC',
                                                                   'general', currency_id)

        journal_deliver_reject = _create_account_journal(env, 'رفض استلام الخادمه قبل الاستلام', 'SALRJ', 'general',
                                                         currency_id)
        journal_reject_after_deliver = _create_account_journal(env, 'رفض استلام الخادمه بعد الاستلام', 'SALRF',
                                                               'general',
                                                               currency_id)

        return_journal_deferred = _create_account_journal(env, 'المبيعات المستحقه - خدم المرجع', 'SALDF', 'sale',
                                                          currency_id)
        return_journal_recognized = _create_account_journal(env, 'المبيعات المحققه - خدم المرجع', 'SALRN', 'general',
                                                            currency_id)

        return_reject_after_testing = _create_account_journal(env, 'الرجوع من الكفيل الثاني', 'SALTS', 'general',
                                                              currency_id)

    except Exception as e:
        logger.exception("Error Title")
        raise ValidationError(e)


def create_accounts_for_system(env, currency_id, forign_currency_id):
    try:
        global direct_deferred_income, direct_deferred_purchase, direct_arrival_purchase, direct_recognized_income, direct_discount_expense
        global reject_after_deliver, return_sales_hm_dues, return_pay_extra_loss, direct_sales_returned, direct_purchase_returned, return_sales_recognized
        global return_sales_deferred, return_re_sales_profit_loss, return_sales_unrecognized_profit_loss, direct_recognized_purchase

        direct_deferred_income = _create_account(env, 'المبيعات المستحقه - خدم الوصول', 'Current Liabilities', 'other',
                                                 'liability', False, currency_id)
        return_sales_deferred = _create_account(env, 'المبيعات المستحقه - خدم المرجع', 'Current Liabilities', 'other',
                                                'liability', False, currency_id)

        direct_recognized_income = _create_account(env, 'المبيعات المحققه - خدم الوصول', 'Income', 'other', 'income',
                                                   False, currency_id)
        direct_sales_returned = return_sales_recognized = _create_account(env, 'المبيعات المحققه - خدم المرجع',
                                                                          'Income', 'other', 'income', False,
                                                                          currency_id)

        direct_deferred_purchase = _create_account(env, 'خدم بالطريق', 'Current Assets', 'other', 'asset', False,
                                                   forign_currency_id)
        direct_arrival_purchase = _create_account(env, 'خدم الوصول', 'Current Assets', 'other', 'asset', False,
                                                  forign_currency_id)

        direct_discount_expense = _create_account(env, 'خصم مسموح - خدم الوصول', 'Expenses', 'other', 'expense', False,
                                                  currency_id)
        return_sales_hm_dues = _create_account(env, 'مستحقات الخدم', 'Payable', 'payable', 'liability', True,
                                               currency_id)
        reject_after_deliver = _create_account(env, 'اداره مكتب الخدم المرجع', 'Current Assets', 'other', 'asset',
                                               False, currency_id)

        direct_recognized_purchase = _create_account(env, 'مردوات المبيعات', 'Income', 'other', 'income', False,
                                                     currency_id)
        direct_purchase_returned = _create_account(env, 'مردوات المشتريات', 'Expenses', 'other', 'expense', False,
                                                   currency_id)

        return_pay_extra_loss = _create_account(env, 'أرباح وخسائر - الخدم المرجع من الكفيل الأول', 'Income', 'other',
                                                'income', False, currency_id)
        return_re_sales_profit_loss = _create_account(env, 'أرباح وخسائر - أعاده البيع الخدم المرجع', 'Income', 'other',
                                                      'income', False, currency_id)
        return_sales_unrecognized_profit_loss = _create_account(env, 'أرباح وخسائر - الخدم المسافر الي بلده', 'Income',
                                                                'other', 'income', False, currency_id)

    except Exception as e:
        logger.exception("create_accounts_for_system")
        raise ValidationError(e)


def create_housemaid_contact_payable(env, property_account_payable_id, property_account_receivable_id):
    try:
        contact = env['res.partner'].search([('name', '=', 'مستحقات الخدم')], limit=1)
        if not contact:
            contact = env['res.partner'].create({
                'name': 'مستحقات الخدم',
                'type': 'contact',
                'active': True,
                'sponsor_gender': 'female',
                'is_company': True,
                'property_account_payable_id': property_account_payable_id,
                'property_account_receivable_id': property_account_receivable_id,
            })
        return contact.id
    except Exception as e:
        logger.exception("Error Title")
        raise ValidationError(e)


def update_account_receivalble(env, direct_accounts_receivable):
    try:
        account = env['account.account'].search([('id', '=', direct_accounts_receivable)], limit=1)
        if account:
            account.write({'name': 'العملاء'})
    except Exception as e:
        logger.exception("update_account_receivalble")
        raise ValidationError(e)


def update_account_purchase(env, return_recognized_purchase):
    try:
        account = env['account.account'].search([('id', '=', return_recognized_purchase)], limit=1)
        if account:
            account.write({'name': 'مشتريات الخدم'})
    except Exception as e:
        logger.exception("update_account_purchase")
        raise ValidationError(e)


def update_housemaid_settings(env):
    try:
        global passport_expiry_years
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

        config = env['res.config.settings'].search([], limit=1)

        config.passport_expiry_years = passport_expiry_years
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


# =========================================== COMMON FUNCTIONS ==========================================================
def _setup_main_configuration(cr, registry):
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        global passport_expiry_years
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

        deliver_reject = None

        passport_expiry_years = 0
        account_chart_template = _get_default_account_chart(env)
        direct_journal_arrival_cash = _get_cash_journal(env)
        return_journal_cash = _get_cash_journal(env)
        direct_accounts_receivable = account_chart_template.property_account_receivable_id.id
        return_accounts_receivable = account_chart_template.property_account_receivable_id.id
        return_recognized_purchase = account_chart_template.property_account_expense_categ_id.id
        return_recognized_purchase = account_chart_template.property_account_expense_categ_id.id

        currency_id = _get_currency_id(env)
        forign_currency_id = _get_forign_currency_id(env)

        create_journals_for_system(env, currency_id, forign_currency_id)
        create_accounts_for_system(env, currency_id, forign_currency_id)

        update_account_receivalble(env, direct_accounts_receivable)
        update_account_purchase(env, return_recognized_purchase)

        property_account_payable_id = return_sales_hm_dues
        property_account_receivable_id = account_chart_template.property_account_receivable_id.id
        return_hm_dues_contact = create_housemaid_contact_payable(env, property_account_payable_id,
                                                                  property_account_receivable_id)

        update_housemaid_settings(env)


    except Exception as e:
        logger.exception("create_account_journal")
        raise ValidationError(e)
