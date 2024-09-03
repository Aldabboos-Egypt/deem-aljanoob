# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging
from odoo.exceptions import ValidationError
from . import post_instllations

logger = logging.getLogger(__name__)


class HousemaidMainConfiguration(models.Model):
    _name = 'housemaidsystem.configuration.settings'

    # Applications Validations
    passport_expiry_years = fields.Integer(string="Number of expiry years validations", default=0)
    branch_office_required = fields.Boolean(string="Branch Required", default=False)

    # whatsapp services
    whatsapp_service_status = fields.Boolean(string="Allow Whatsapp Services", default=False)
    whatsapp_endpoint = fields.Char(string="Whatsapp Service Endpoint", default='')
    whatsapp_token = fields.Char(string="Whatsapp Service token", default='')

    # ٍ Reservation Screen
    direct_journal_arrival_cash = fields.Many2one('account.journal', domain=[('type', 'in', ['cash','bank'])])
    direct_journal_deferred_income = fields.Many2one('account.journal', domain=[('type', '=', 'sale')])
    direct_accounts_receivable = fields.Many2one('account.account', domain=[('internal_type', '=', 'general')])
    direct_deferred_income = fields.Many2one('account.account')
    direct_deferred_purchase = fields.Many2one('account.account', domain=[('internal_group', '=', 'asset')])

    # Arrival Screen
    direct_arrival_purchase = fields.Many2one('account.account', domain=[('internal_group', '=', 'asset')])

    # Deliver to First Sponsor Screen
    direct_journal_recognized_income = fields.Many2one('account.journal', domain=[('type', '=', 'general')])
    direct_recognized_income = fields.Many2one('account.account')
    direct_discount_expense = fields.Many2one('account.account', domain=[('internal_group', '=', 'expense')])
    direct_recognized_purchase = fields.Many2one('account.account', domain=[('internal_group', '=', 'expense')])

    # Re-Sell Screen
    journal_deliver_reject = fields.Many2one('account.journal', domain=[('type', '=', 'general')])
    deliver_reject = fields.Many2one('account.account', domain=[('internal_group', '=', 'asset')])

    # Return Back From First Sponsor Screen
    return_journal_cash = fields.Many2one('account.journal', domain=[('type', 'in', ['cash','bank'])])
    journal_reject_after_deliver = fields.Many2one('account.journal', domain=[('type', '=', 'general')])
    reject_after_deliver = fields.Many2one('account.account', domain=[('internal_group', '=', 'asset')])
    return_sales_hm_dues = fields.Many2one('account.account', domain=[('internal_group', '=', 'liability')])
    return_hm_dues_contact = fields.Many2one('res.partner')
    return_pay_extra_loss = fields.Many2one('account.account', domain=[('internal_group', '=', 'income')])

    # Back To Country
    direct_sales_returned = fields.Many2one('account.account', domain=[('internal_group', '=', 'income')])
    direct_purchase_returned = fields.Many2one('account.account', domain=[('internal_group', '=', 'expense')])
    return_sales_unrecognized_profit_loss = fields.Many2one('account.account',
                                                            domain=[('internal_group', '=', 'income')])

    # Return Sales
    return_journal_deferred = fields.Many2one('account.journal', domain=[('type', '=', 'sale')])
    return_journal_recognized = fields.Many2one('account.journal', domain=[('type', '=', 'general')])
    return_reject_after_testing = fields.Many2one('account.journal', domain=[('type', '=', 'general')])
    return_accounts_receivable = fields.Many2one('account.account', domain=[('internal_type', '=', 'receivable')])
    return_sales_deferred = fields.Many2one('account.account', domain=[('internal_group', '=', 'liability')])
    return_sales_recognized = fields.Many2one('account.account', domain=[('internal_group', '=', 'income')])
    return_recognized_purchase = fields.Many2one('account.account', domain=[('internal_group', '=', 'expense')])
    return_re_sales_profit_loss = fields.Many2one('account.account',
                                                  domain=[('internal_group', '=', 'income')])


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Applications Validations
    passport_expiry_years = fields.Integer(string="Number of expiry years validations", )
    branch_office_required = fields.Boolean(string="Branch Required", default=False)

    # whatsapp services
    whatsapp_service_status = fields.Boolean(string="Allow Whatsapp Services", default=False)
    whatsapp_endpoint = fields.Char(string="Whatsapp Service Endpoint", default='')
    whatsapp_token = fields.Char(string="Whatsapp Service token", default='')

    # Sales
    direct_journal_deferred_income = fields.Many2one('account.journal', 'Deferred Income Journal', reqired='True',
                                                     help='Default Journal for posting sales deferred income transactions.')
    direct_journal_recognized_income = fields.Many2one('account.journal', 'Recognized Income Journal', reqired='True',
                                                       help='Default Journal for posting recognized income transactions.')
    direct_accounts_receivable = fields.Many2one('account.account', 'Receivable Account', reqired='True',
                                                 help='Default account for un-paid payments for sales transactions')
    direct_deferred_income = fields.Many2one('account.account', 'Deferred Income Account', reqired='True',
                                             help='Default account for sales transactions (Deferred)')
    direct_recognized_income = fields.Many2one('account.account', 'Recognized Income Account', reqired='True',
                                               help='Default account for sales transactions (Recognized)')
    direct_discount_expense = fields.Many2one('account.account', 'Sales Discount Expense Account', reqired='True',
                                              help='Default account for sales discount transactions (Recognized)')
    direct_journal_arrival_cash = fields.Many2one('account.journal', 'Sales Cash Journal', reqired='True',
                                                  help='Default Journal for sales transactions')
    direct_sales_returned = fields.Many2one('account.account', 'Sales Returned', reqired='True',
                                            help='Default Account for sales returned')

    # purchase
    direct_deferred_purchase = fields.Many2one('account.account', 'Deferred Purchase Account (Assets)', reqired='True',
                                               help='Default account for purchase transactions (Deferred)')
    direct_arrival_purchase = fields.Many2one('account.account', 'Arrival Purchase Account (Assets)', reqired='True',
                                              help='Default account for purchase transactions (Arrival)')
    direct_recognized_purchase = fields.Many2one('account.account', 'Recognized Purchase Account (Expense)',
                                                 reqired='True',
                                                 help='Default account for purchase transactions (Recognized)')
    direct_purchase_returned = fields.Many2one('account.account', 'Purchase Returned (Expense)',
                                               help='Default account for purchase returned')

    # Deliver Reject
    journal_deliver_reject = fields.Many2one('account.journal', 'Deliver Reject Journal', reqired='True',
                                             help='Default Journal for deliver reject for first sponsor transactions.')
    deliver_reject = fields.Many2one('account.account', 'Deliver Reject Expense Account', reqired='True',
                                     help='Default account for deliver reject transactions.')

    # Reject after deliver
    journal_reject_after_deliver = fields.Many2one('account.journal', 'Reject After Deliver Journal', reqired='True',
                                                   help='Default Journal for reject after deliver by first sponsor transactions.')
    reject_after_deliver = fields.Many2one('account.account', 'Reject after deliver Expense Account', reqired='True',
                                           help='Default account for reject after deliver transactions.')

    # Sales Return
    return_journal_deferred = fields.Many2one('account.journal', 'Sales Return Posting Journal', reqired='True',
                                              help='Default Journal for posting sales return transactions (Deferred)')
    return_journal_recognized = fields.Many2one('account.journal', 'Sales Return Posting Journal (Recognized)',
                                                reqired='True',
                                                help='Default Journal for posting sales return transactions.')

    return_accounts_receivable = fields.Many2one('account.account', 'Sales Return Accounts Receivable',
                                                 reqired='True', help='Default account for un-paid payments '
                                                                      'for sales return transactions')

    return_sales_deferred = fields.Many2one('account.account', 'Sales Return (Deferred)',
                                            reqired='True', help='Default account for sales return transactions')
    return_sales_recognized = fields.Many2one('account.account', 'Sales Return (Recognized)',
                                              reqired='True', help='Default account for sales return transactions')
    return_sales_hm_dues = fields.Many2one('account.account', 'Housemaid Dues',
                                           reqired='True',
                                           help='Default payable account for sales return transactions of housemaid salary')
    return_hm_dues_contact = fields.Many2one('res.partner', 'Housemaid Dues',
                                             reqired='True',
                                             help='Default contact person for housemaid dues')
    return_pay_extra_loss = fields.Many2one('account.account', 'Return back - Pay extra or less to sponsor',
                                            reqired='True',
                                            help='Default income account to register the payment from or to sponsor')
    return_journal_cash = fields.Many2one('account.journal', 'Sales Return Careturn_reject_after_testingsh Journal',
                                          reqired='True',
                                          help='Default Journal for sales return transactions')
    return_recognized_purchase = fields.Many2one('account.account', 'Recognized Return Purchase Account (Expense)',
                                                 reqired='True',
                                                 help='Default account for return purchase transactions (Recognized)')
    return_reject_after_testing = fields.Many2one('account.journal', 'Reject after testing',
                                                  reqired='True',
                                                  help='Default account for reject after testing')
    return_sales_unrecognized_profit_loss = fields.Many2one('account.account', 'Un-Recognized Profit\Losss '
                                                                               'from Sales Retun of Back to country (Expense)',
                                                            reqired='True',
                                                            help='Default account for Profit\Losss from Sales Retun of Back to country (Un-Recognized)')
    return_re_sales_profit_loss = fields.Many2one('account.account', 'Sell As Test Profit\Losss '
                                                                     'from Sales Retun Re-Sell (Expense)',
                                                  reqired='True',
                                                  help='Default account for Profit\Losss from Sales As test (Un-Recognized)')

    @api.model
    def get_values(self):
        try:
            res = super(ResConfigSettings, self).get_values()
            IrDefault = self.env['ir.default'].sudo()

            # Applications Validations
            default_passport_expiry_years = IrDefault.get('housemaidsystem.configuration.settings',
                                                          "passport_expiry_years")
            default_branch_office_required = IrDefault.get('housemaidsystem.configuration.settings',
                                                           "branch_office_required")

            # whatsapp services
            default_whatsapp_service_status = IrDefault.get('housemaidsystem.configuration.settings',
                                                            "whatsapp_service_status")
            default_whatsapp_endpoint = IrDefault.get('housemaidsystem.configuration.settings',
                                                      "whatsapp_endpoint")
            default_whatsapp_token = IrDefault.get('housemaidsystem.configuration.settings',
                                                   "whatsapp_token")

            # Sales
            default_direct_journal_deferred_income = IrDefault.get('housemaidsystem.configuration.settings',
                                                                   "direct_journal_deferred_income")
            default_direct_journal_recognized_income = IrDefault.get('housemaidsystem.configuration.settings',
                                                                     "direct_journal_recognized_income")
            default_direct_accounts_receivable = IrDefault.get('housemaidsystem.configuration.settings',
                                                               "direct_accounts_receivable")
            default_direct_deferred_income = IrDefault.get('housemaidsystem.configuration.settings',
                                                           "direct_deferred_income")
            default_direct_recognized_income = IrDefault.get('housemaidsystem.configuration.settings',
                                                             "direct_recognized_income")
            default_direct_discount_expense = IrDefault.get('housemaidsystem.configuration.settings',
                                                            "direct_discount_expense")
            default_direct_journal_arrival_cash = IrDefault.get('housemaidsystem.configuration.settings',
                                                                "direct_journal_arrival_cash")
            default_direct_sales_returned = IrDefault.get('housemaidsystem.configuration.settings',
                                                          "direct_sales_returned")

            # purchase
            default_direct_deferred_purchase = IrDefault.get('housemaidsystem.configuration.settings',
                                                             "direct_deferred_purchase")
            default_direct_arrival_purchase = IrDefault.get('housemaidsystem.configuration.settings',
                                                            "direct_arrival_purchase")
            default_direct_recognized_purchase = IrDefault.get('housemaidsystem.configuration.settings',
                                                               "direct_recognized_purchase")
            default_direct_purchase_returned = IrDefault.get('housemaidsystem.configuration.settings',
                                                             "direct_purchase_returned")

            # Deliver Reject
            default_journal_deliver_reject = IrDefault.get('housemaidsystem.configuration.settings',
                                                           "journal_deliver_reject")
            default_deliver_reject = IrDefault.get('housemaidsystem.configuration.settings',
                                                   "deliver_reject")

            # Reject after deliver
            default_journal_reject_after_deliver = IrDefault.get('housemaidsystem.configuration.settings',
                                                                 "journal_reject_after_deliver")
            default_reject_after_deliver = IrDefault.get('housemaidsystem.configuration.settings',
                                                         "reject_after_deliver")

            # Return
            default_return_journal_deferred = IrDefault.get('housemaidsystem.configuration.settings',
                                                            "return_journal_deferred")
            default_return_journal_recognized = IrDefault.get('housemaidsystem.configuration.settings',
                                                              "return_journal_recognized")
            default_return_accounts_receivable = IrDefault.get('housemaidsystem.configuration.settings',
                                                               "return_accounts_receivable")
            default_return_sales_deferred = IrDefault.get('housemaidsystem.configuration.settings',
                                                          "return_sales_deferred")
            default_return_sales_recognized = IrDefault.get('housemaidsystem.configuration.settings',
                                                            "return_sales_recognized")
            default_return_sales_hm_dues = IrDefault.get('housemaidsystem.configuration.settings',
                                                         "return_sales_hm_dues")
            default_return_hm_dues_contact = IrDefault.get('housemaidsystem.configuration.settings',
                                                           "return_hm_dues_contact")

            default_return_pay_extra_loss = IrDefault.get('housemaidsystem.configuration.settings',
                                                          "return_pay_extra_loss")
            default_return_journal_cash = IrDefault.get('housemaidsystem.configuration.settings',
                                                        "return_journal_cash")
            default_return_recognized_purchase = IrDefault.get('housemaidsystem.configuration.settings',
                                                               "return_recognized_purchase")
            default_return_reject_after_testing = IrDefault.get('housemaidsystem.configuration.settings',
                                                                "return_reject_after_testing")
            default_return_sales_unrecognized_profit_loss = IrDefault.get('housemaidsystem.configuration.settings',
                                                                          "return_sales_unrecognized_profit_loss")
            default_return_re_sales_profit_loss = IrDefault.get('housemaidsystem.configuration.settings',
                                                                "return_re_sales_profit_loss")

            res.update(

                passport_expiry_years=default_passport_expiry_years if default_passport_expiry_years else False,
                branch_office_required=default_branch_office_required if default_branch_office_required else False,

                whatsapp_service_status=default_whatsapp_service_status if default_whatsapp_service_status else False,
                whatsapp_endpoint=default_whatsapp_endpoint if default_whatsapp_endpoint else False,
                whatsapp_token=default_whatsapp_token if default_whatsapp_token else False,

                direct_journal_deferred_income=default_direct_journal_deferred_income if default_direct_journal_deferred_income else False,
                direct_journal_recognized_income=default_direct_journal_recognized_income if default_direct_journal_recognized_income else False,
                direct_accounts_receivable=default_direct_accounts_receivable if default_direct_accounts_receivable else False,
                direct_deferred_income=default_direct_deferred_income if default_direct_deferred_income else False,
                direct_recognized_income=default_direct_recognized_income if default_direct_recognized_income else False,
                direct_sales_returned=default_direct_sales_returned if default_direct_sales_returned else False,

                direct_deferred_purchase=default_direct_deferred_purchase if default_direct_deferred_purchase else False,
                direct_arrival_purchase=default_direct_arrival_purchase if default_direct_arrival_purchase else False,
                direct_recognized_purchase=default_direct_recognized_purchase if default_direct_recognized_purchase else False,
                direct_purchase_returned=default_direct_purchase_returned if default_direct_purchase_returned else False,

                direct_discount_expense=default_direct_discount_expense if default_direct_discount_expense else False,
                direct_journal_arrival_cash=default_direct_journal_arrival_cash if default_direct_journal_arrival_cash else False,

                journal_deliver_reject=default_journal_deliver_reject if default_journal_deliver_reject else False,
                deliver_reject=default_deliver_reject if default_deliver_reject else False,

                journal_reject_after_deliver=default_journal_reject_after_deliver if default_journal_reject_after_deliver else False,
                reject_after_deliver=default_reject_after_deliver if default_reject_after_deliver else False,

                return_journal_deferred=default_return_journal_deferred if default_return_journal_deferred else False,
                return_journal_recognized=default_return_journal_recognized if default_return_journal_recognized else False,
                return_accounts_receivable=default_return_accounts_receivable if default_return_accounts_receivable else False,
                return_sales_deferred=default_return_sales_deferred if default_return_sales_deferred else False,
                return_sales_recognized=default_return_sales_recognized if default_return_sales_recognized else False,
                return_sales_hm_dues=default_return_sales_hm_dues if default_return_sales_hm_dues else False,
                return_hm_dues_contact=default_return_hm_dues_contact if default_return_hm_dues_contact else False,
                return_pay_extra_loss=default_return_pay_extra_loss if default_return_pay_extra_loss else False,

                return_journal_cash=default_return_journal_cash if default_return_journal_cash else False,
                return_recognized_purchase=default_return_recognized_purchase if default_return_recognized_purchase else False,
                return_reject_after_testing=default_return_reject_after_testing if default_return_reject_after_testing else False,
                return_sales_unrecognized_profit_loss=default_return_sales_unrecognized_profit_loss
                if default_return_sales_unrecognized_profit_loss else False,
                return_re_sales_profit_loss=default_return_re_sales_profit_loss
                if default_return_re_sales_profit_loss else False,

            )
            return res

        except Exception as e:
            logger.exception("Get Values Method")
            raise ValidationError(e)

    def set_values(self):
        try:
            super(ResConfigSettings, self).set_values()
            IrDefault = self.env['ir.default'].sudo()

            # Applications Validations
            IrDefault.set('housemaidsystem.configuration.settings', "passport_expiry_years",
                          self.passport_expiry_years)
            IrDefault.set('housemaidsystem.configuration.settings', "branch_office_required",
                          self.branch_office_required)

            # whatsapp services
            IrDefault.set('housemaidsystem.configuration.settings', "whatsapp_service_status",
                          self.whatsapp_service_status)
            IrDefault.set('housemaidsystem.configuration.settings', "whatsapp_endpoint",
                          self.whatsapp_endpoint)
            IrDefault.set('housemaidsystem.configuration.settings', "whatsapp_token",
                          self.whatsapp_token)

            # Sales
            IrDefault.set('housemaidsystem.configuration.settings', "direct_journal_deferred_income",
                          self.direct_journal_deferred_income.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_journal_recognized_income",
                          self.direct_journal_recognized_income.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_accounts_receivable",
                          self.direct_accounts_receivable.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_deferred_income",
                          self.direct_deferred_income.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_recognized_income",
                          self.direct_recognized_income.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_discount_expense",
                          self.direct_discount_expense.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_journal_arrival_cash",
                          self.direct_journal_arrival_cash.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_sales_returned",
                          self.direct_sales_returned.id)

            # purchase (First Sponsor)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_deferred_purchase",
                          self.direct_deferred_purchase.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_arrival_purchase",
                          self.direct_arrival_purchase.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_recognized_purchase",
                          self.direct_recognized_purchase.id)
            IrDefault.set('housemaidsystem.configuration.settings', "direct_purchase_returned",
                          self.direct_purchase_returned.id)

            # Deliver Reject
            IrDefault.set('housemaidsystem.configuration.settings', "journal_deliver_reject",
                          self.journal_deliver_reject.id)
            IrDefault.set('housemaidsystem.configuration.settings', "deliver_reject",
                          self.deliver_reject.id)

            # Reject after deliver
            IrDefault.set('housemaidsystem.configuration.settings', "journal_reject_after_deliver",
                          self.journal_reject_after_deliver.id)
            IrDefault.set('housemaidsystem.configuration.settings', "reject_after_deliver",
                          self.reject_after_deliver.id)

            # Sales Return
            IrDefault.set('housemaidsystem.configuration.settings', "return_journal_deferred",
                          self.return_journal_deferred.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_journal_recognized",
                          self.return_journal_recognized.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_accounts_receivable",
                          self.return_accounts_receivable.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_sales_deferred",
                          self.return_sales_deferred.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_sales_recognized",
                          self.return_sales_recognized.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_sales_hm_dues",
                          self.return_sales_hm_dues.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_hm_dues_contact",
                          self.return_hm_dues_contact.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_pay_extra_loss",
                          self.return_pay_extra_loss.id)

            IrDefault.set('housemaidsystem.configuration.settings', "return_journal_cash",
                          self.return_journal_cash.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_recognized_purchase",
                          self.return_recognized_purchase.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_reject_after_testing",
                          self.return_reject_after_testing.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_sales_unrecognized_profit_loss",
                          self.return_sales_unrecognized_profit_loss.id)
            IrDefault.set('housemaidsystem.configuration.settings', "return_re_sales_profit_loss",
                          self.return_re_sales_profit_loss.id)

            self._cr.execute('Delete from housemaidsystem_configuration_settings')
            housemaid_main_configuration = self.env['housemaidsystem.configuration.settings'].sudo()

            data = {
                "passport_expiry_years": self.passport_expiry_years,
                "branch_office_required": self.branch_office_required,

                "whatsapp_service_status": self.whatsapp_service_status,
                "whatsapp_endpoint": self.whatsapp_endpoint,
                "whatsapp_token": self.whatsapp_token,

                "direct_journal_deferred_income": self.direct_journal_deferred_income.id,
                "direct_journal_recognized_income": self.direct_journal_recognized_income.id,
                "direct_accounts_receivable": self.direct_accounts_receivable.id,
                "direct_deferred_income": self.direct_deferred_income.id,
                "direct_recognized_income": self.direct_recognized_income.id,
                "direct_sales_returned": self.direct_sales_returned.id,

                "direct_deferred_purchase": self.direct_deferred_purchase.id,
                "direct_arrival_purchase": self.direct_arrival_purchase.id,
                "direct_recognized_purchase": self.direct_recognized_purchase.id,
                "direct_purchase_returned": self.direct_purchase_returned.id,

                "direct_discount_expense": self.direct_discount_expense.id,
                "direct_journal_arrival_cash": self.direct_journal_arrival_cash.id,

                "journal_deliver_reject": self.journal_deliver_reject.id,
                "deliver_reject": self.deliver_reject.id,

                "journal_reject_after_deliver": self.journal_reject_after_deliver.id,
                "reject_after_deliver": self.reject_after_deliver.id,

                "return_journal_deferred": self.return_journal_deferred.id,
                "return_journal_recognized": self.return_journal_recognized.id,
                "return_accounts_receivable": self.return_accounts_receivable.id,
                "return_sales_deferred": self.return_sales_deferred.id,
                "return_sales_recognized": self.return_sales_recognized.id,
                "return_sales_hm_dues": self.return_sales_hm_dues.id,
                "return_hm_dues_contact": self.return_hm_dues_contact.id,
                "return_pay_extra_loss": self.return_pay_extra_loss.id,
                "return_journal_cash": self.return_journal_cash.id,
                "return_recognized_purchase": self.return_recognized_purchase.id,
                "return_reject_after_testing": self.return_reject_after_testing.id,
                "return_sales_unrecognized_profit_loss": self.return_sales_unrecognized_profit_loss.id,
                "return_re_sales_profit_loss": self.return_re_sales_profit_loss.id,
            }
            housemaid_main_configuration.create(data)

        except Exception as e:
            logger.exception("Set Values Method")
            raise ValidationError(e)

    # def action_setup_housemaid(self):
    #     post_instllations.main_setup(self)



class ResCompany(models.Model):
    _inherit = 'res.company'

    first_content= fields.Html(string='First Content', )
    second_content= fields.Html(string='Second Content', )

