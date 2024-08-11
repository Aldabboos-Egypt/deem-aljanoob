# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError
import datetime

logger = logging.getLogger(__name__)


class ExternalOffices(models.Model):
    _name = 'housemaidsystem.configuration.externaloffices'
    _rec_name = 'full_name'
    _description = 'External offices'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']



    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        records = self.search([])
        if name:
            ids = self.search(['|', ('name', 'ilike', name), ('code', 'ilike', name)]+ args, limit=limit)
            if records and ids:
                records = self.browse(list(set(records.ids).intersection(ids.ids)))
            elif ids:
                records = ids
        return records.name_get()


    # ==================  Compute / On Change ==========================

    # @api.depends('code', 'full_name')
    # def _compute_name(self):
    #     self.name = self.code.upper() + ' - ' + self.full_name

    @api.onchange('code')
    def _code_upper(self):
        self.code = self.code.upper() if self.code else False

    # ================== Constraints ==========================
    _sql_constraints = [
        ('code_uniqe', 'unique (code,name)', "Code already exists !"),
    ]
    _sql_constraints_account = [
        ('account', "Office Account already exists !"),
    ]
    _sql_constraints_susp_account = [
        ('suspense_account', "Office suspense account already exists !"),
    ]
    _sql_constraints_journal = [
        ('journal', "Office deferred journal already exists !"),
    ]
    _sql_constraints_journal_recognized = [
        ('journal_recognized', "Office recognized journal already exists !"),
    ]

    # ================== Create - unlink - write Methods ==========================

    def create_ir_seq(self, code):
        try:

            ir_seq = self.env['ir.sequence'].search([('name', '=', code)], limit=1)
            if not ir_seq:
                ir_seq_data = {
                    'code': 'housemaidsystem.configuration.externaloffices.' + code,
                    'name': code,
                    'padding': 0,
                    'number_increment': 1,
                    'prefix': code + '%(y)s%(month)s-',
                }
                ir_seq.create(ir_seq_data)
        except Exception as e:
            logger.exception("create_ir_seq")
            raise ValidationError(e)

    def create_office_vendor(self, full_name, code, payable_account):
        try:
            vendor = self.env['res.partner']
            vendor_data = {
                'name': full_name,
                'display_name': code + ' - ' + full_name,
                'active': True,
                # 'customer': False,
                # 'supplier': True,
                'employee': False,
                'is_company': True,
                'property_account_payable_id': payable_account,
            }
            new_vendor = vendor.create(vendor_data)
            return new_vendor.id
        except Exception as e:
            logger.exception("create_office_vendor method")
            raise ValidationError(e)

    def create_account(self, account_name, account_type, currency_id):

        try:
            if account_type == 'suspense':
                account_name = account_name + ' - Suspend Account'
            else:
                account_name = account_name + ' - Main Account'

            account = self.env['account.account']
            account_type = self.sudo().env['account.account.type'].search([('name', 'in', ('Payable','الدائن'))] )

            account_data = {
                'name': account_name,
                'code': self.get_next_code(),
                'currency_id': currency_id,
                'internal_type': 'payable',
                'user_type_id': account_type.id,
                'internal_group': 'liability',
                'reconcile': True
            }
            new_account = account.create(account_data)
            return new_account.id
        except Exception as e:
            logger.exception("create_office_vendor method")
            raise ValidationError(e)

    def create_journal(self, journal_name, account_type, code, currency_id):
        try:
            if account_type == 'deferred':
                journal_data = {
                    'name': journal_name + ' - Deferred Journal',
                    'code': code + 'DF',
                    'currency_id': currency_id,
                    'type': 'general',
                }
            else:

                account_chart_template = self.env['account.chart.template'].search([], limit=1)

                journal_data = {
                    'name': journal_name + ' - Main Journal',
                    'code': code + 'RC',
                    'currency_id': currency_id,
                    'type': 'purchase',
                    'default_account_id': account_chart_template.property_account_expense_categ_id.id,
                }

            journal = self.env['account.journal']
            new_journal = journal.create(journal_data)
            return new_journal.id
        except Exception as e:
            logger.exception("create_office_vendor method")
            raise ValidationError(e)

    def get_next_code(self):
        try:
            accounts_list = self.env['account.account'].search([('internal_type', '=', 'payable')])
            codes = []
            for account in accounts_list:
                codes.append(int(account.code))
            next_code = max(codes) + 1

            return str(next_code)
        except Exception as e:
            logger.exception("get_next_code method")
            raise ValidationError(e)

    @api.depends('code', 'name')
    def _compute_name(self):
        for rec in self:
            rec.full_name = rec.code + ' : ' + rec.name

    @api.model
    def create(self, vals):
        try:
            self.create_ir_seq(vals['code'])
            account_name = vals['code'] + ':' + vals['name'] + ' Account'
            journal_name = vals['code'] + ':' + vals['name'] + ' Journal'
            currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            vals['suspense_account'] = self.create_account(account_name, 'suspense', currency.id),
            vals['account'] = self.create_account(account_name, 'main', currency.id),
            vals['journal'] = self.create_journal(journal_name, 'deferred', vals['code'], currency.id)
            vals['journal_recognized'] = self.create_journal(journal_name, 'recognized', vals['code'], currency.id)
            vals['vendor_id'] = self.create_office_vendor(vals['name'], vals['code'], vals['account'])
            externaloffices = super(ExternalOffices, self).create(vals)

            body_msg = u"""<ul class="o_mail_thread_message_tracking">"""
            body_msg += u"""<li>New external office added at : <span>""" + (datetime.date.today()).strftime(
                '%Y-%m-%d') + u"""</span></li>"""
            body_msg += u"""<li>Office code : <span>""" + externaloffices.code + """</span></li>"""
            body_msg += u"""<li>Office name : <span>""" + externaloffices.name + """</span></li>"""
            body_msg += u"""<li>Office country name : <span>""" + externaloffices.office_country.name + """</span></li>"""

            body_msg += u"""<li>Office deferred journal : <span>""" + externaloffices.journal.name + """</span></li>"""
            body_msg += u"""<li>Office recognized journal : <span>""" + externaloffices.journal_recognized.name + """</span></li>"""

            body_msg += u"""<li>Office main account code : <span>""" + externaloffices.account.code + """</span></li>"""
            body_msg += u"""<li>Office main account number : <span>""" + externaloffices.account.name + """</span></li>"""

            body_msg += u"""<li>Office suspense account code : <span>""" + externaloffices.suspense_account.code + """</span></li>"""
            body_msg += u"""<li>Office suspense account number : <span>""" + externaloffices.suspense_account.name + """</span></li>"""

            body_msg += u"""</ul>"""
            externaloffices.message_post(body=body_msg)

            return externaloffices

        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)

    def write(self, vals):
        try:
            externaloffices = super(ExternalOffices, self).write(vals)
            return externaloffices
        except Exception as e:
            logger.exception("Write Method")
            raise ValidationError(e)

    # ================== Fields====================================================
    name = fields.Char(string="Name",translate=True )
    code = fields.Char(string="Code", required=True, size=6, onchange="_code_upper", copy=False)
    full_name = fields.Char(string="Office Name", compute='_compute_name')
    office_country = fields.Many2one('res.country', string="Office Country", required=True, )
    account = fields.Many2one('account.account', string="Main Account", domain=[('internal_type', '=', 'payable')],
                              help="Please create new payable account for this office as main account.")
    suspense_account = fields.Many2one('account.account', string="Suspense Account",
                                       domain=[('internal_type', '=', 'payable')],
                                       help="Please create new payable account for this office as suspense account.")
    journal = fields.Many2one('account.journal', string="Deferred Journal", domain=[('type', '=', 'purchase')],
                              help="Please create new joural with type miscellaneous to record all transactions on suspense account.")
    journal_recognized = fields.Many2one('account.journal', string="Recognized Journal",
                                         domain=[('type', '=', 'purchase')],
                                         help="Please create new joural with type purchase to record all transactions on main account.")
    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    commission = fields.Float(string="Office Commission", required=True,
                              help="Housemaid commission is cost in USD.")
    sales_price = fields.Float(string="Sales Price", required=False, default=0.0,
                               help="Housemaid sales price")
    office_currency_id = fields.Many2one(comodel_name='res.currency', string="Office Currency",
                                         help="Office Commission", default=2, store=True)
