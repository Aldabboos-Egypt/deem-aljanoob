# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
import datetime
from dateutil import parser
import logging
from . import accounting_integration

logger = logging.getLogger(__name__)

app_stages = [('application', 'Application'),
              ('cancelapplication', 'Cancel Application'),
              ('reservation', 'Reservation'),
              ('printsposnorreceipt', 'Print Sponsor Receipt'),
              ('visa', 'Visa'),
              ('expectedarrival', 'Expected Arrival'),
              ('arrival', 'Arrival'),
              ('deliverpaidfull', 'Delivered Paid Full'),
              ('deliverpaidpartial', 'Delivered Paid Partial'),
              ('resell', 'Re-Sell'),
              ('returnback', 'Return Back From First Sponsor'),
              ('sellastest', 'Sell As Test'),
              ('sellasfinall', 'Sell As Final'),
              ('rejectedbysponsor', 'Rejected By Sponsor'),
              ('returnbackagain', 'Return Back From Last Sponsor'),
              ('backtocountry', 'Back to Country After First Sponsor'),
              ('runaway1', 'Run Away From First Sponsor'),
              ('backtocountry1', 'Back to Country After Last Sponsor'),
              ('runaway2', 'Run Away From Last Sponsor'),
              ]


class applications(models.Model):
    _name = 'housemaidsystem.applicant.applications'
    _description = 'Applications'
    _rec_name = 'external_office_id'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']



    transfer_request_number = fields.Char(string='Transfer Request Number')
    transfer_request_date = fields.Date(string='Transfer Request Date')

    security_approval_number = fields.Char(string='Security Approval Number')
    security_approval_date = fields.Date(string='Security Approval Date')

    work_id_request_number = fields.Char(string='Work ID Request Number')
    work_id_request_date = fields.Date(string='Work ID Request Date')

    # --------------Fields List---------------------------
    # fields.Date.today()
    applicant_date = fields.Date(string="Applicant Date", required=True, default=fields.Date.context_today)
    name = fields.Char(string="Name", compute='_compute_name')
    external_office_id = fields.Char(string="External Office Code", size=20, required=True)
    labor_image = fields.Binary("Photo", attachment=True,
                                help="This field holds the image used as photo for the housemaidsystem, limited to 1024x1024px.")
    full_name = fields.Char(string="Full Name", required=True, size=80)
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices', string="External Office",
                                  required=True)
    marital_status = fields.Selection(string="Marital Status", selection=[
        ('single', 'Single'),
        ('married', 'Married'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], default='single')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', default='female')
    birth_date = fields.Date(string="Birth Date", required=True)
    age = fields.Integer(string="Age")
    kids = fields.Integer(string="Kids", default=0)
    country_id = fields.Many2one('res.country', string='Nationality')
    passport_id = fields.Char(string='Number', size=40)
    passport_issue_date = fields.Date(string="Issue Date")
    passport_expiry_date = fields.Date(string="Expiry Date")
    passport_country_id = fields.Many2one('res.country', string='Issue Country')
    experience = fields.Html('Experience Details', track_visibility='onchange')
    english_skils = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'), ('poor', 'Poor')],
                                     string='English Skills')
    arabic_skils = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'), ('poor', 'Poor')],
                                    string='Arabic Skills')
    place_of_birth = fields.Char(string="Place of birth", size=80)
    post_applied = fields.Many2one('housemaidsystem.configuration.postapplied', string='Post Applied')
    religion = fields.Many2one('housemaidsystem.configuration.religion', string='Religion')
    education = fields.Many2one('housemaidsystem.configuration.education', string='Education')
    state = fields.Selection(app_stages, string='Status', copy=False, track_visibility='onchange',
                             default='application')
    External_office_trans_ids = fields.One2many(comodel_name="housemaidsystem.configuration.externalofficetrans",
                                                inverse_name="application_id",
                                                string="External transactions")
    customer_id = fields.Many2one(comodel_name="res.partner", string="Current Sponsor")
    office_commission = fields.Monetary(string="Office Commission",
                                        currency_field='currency_id', required=False)
    currency_id = fields.Many2one('res.currency', required=False, )
    hm_salary = fields.Float(string="Salary", )
    officebranches = fields.Many2one('housemaidsystem.configuration.officebranches',
                                     string="Sales Office", required=False)
    # ***********************************************************************************
    reservation_down_payment_refund = fields.Many2one('account.payment', 'Down Payment Invoice Refund')
    sell_as_test_down_payment_refund = fields.Many2one('account.payment', 'Sell Ast Test Invoice Refund')
    # ***********************************************************************************
    previouse_state = fields.Selection(app_stages, string='Previous Status', copy=False, default=None)
    # ***********************************************************************************
    analytic_account = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag = fields.Many2one('account.analytic.tag', string='Analytic Tag')

    def register_payment_action(self):
        try:
            reservations_obj = self.env['housemaidsystem.applicant.reservations'].search(
                [('application_id', '=', self.id)],
                limit=1)

            invoice = self.env['account.move'].search \
                ([('id', '=', reservations_obj.invoice_sales_id.id)], limit=1)

            if invoice.state == 'cancel':
                raise ValidationError(
                    "invoice %s is cancel, please activate this invoice before visa process." % (
                        invoice.display_name))

            if invoice.state == 'paid':
                raise ValidationError(
                    "invoice %s is fully paid, please check the invoice payments." % (
                        invoice.display_name))

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.collect_payment_late',
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_collect_payment_form_view').id, 'form')],
                'name': 'Collect Payment Late',
                'context': {'default_application_id': self.id,
                            'default_transaction_date': fields.Date.today(),
                            'default_deal_amount': reservations_obj.deal_amount,
                            'default_invoice_sales_id': reservations_obj.invoice_sales_id.id,
                            'default_customer_id': reservations_obj.customer_id.id,
                            'default_down_payment_amount': (
                                                               reservations_obj.down_payment_amount if reservations_obj.down_payment_amount else 0.0) + (
                                                               reservations_obj.additional_payment_amount if reservations_obj.additional_payment_amount else 0.0),
                            'default_down_payment_invoice': reservations_obj.down_payment_invoice.id,
                            'default_due_amount': reservations_obj.invoice_sales_id.amount_residual_signed,
                            },
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result
        except Exception as e:
            logger.exception("register_payment_action")
            raise ValidationError(e)

    # ************* Sponsor Payments *******
    # def print_sponsor_hm_payment_action(self):
    # if self.state == 'returnback':
    #     sellastest_obj = self.env['housemaidsystem.applicant.selltest']. \
    #         search([('application_id', '=', self.id)], order='id desc', limit=1)
    #     if sellastest_obj:
    #         docs = self.env['housemaidsystem.sponsorpayments'].search \
    #             ([('application_id', '=', self.id), ('customer_id', '=', sellastest_obj.new_customer_id.id),
    #               ('payment_type', '=', 'Payment')],
    #              order='id desc', limit=1)
    #     else:
    #         docs = self.env['housemaidsystem.sponsorpayments'].search \
    #             ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id),
    #               ('payment_type', '=', 'Payment')],
    #              order='id desc', limit=1)
    #
    # if self.state == 'returnbackagain':
    #     docs = self.env['housemaidsystem.sponsorpayments'].search \
    #         ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id),
    #           ('payment_type', '=', 'Payment')],
    #          order='id desc', limit=1)
    # # Printing Call
    # # =================
    # if docs:
    #     data = {}
    #     report = self.env.ref('housemaidsystem.report_payment_receipt_action')
    #     return report.report_action(docs, data=data)
    # else:
    #     raise ValidationError("No data found.")

    def print_sponsor_contract_action(self):
        try:
            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.configuration.contracts_print',
                'views': [
                    (self.env.ref('housemaidsystem.housemaid_configuration_contracts_print_tree_view').id, 'tree'),
                    (False, 'form')],
                'name': 'Sponsor Contracts List',
                'context': {'search_default_customer_id': self.customer_id.id,
                            'search_default_application_id': self.id},
                'view_mode': 'list,form',
                'view_ids': [],
                'target': 'current',
                'res_id': 0,
            }
            return result
        except Exception as e:
            logger.exception("print_sponsor_contract_action")
            raise ValidationError(e)

    def print_sponsor_payment_action(self):
        try:
            result = None
            customer_id = 0
            applications_obj = self.env['housemaidsystem.applicant.applications'].search \
                ([('id', '=', self.id)], limit=1, order='id desc')

            if applications_obj:
                if applications_obj.state == 'application':
                    applications_cancel_obj = self.env['housemaidsystem.applicant.cancel_reservations'].search \
                        ([('application_id', '=', applications_obj.id)], limit=1, order='id desc')
                    if applications_cancel_obj:
                        customer_id = applications_cancel_obj.customer_id.id
                else:
                    customer_id = applications_obj.customer_id.id
                if customer_id == 0:
                    raise ValidationError("This application doesn't have any payments")

                result = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.payment',
                    'views': [(self.env.ref('account.view_account_payment_tree').id, 'tree'),
                              (False, 'form')],
                    'name': 'Sponsor Payments List',
                    'context': {'search_default_partner_id': customer_id},
                    'view_mode': 'list,form',
                    'view_ids': [],
                    'target': 'current',
                    'res_id': 0,
                }
            return result

            # result = {
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'housemaidsystem.sponsorpayments',
            #     'views': [(self.env.ref('housemaidsystem.housemaid_sponsor_payments_list_tree_view').id, 'tree'),
            #               (False, 'form')],
            #     'name': 'Sponsor Payment List',
            #     'context': {'search_default_application_id': self.id, 'search_default_state': 'confirmed', },
            #     'view_mode': 'list,form',
            #     'view_ids': [],
            #     'target': 'current',
            #     'res_id': 0,
            # }

        except Exception as e:
            logger.exception("print_sponsor_hm_payment_action Method")
            raise ValidationError(e)
        # docs = None
        #
        # if self.state == 'application':
        #     docs = self.env['housemaidsystem.sponsorpayments'].search \
        #         ([('application_id', '=', self.id)],
        #          order='id desc', limit=1)
        #
        # # Reservation\Visa\Expected Arriaval\Arriva
        # #=========================================
        # if self.state == 'reservation' or self.state == 'visa' \
        #         or self.state == 'expectedarrival' or self.state == 'arrival':
        #     reservation = self.env['housemaidsystem.applicant.reservations'].search \
        #         ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
        #     docs = self.env['housemaidsystem.sponsorpayments'].search\
        #         ([('application_id', '=', self.id), ('customer_id', '=', reservation.customer_id.id),
        #           ('app_state', '=', '')],
        #          order='id desc', limit=1)
        #
        #
        # # Print Sponsor Receipt after Deliver and paid full
        # #==================================================
        # if self.state == 'deliverpaidfull':
        #     docs = self.env['housemaidsystem.sponsorpayments'].search \
        #         ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id)],
        #          order='id desc', limit=1)
        #
        # # Print Sponsor Receipt after Deliver and paid partial
        # #==================================================
        # if self.state == 'deliverpaidpartial':
        #     docs = self.env['housemaidsystem.sponsorpayments'].search \
        #         ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id)],
        #          order='id desc', limit=1)
        #
        # # Print Sponsor Receipt after Deliver and paid partial
        # #==================================================
        # if self.state == 'returnback':
        #     sellastest_obj = self.env['housemaidsystem.applicant.selltest'].\
        #         search([('application_id', '=', self.id)], order='id desc', limit=1)
        #     if sellastest_obj:
        #         docs = self.env['housemaidsystem.sponsorpayments'].search \
        #             ([('application_id', '=', self.id), ('customer_id', '=', sellastest_obj.new_customer_id.id),
        #               ('payment_type', '=', 'Refund')],
        #              order='id desc', limit=1)
        #     else:
        #         docs = self.env['housemaidsystem.sponsorpayments'].search \
        #             ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id), ('payment_type', '=', 'Refund')],
        #              order='id desc', limit=1)
        #
        # # Print Sponsor Receipt after sell as test
        # #==================================================
        # if self.state == 'sellastest':
        #     docs = self.env['housemaidsystem.sponsorpayments'].search \
        #         ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id), ('payment_type', '=', 'Payment')],
        #          order='id desc', limit=1)
        #
        # # Print Sponsor Receipt after sell as test
        # # ==================================================
        # if self.state == 'sellasfinall':
        #     docs = self.env['housemaidsystem.sponsorpayments'].search \
        #         ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id),
        #           ('payment_type', '=', 'Payment')],
        #          order='id desc', limit=1)
        #
        # # Print Sponsor Receipt when return back from last sposnor
        # # ==================================================
        # if self.state == 'returnbackagain':
        #     docs = self.env['housemaidsystem.sponsorpayments'].search \
        #         ([('application_id', '=', self.id), ('customer_id', '=', self.customer_id.id),
        #           ('payment_type', '=', 'Refund')],
        #          order='id desc', limit=1)
        #
        #
        # # Printing Call
        # #=================
        # if docs:
        #     data = {}
        #     report = self.env.ref('housemaidsystem.report_payment_receipt_action')
        #     return report.report_action(docs, data=data)
        # else:
        #     raise ValidationError("No data found.")

    # ************* Application State {1-cancel application \ 2-reservation}*******
    def application_cancelapplication_action(self):
        result = {
            'name': 'Application Cancel',
            'res_model': 'housemaidsystem.applicant.cancelapplication',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_cancelapplication_form_view').id, 'form')],
            'context': {'default_application_id': self.id},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def application_reservation_action(self):
        deal_amount = 0.0
        external_office = self.env['housemaidsystem.configuration.externaloffices'].browse(self.office_code.id)
        if external_office:
            deal_amount = external_office.sales_price if external_office.sales_price else 0.0

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.reservations',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_reservations_form_view').id, 'form')],
            'name': 'Reservation',
            'context': {'default_application_id': self.id,
                        'default_deal_amount': deal_amount,
                        'default_reservation_date': fields.Date.today()},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # *******Cancel Application State {1- Activate Application}*******************
    def cancelapplication_application_action(self):
        result = {
            'name': 'Application Activation',
            'res_model': 'housemaidsystem.applicant.activateapplication',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_activeatepplication_form_view').id, 'form')],
            'context': {'default_application_id': self.id},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # ******* Reservation State {1- Cancel Reservation / 3- Create Visa}*****
    def cancel_reservation_action(self):
        reservations_obj = self.env['housemaidsystem.applicant.reservations'].search([('application_id', '=', self.id)],
                                                                                     limit=1)
        reservations_obj.unlink()

    def reservation_visa_action(self):
        reservations_obj = self.env['housemaidsystem.applicant.reservations'].search([('application_id', '=', self.id)],
                                                                                     limit=1)
        invoice = self.env['account.move'].search \
            ([('id', '=', reservations_obj.invoice_sales_id.id)], limit=1)

        if invoice.state == 'cancel':
            raise ValidationError(
                "invoice %s is cancel, please activate this invoice before visa process." % (
                    invoice.display_name))

        previouse_visa = self.env['housemaidsystem.applicant.visa'].search(
            [('customer_id', '=', reservations_obj.customer_id.id)], limit=1, order='id DESC')

        if previouse_visa:

            if previouse_visa.visa_sponsor_name:
                visa_sponsor_name_str = previouse_visa.visa_sponsor_name
            else:
                if reservations_obj.customer_id.name:
                    visa_sponsor_name_str = reservations_obj.customer_id.name
                else:
                    visa_sponsor_name_str = ''

            if previouse_visa.country_id:
                visa_sponsor_name_str = previouse_visa.visa_sponsor_name
            else:
                if reservations_obj.customer_id.name:
                    visa_sponsor_name_str = reservations_obj.customer_id.name
                else:
                    visa_sponsor_name_str = ''


        else:
            if reservations_obj.customer_id.name:
                visa_sponsor_name_str = previouse_visa.visa_sponsor_name
            else:
                visa_sponsor_name_str = ''

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.visa',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_visa_form_view').id, 'form')],
            'name': 'Visa',
            'context': {'default_application_id': self.id,
                        'default_transaction_date': fields.Date.today(),
                        'default_visa_issue_date': fields.Date.today(),
                        'default_visa_exp_date': fields.Date.today(),
                        'default_visa_rec_date': fields.Date.today(),
                        'default_visa_snd_date': fields.Date.today(),
                        # 'default_visa_sponsor_name': visa_sponsor_name_str,
                        # 'default_country_id': visa_sponsor_name_str,
                        # 'default_state_id': visa_sponsor_name_str,
                        # 'default_area_id': visa_sponsor_name_str,
                        # 'default_sponsor_block': visa_sponsor_name_str,
                        # 'default_sponsor_street': visa_sponsor_name_str,
                        # 'default_sponsor_street': visa_sponsor_name_str,
                        # 'default_sponsor_street': visa_sponsor_name_str,
                        },
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # ******* printsposnorreceipt State {1- Make application active}*****
    def make_application_active_after_print_refund_payment_action(self):
        self.state = 'application'

    # ***Visa State {1- cancel visa / 2- Record expected arrival / 3- Edit Visa}***
    def cancel_visa_action(self):
        visa_obj = self.env['housemaidsystem.applicant.visa'].search([('application_id', '=', self.id)],
                                                                     limit=1)
        visa_obj.unlink

    def visa_expectedarrival_action(self):
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.expectedarrival',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_expectedarrival_form_view').id, 'form')],
            'name': 'Expected Arrival',
            'context': {'default_application_id': self.id,
                        'default_transaction_date': fields.Date.today(),
                        'default_expected_arrival_date': datetime.datetime.now(),
                        'default_email_date': fields.Date.today()},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def edit_visa_action(self):
        visa_obj = self.env['housemaidsystem.applicant.visa'].search([('application_id', '=', self.id)],
                                                                     limit=1)
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.visa',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_visa_editform_view').id, 'form')],
            'name': 'Visa',
            'context': {'default_application_id': self.id},
            'res_id': visa_obj.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # ***Expected Arrival State {1- cancel Expected Arrival / 2- Record arrival / 3- Edit Expected arrival}***
    def cancel_expectedarrival_action(self):
        expectedarrival_obj = self.env['housemaidsystem.applicant.expectedarrival'].search(
            [('application_id', '=', self.id)],
            limit=1)
        expectedarrival_obj.unlink()

    def expectedarrival_arrival_action(self):

        reservation = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', self.id)], limit=1)

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.arrival',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_arrival_form_view').id, 'form')],
            'name': 'Arrival',
            'context': {'default_application_id': self.id,
                        'default_transaction_date': fields.Date.today(),
                        'default_invoice_id': reservation.invoice_sales_id.id,
                        'default_arrival_date': fields.Date.today()},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def edit_expectedarrival_action(self):
        expectedarrival_obj = self.env['housemaidsystem.applicant.expectedarrival'].search(
            [('application_id', '=', self.id)],
            limit=1)
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.expectedarrival',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_expectedarrival_editform_view').id, 'form')],
            'name': 'Expected Arrival',
            'context': {'default_application_id': self.id},
            'res_id': expectedarrival_obj.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

        # *****************************************************************************
        # ***Arrival State {1- cancel Arrival / 2- Record deliver / 3- Edit arrival  / 4- Invoice & payment / 5- resell}***

    def cancel_arrival_action(self):
        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search([('application_id', '=', self.id)], limit=1)
        arrival_obj.unlink()

    # Deliver housemaidsystem for first sponsor
    def arrival_deliver_action(self):
        try:
            reservation = self.env['housemaidsystem.applicant.reservations'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.deliver',
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_deliver_form_view').id, 'form')],
                'name': 'Deliver Housemaid For First Sponsor',
                'context': {'default_application_id': self.id,
                            'default_customer_id': reservation.customer_id.id,
                            'default_vendor_id': reservation.invoice_purchase_id.partner_id.id,
                            'default_paid_amount': reservation.invoice_sales_id.amount_residual,
                            'default_invoice_id': reservation.invoice_sales_id.id,
                            'default_invoice_po_id': reservation.invoice_purchase_id.id},
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result

        except Exception as e:
            logger.exception("arrival_deliver_action Method")
            raise ValidationError(e)

    def edit_arrival_action(self):
        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search(
            [('application_id', '=', self.id)],
            limit=1)
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.arrival',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_arrival_editform_view').id, 'form')],
            'name': 'Arrival',
            'context': {'default_application_id': self.id},
            'res_id': arrival_obj.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # Resell Button
    def resell_for_first_spons_action(self):
        try:
            reservation = self.env['housemaidsystem.applicant.reservations'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
            invoice = self.env['account.move'].search \
                ([('id', '=', reservation.invoice_sales_id.id)], limit=1)

            # if invoice.amount_total != invoice.amount_residual:
            #     raise ValidationError(_(
            #         "invoice %s has active payments, please refund any payment before start re-sell process." % (
            #             invoice.display_name)))

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.resell',
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_resell_form_view').id, 'form')],
                'name': 'Re-Sell',
                'context': {'default_application_id': self.id,
                            'default_customer_id': reservation.customer_id.id,
                            'default_vendor_id': reservation.invoice_purchase_id.partner_id.id,
                            'default_invoice_id': reservation.invoice_sales_id.id,
                            'default_refund': (invoice.amount_total - invoice.amount_residual),
                            'default_invoice_po_id': reservation.invoice_purchase_id.id},
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result
        except Exception as e:
            logger.exception("resell_for_first_spons_action Method")
            raise ValidationError(e)

        # *****************************************************************************
        # ***re-sell State {1- cancel resell / 2- Sell as test / 3- Print sposor voucher}***

    def cancel_resell_for_first_spons_action(self):
        resell = self.env['housemaidsystem.applicant.resell'].search([('application_id', '=', self.id)],
                                                                     limit=1)
        resell.unlink()
        self.state = 'arrival'

    def sell_as_test_after_resell_action(self):
        resell = self.env['housemaidsystem.applicant.resell'].search \
            ([('application_id', '=', self.id)], limit=1)

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.selltest',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view').id, 'form')],
            'name': 'Sell As Test',
            'context': {'default_application_id': self.id,
                        'default_old_customer_id': resell.customer_id.id,
                        'default_old_invoice_id': resell.invoice_id.id},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

        # *****************************************************************************
        # *** Delivered partial paid State {1- step back / 2- pay all}***

    def step_back_arrival_action(self):
        deliver = self.env['housemaidsystem.applicant.deliver'].search([('application_id', '=', self.id)],
                                                                       limit=1)

        deliver.unlink()
        self.state = 'arrival'

    def pay_all_action(self):
        deliver = self.env['housemaidsystem.applicant.deliver'].search([('application_id', '=', self.id)],
                                                                       limit=1)
        deliver.paid_payment2_invoice = accounting_integration.deliver_sales_second_payment(deliver)
        self.state = 'deliverpaidfull'

    def deliver_printinvoice_action(self):
        reservation = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.move_form').id, 'form')],
            'name': 'Invoice',
            'context': {'default_invoice_sales_id': self.id},
            'res_id': reservation.invoice_sales_id.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

        # *****************************************************************************
        # *** Delivered paid full State {1- step back / 2- Return Back from first sponsor / 3- print invoice}***

    def step_back_to_arrival_action(self):
        reservation = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', self.id)], limit=1)
        deliver = self.env['housemaidsystem.applicant.deliver'].search([('application_id', '=', self.id)],
                                                                       limit=1)
        deliver.unlink()
        self.state = 'arrival'

    def return_back_from_first_spons_action(self):
        try:
            # Get Purchase deferred account
            # self._cr.execute("""Select
            #                     (A.amount - C.amount)
            #                     from
            #                     account_move      A,
            #                     account_move_line B,
            #                     account_payment   C
            #                     where
            #                     A."id" = B.move_id
            #                     and b.reconciled = 'true'
            #                     and a."state" = 'posted'
            #                     and a.partner_id = %s
            #                     and c.id = B.payment_id
            #                     and c.payment_difference_handling = 'reconcile'
            #                     and c.writeoff_account_id is not null""", (reservation.customer_id.id,))
            #
            # for result in self._cr.fetchall():
            #     customer_dues = result[0] if result[0] else 0
            customer_dues = discount = 0
            reservation = self.env['housemaidsystem.applicant.reservations'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
            invoice = self.env['account.move'].search \
                ([('id', '=', reservation.invoice_sales_id.id)], limit=1)
            customer_dues = (invoice.amount_total - invoice.amount_residual_signed)

            deliver = self.env['housemaidsystem.applicant.deliver'].search \
                ([('application_id', '=', self.id)], limit=1)
            discount = deliver.discount_amount if deliver.discount_amount else 0.0

            customer_dues = customer_dues - discount

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.returnbackfromfirstsponsor',
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_returnbackfromfirstsponsor_form_view').id,
                           'form')],
                'name': 'Return Back From First Sponsor',
                'context': {'default_application_id': self.id,
                            'default_customer_id': reservation.customer_id.id,
                            'default_invoice_id': reservation.invoice_sales_id.id,
                            'default_previouse_discount': discount,
                            'default_deliver_date': deliver.deliver_date},
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result
        except Exception as e:
            logger.exception("return_back_from_first_spons_action Title")
            raise ValidationError(e)

    def deliverpaidfull_printinvoice_action(self):
        reservation = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.move_form').id, 'form')],
            'name': 'Invoice',
            'context': {'default_invoice_sales_id': self.id},
            'res_id': reservation.invoice_sales_id.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def deliverpaidfull_print_sale_invoice_action(self):
        deliver_obj = self.env['housemaidsystem.applicant.deliver'].search \
            ([('application_id', '=', self.id)], limit=1)

        if not deliver_obj.paid_payment_invoice:
            raise ValidationError(
                _('No payment is paid upon deliver the housemaidsystem.'))


        else:
            payment_date = deliver_obj.paid_payment_invoice.payment_date
            payment_name = deliver_obj.paid_payment_invoice.name
            payment_total = 0.0
            payment_paid = deliver_obj.paid_payment_invoice.amount
            payment_amount_str = accounting_integration.convert_amount_to_word(payment_paid)
            housemaid_ref = deliver_obj.application_id.external_office_id + ':' + deliver_obj.application_id.full_name
            payment_reason = 'Deliver Housemaid %s To First Sponsor' % (housemaid_ref)
            payment_responsible = 'Hamada'

            sponsor_name = deliver_obj.customer_id.name

            invoice_amount_total = 0.0
            invoice_amount_residual = 0.0
            payment_invoice_ref = 'hhhh'

            data = {'payment_name': payment_name,
                    'payment_date': payment_date, 'payment_total': payment_total, 'payment_paid': payment_paid,
                    'payment_amount_str': payment_amount_str, 'invoice_amount_total': invoice_amount_total,
                    'invoice_amount_residual': invoice_amount_residual,
                    'payment_invoice_ref': payment_invoice_ref, 'payment_reason': payment_reason,
                    'payment_responsible': payment_responsible,
                    'sponsor_name': sponsor_name, 'housemaid_ref': housemaid_ref
                    }
            docs = None
            report = self.env.ref(
                'housemaidsystem.payment_receipt_report_action')
            return report.report_action(docs, data=data)

        # *****************************************************************************
        # *** Return back from first sponsor State {1- step back / 2- Sell as test / 3- Show current sponsor / 4- print refund voucher***

    def step_back_deliverfullpay_action(self):
        returnbackfromfirstsponsor_obj = self.env['housemaidsystem.applicant.returnbackfromfirstsponsor'].search \
            ([('application_id', '=', self.id)], limit=1)

        returnbackfromfirstsponsor_obj.unlink()
        self.state = 'deliverpaidfull'

    def sell_as_test_after_returnback_from_first_sponsor_action(self):
        refund_amount = 0.0
        reservation = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
        if reservation:
            if reservation.invoice_sales_id:
                refund_amount = reservation.invoice_sales_id.amount_total

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.selltest',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view').id, 'form')],
            'name': 'Sell As Test',
            'context': {'default_application_id': self.id,
                        'default_old_customer_id': reservation.customer_id.id,
                        'default_old_invoice_id': reservation.invoice_sales_id.id,
                        'default_previous_refund': refund_amount if refund_amount != 0.0 else 0.0},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def back_to_country_after_returnback_from_first_sponsor_action(self):
        self.state = 'backtocountry'
        self.previouse_state = 'returnback'

    def runaway_after_returnback_from_first_sponsor_action(self):
        self.state = 'runaway1'
        self.previouse_state = 'returnback'

        # reservation = self.env['housemaidsystem.applicant.reservations'].search \
        #     ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
        # deliver = self.env['housemaidsystem.applicant.deliver'].search \
        #     ([('application_id', '=', self.id)], limit=1)
        # returnbackfromfirstsponsor = self.env['housemaidsystem.applicant.returnbackfromfirstsponsor'].search \
        #     ([('application_id', '=', self.id)], limit=1)
        #
        # customer_dues = 0
        # # Get Purchase deferred account
        # self._cr.execute("""Select
        #                     (A.amount - C.amount)
        #                     from
        #                     account_move A,account_move_line B,account_payment C
        #                     where
        #                     A."id" = B.move_id
        #                     and b.reconciled = 'true'
        #                     and a."state" = 'posted'
        #                     and a.partner_id = %s
        #                     and c.id = B.payment_id
        #                     and c.payment_difference_handling = 'reconcile'
        #                     and c.writeoff_account_id is not null""", (reservation.customer_id.id,))
        #
        # for result in self._cr.fetchall():
        #     customer_dues = result[0] if result[0] else 0
        #
        # result = {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'housemaidsystem.applicant.backtocountryafterfirstsponsor',
        #     'views': [(self.env.ref('housemaidsystem.housemaid_applicant_backtocountryafterfirstsponsor_form_view').id,
        #                'form')],
        #     'name': 'Back To Country After Back From First Sponsor',
        #     'context': {'default_application_id': self.id,
        #                 'default_customer_id': reservation.customer_id.id,
        #                 'default_invoice_id': reservation.invoice_sales_id.id,
        #                 'default_previouse_discount': customer_dues,
        #                 'default_deliver_date': returnbackfromfirstsponsor.return_date,
        #                 'default_refund_amount': returnbackfromfirstsponsor.refund_amount},
        #     'flags': {'form': {'action_buttons': False}},
        #     'target': 'new',
        # }
        # return result

    def back_to_country_after_returnback_from_last_sponsor_action(self):
        self.state = 'backtocountry1'
        self.previouse_state = 'returnbackagain'

    def runaway_after_returnback_from_last_sponsor_action(self):
        self.state = 'runaway2'
        self.previouse_state = 'returnbackagain'

        # result = {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'housemaidsystem.applicant.backtocountryafterlastsponsor',
        #     'views': [(self.env.ref('housemaidsystem.housemaid_applicant_backtocountryafterlastsponsor_form_view').id,
        #                'form')],
        #     'name': 'Back To Country After Back From Last Sponsor',
        #     'context': {'default_application_id': self.id,
        #                 'default_customer_id': self.customer_id.id},
        #     'flags': {'form': {'action_buttons': False}},
        #     'target': 'new',
        # }
        # return result

    def returnback_printinvoice_action(self):
        reservation = self.env['housemaidsystem.applicant.reservations'].search \
            ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.move_form').id, 'form')],
            'name': 'Invoice',
            'context': {'default_invoice_sales_id': self.id},
            'res_id': reservation.invoice_sales_id.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # <!-- *** Sell As test State {1- Step back / 2- Test Accepted / 3- Test Rejected / 4- View Invoice / 5- Print sponsor voucher} ***-->

    def sellastest_printinvoice_action(self):
        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')
        if selltest:
            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'views': [(self.env.ref('account.move_form').id, 'form')],
                'name': 'Invoice',
                'context': {'default_invoice_id': self.id},
                'res_id': selltest.new_invoice_id.id,
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result

    def sellastest_printinvoicevoucher_action(self):
        try:
            selltest = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id)], limit=1)

            if not selltest.down_payment_invoice:
                raise ValidationError(
                    _('No payment is paid upon sell the housemaidsystem as test.'))
            else:
                data = {}
                docs = self.env['account.payment'].search([('id', '=', selltest.down_payment_invoice.id)])
                report = self.env.ref(
                    'housemaidsystem.report_payment_receipt_document_action')
                return report.report_action(docs, data=data)
        except Exception as e:
            logger.exception("sellastest_printinvoicevoucher_action Method")
            raise ValidationError(e)

    def sellastest_test_result_action(self):
        try:
            selltest_obj = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'inactive')], limit=1, order='id desc')
            if not selltest_obj:
                raise ValidationError("Record not found.")
            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.selltest',
                'res_id': selltest_obj.id,
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view_action').id, 'form')],
                'name': 'Sell Test Result',
                'context': {'default_application_id': self.id, },
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result
        except Exception as e:
            logger.exception("sellastest_test_result_action Method")
            raise ValidationError(e)

    def sellastest_test_accepted_action(self):
        try:
            selltest = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1, order='id desc')

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.selltest',
                'res_id': selltest.id,
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view_action').id, 'form')],
                'name': 'Sell Test - Accepted',
                'context': {'default_application_id': self.id, },
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result



        except Exception as e:
            logger.exception("sellastest_test_accepted_action Method")
            raise ValidationError(e)

    def sellastest_test_rejected_action(self):
        try:
            selltest_obj = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'inactive')],
                 limit=1, order='id desc')

            if not selltest_obj:
                raise ValidationError("Record not found.")

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.selltest',
                'res_id': selltest_obj.id,
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view_action').id, 'form')],
                'name': 'Sell Test - Reject',
                'context': {'default_application_id': self.id, },
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
            return result


        except Exception as e:
            logger.exception("sellastest_test_rejected_action Method")
            raise ValidationError(e)

    def rejectedbysponsor_printinvoicevoucher_action(self):
        try:
            if not self.sell_as_test_down_payment_refund:
                raise ValidationError(
                    _('No payment is paid upon reject testing the housemaidsystem.'))
            else:
                data = {}
                docs = self.env['account.payment'].search([('id', '=', self.sell_as_test_down_payment_refund.id)])
                report = self.env.ref(
                    'housemaidsystem.report_payment_receipt_document_action')
                return report.report_action(docs, data=data)
        except Exception as e:
            logger.exception("sellasfinal_printinvoice_action Method")
            raise ValidationError(e)

    # *** <!-- *** Sell As final State {1- Step back  / 2- Return Back / 3- View Invoice} ***-->***
    def step_back_sellastest_action(self):
        try:
            selltest = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1, order='id desc')
            if selltest:
                selltest.write({'rec_status': 'inactive'})
                selltest.invoice_sales_recong_id.button_cancel()
                selltest.complete_payment_invoice.cancel()
                selltest.complete_payment_amount = 0
                self.state = 'sellastest'
        except Exception as e:
            logger.exception("step_back_sellastest_action Method")
            raise ValidationError(e)

    def sellasfinal_step_back_sell_test_results_action(self):
        try:
            new_customer_id = new_invoice_id = None
            previous_discount = 0.0

            selltest = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id)], limit=1, order='id desc')

            if selltest:
                if selltest.invoice_sales_recong_id:
                    selltest.invoice_sales_recong_id.button_cancel()
                    selltest.invoice_sales_recong_id.unlink()

                if selltest.close_deliver_reject_balance_move:
                    selltest.invoice_sales_recong_id.button_cancel()
                    selltest.invoice_sales_recong_id.unlink()

                # if selltest.complete_payment_invoice:
                #     accounting_integration.resell_sales_invoice_reverse_payment(selltest)

                selltest.application_id.state = 'sellastest'
                selltest.rec_status = 'inactive'



        except Exception as e:
            logger.exception("sellasfinal_step_back_sell_test_results_action Method")
            raise ValidationError(e)

    def sellasfinal_retunback_action(self):

        old_customer_obj = old_invoice_obj = deliver_date = None
        previous_discount = paid_by_sponsor = 0.0

        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')
        if selltest:
            old_customer_obj = selltest.new_customer_id
            old_invoice_obj = selltest.new_invoice_id
            old_invoice_total = old_invoice_obj.amount_total if old_invoice_obj.amount_total else 0.0
            deliver_date = selltest.test_date
            previous_discount = selltest.sepecial_discount_amount if selltest.sepecial_discount_amount else 0.0
            paid_by_sponsor = old_invoice_total - previous_discount

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.returnbackfromlastsponsor',
            'views': [
                (self.env.ref('housemaidsystem.housemaid_applicant_returnbackfromlastsponsor_form_view').id, 'form')],
            'name': 'Return Back From Last Sponsor',
            'context': {'default_application_id': self.id,
                        'default_deliver_date': deliver_date,
                        'default_old_customer_id': old_customer_obj.id,
                        'default_previous_discount': previous_discount,
                        'default_paid_by_sponsor': paid_by_sponsor,
                        'default_old_invoice_id': old_invoice_obj.id},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def sellasfinal_printinvoice_action(self):
        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.move_form').id, 'form')],
            'name': 'Invoice',
            'context': {'default_invoice_id': self.id},
            'res_id': selltest.new_invoice_id.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def sellasfinal_printinvoicevoucher_action(self):
        try:
            selltest = self.env['housemaidsystem.applicant.selltest'].search \
                ([('application_id', '=', self.id)], limit=1)

            if not selltest.complete_payment_invoice:
                raise ValidationError(
                    _('No payment is paid upon sell the housemaidsystem as final.'))
            else:
                data = {}
                docs = self.env['account.payment'].search([('id', '=', selltest.complete_payment_invoice.id)])
                report = self.env.ref(
                    'housemaidsystem.report_payment_receipt_document_action')
                return report.report_action(docs, data=data)
        except Exception as e:
            logger.exception("sellasfinal_printinvoice_action Method")
            raise ValidationError(e)

    # *** <!-- *** Return Back From Last Sponsor State {1- Step back  / 2- Sell As test / 3- View Invoice} ***-->***
    def step_back_sellasfinal_action(self):
        self.state = 'sellasfinall'

    def returnbackagain_printinvoice_action(self):
        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')

        if not selltest:
            raise ValidationError(
                "No invoice is available.")

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.move_form').id, 'form')],
            'name': 'Invoice',
            'context': {'default_invoice_id': self.id},
            'res_id': selltest.new_invoice_id.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    def sell_as_test_after_returnback_from_last_sponsor_action(self):
        refund_amount = 0.0
        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id), ('test_status', '=', 'accepted')], limit=1, order='id desc')

        returnbackfromlastsponsor = self.env['housemaidsystem.applicant.returnbackfromlastsponsor'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')

        if returnbackfromlastsponsor:
            refund_amount = returnbackfromlastsponsor.refund_amount

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'housemaidsystem.applicant.selltest',
            'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view').id, 'form')],
            'name': 'Re-Sell',
            'context': {'default_application_id': self.id,
                        'default_old_customer_id': selltest.new_customer_id.id,
                        'default_old_invoice_id': selltest.new_invoice_id.id,
                        'default_previous_refund': refund_amount if refund_amount != 0.0 else 0.0},
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }
        return result

    # *** <!-- *** Rejected by sponsor {1- Sell As test /2- View Invoice} ***-->***

    def sell_as_test_after_rejected_by_sponsor_action(self):
        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')
        if selltest:
            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.selltest',
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view').id, 'form')],
                'name': 'Re-Sell',
                'context': {'default_application_id': self.id, 'default_old_customer_id': selltest.new_customer_id.id,
                            'default_old_invoice_id': selltest.new_invoice_id.id},
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
        else:
            reservation = self.env['housemaidsystem.applicant.reservations'].search \
                ([('application_id', '=', self.id), ('rec_status', '=', 'active')], limit=1)

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.applicant.selltest',
                'views': [(self.env.ref('housemaidsystem.housemaid_applicant_selltest_form_view').id, 'form')],
                'name': 'Re-Sell',
                'context': {'default_application_id': self.id, 'default_old_customer_id': reservation.customer_id.id,
                            'default_old_invoice_id': reservation.invoice_sales_id.id},
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
        return result

    def rejectedbysponsor_printinvoice_action(self):
        selltest = self.env['housemaidsystem.applicant.selltest'].search \
            ([('application_id', '=', self.id)], limit=1, order='id desc')
        if selltest:
            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'views': [(self.env.ref('account.move_form').id, 'form')],
                'name': 'Invoice',
                'context': {'default_invoice_id': self.id},
                'res_id': selltest.new_invoice_id.id,
                'flags': {'form': {'action_buttons': False}},
                'target': 'new',
            }
        else:
            resell = self.env['housemaidsystem.applicant.resell'].search \
                ([('application_id', '=', self.id)], limit=1)
            if resell:
                resell = self.env['housemaidsystem.applicant.resell'].search \
                    ([('application_id', '=', self.id)], limit=1)
                result = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'views': [(self.env.ref('account.move_form').id, 'form')],
                    'name': 'Invoice',
                    'context': {'default_invoice_id': self.id},
                    'res_id': resell.invoice_id.id,
                    'flags': {'form': {'action_buttons': False}},
                    'target': 'new',
                }
            else:
                reservations = self.env['housemaidsystem.applicant.reservations'].search \
                    ([('application_id', '=', self.id)], limit=1)
                result = {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'views': [(self.env.ref('account.move_form').id, 'form')],
                    'name': 'Invoice',
                    'context': {'default_invoice_id': self.id},
                    'res_id': reservations.invoice_sales_id.id,
                    'flags': {'form': {'action_buttons': False}},
                    'target': 'new',
                }

        return result

    # View Current Sponsor
    def view_sponsor_action(self):

        applications_obj = self.env['housemaidsystem.applicant.applications'].search \
            ([('id', '=', self.id)], limit=1, order='id desc')

        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'views': [(self.env.ref('base.view_partner_form').id, 'form')],
            'name': 'Sponsor',
            'context': {'default_customer': applications_obj.customer_id.id},
            'res_id': applications_obj.customer_id.id,
            'flags': {'form': {'action_buttons': False}},
            'target': 'new',
        }

        return result

    def sponsor_dues_action(self):
        try:

            result = {
                'type': 'ir.actions.act_window',
                'res_model': 'housemaidsystem.sponsorpayments',
                'views': [(self.env.ref('housemaidsystem.housemaid_sponsor_payments_list_tree_view').id, 'tree'),
                          (False, 'form')],
                'name': 'Sponsor Payments List',
                'context': {'search_default_application_id': self.id, 'search_default_state': 'draft', },
                'view_mode': 'list,form',
                'view_ids': [],
                'target': 'current',
                'res_id': 0,
            }
            return result
        except Exception as e:
            logger.exception("sponsor_dues_action Method")
            raise ValidationError(e)

    # <!--  ***  Return Back to country {1- step Back} ***-->
    def step_back_from_backtocountry_to_returnback_action(self):

        if self.previouse_state == 'returnback':
            backtocountryafterfirstsponsor_obj = self.env[
                'housemaidsystem.applicant.backtocountryafterfirstsponsor'].search \
                ([('application_id', '=', self.id)], limit=1)
            self.state = self.previouse_state
            backtocountryafterfirstsponsor_obj.unlink()

    def step_back_from_backtocountry_to_returnback_again_action(self):

        if self.previouse_state == 'returnbackagain':
            backtocountryafterlastsponsor_obj = self.env[
                'housemaidsystem.applicant.backtocountryafterlastsponsor'].search \
                ([('application_id', '=', self.id)], limit=1)
            self.state = self.previouse_state
            backtocountryafterlastsponsor_obj.unlink()

    # ---------------Compute ---------------------------

    @api.depends('office_code', 'full_name')
    def _compute_name(self):
        for rec in self:
            self.name = rec.external_office_id + ' : ' + rec.full_name.upper()

    # ---------------On Change ---------------------------

    @api.onchange('birth_date')
    def onchange_getage_id(self):
        for rec in self:
            if rec.birth_date:
                now = fields.Date.today()
                rec.age = (now.year - rec.birth_date.year)
            else:
                rec.age = 0

    @api.onchange('office_code')
    def onchange_office_code(self):
        for rec in self:
            if rec.office_code:
                self.currency_id = rec.office_code.journal.currency_id
                self.office_commission = rec.office_code.commission

    # ---------------Validate---------------------------

    # @api.constrains('passport_issue_date', 'passport_expiry_date')
    # def _validate_passportdates(self):
    #     for rec in self:
    #         if rec.passport_issue_date >= rec.passport_expiry_date:
    #             raise ValidationError("Passport issue date is wrong")

    _sql_constraints = [
        ('ex_office_id_uniqe', 'unique (external_office_id)', "External Office ID exists !")
    ]

    # ---------------Create / Write / unlink ---------------------------

    @api.model
    def create(self, vals):
        external_office = self.env['housemaidsystem.configuration.externaloffices'].browse(vals.get('office_code'))
        if external_office:
            vals['currency_id'] = external_office.journal.currency_id.id

            new_external_office_id = vals['external_office_id'] if vals['external_office_id'] else ''
            if new_external_office_id != '':
                if not str(new_external_office_id).startswith(external_office.code):
                    raise ValidationError(_("Housemaid code %s is not match with office code %s")
                                          % (new_external_office_id, external_office.code))

        # ======================================================================
        # Check dynamic validations
        passport_expiry_years = 0
        branch_office_required = False

        self._cr.execute(""" SELECT passport_expiry_years, branch_office_required 
        FROM housemaidsystem_configuration_settings """)

        for result in self._cr.fetchall():
            passport_expiry_years = result[0] if result[0] else 0
            branch_office_required = result[1] if result[1] else False

        if vals['passport_expiry_date']:
            if fields.Datetime.from_string(vals['passport_expiry_date']) < fields.datetime.now():
                raise ValidationError("Passport is expired.")
            else:
                if passport_expiry_years != 0:
                    days_count = fields.Datetime.from_string(
                        vals['passport_expiry_date']).day - fields.datetime.now().day
                    if days_count < passport_expiry_years * 365:
                        raise ValidationError("Passport will be expired after %i days, as per "
                                              "system validation it should be %i years minmum." % (
                                                  days_count, passport_expiry_years))

        if branch_office_required:
            if not vals['officebranches']:
                raise ValidationError("Sales Office is missing.")

        # ======================================================================
        applications_obj = super(applications, self).create(vals)
        return applications_obj

    def write(self, vals):
        try:
            if vals.get('office_code', False):
                raise ValidationError(
                    "Changing application external office is not allowed, "
                    "delete this record and enter it again.")

            # ==============================================================
            # Dynamic Validation
            passport_expiry_years = 0
            branch_office_required = False

            self._cr.execute(""" SELECT passport_expiry_years, branch_office_required 
            FROM housemaidsystem_configuration_settings """)

            for result in self._cr.fetchall():
                passport_expiry_years = result[0] if result[0] else 0
                branch_office_required = result[1] if result[1] else False

            if vals.get('passport_expiry_date', False):
                if fields.Datetime.from_string(vals.get('passport_expiry_date', False)) < fields.datetime.now():
                    raise ValidationError("Passport is expired.")
                else:
                    if passport_expiry_years != 0:
                        days_count = fields.Datetime.from_string(
                            vals.get('passport_expiry_date', False)).day - fields.datetime.now().day
                        if days_count < passport_expiry_years * 365:
                            raise ValidationError(
                                "Passport will be expired after %i days, as per "
                                "system validation it should be %i years minmum." % (
                                    days_count, passport_expiry_years))

            # if self.officebranches
            # if vals.get('officebranches', False):
            #
            #     if branch_office_required:
            #         if not vals.get('officebranches', False):
            #             raise ValidationError("Sales Office is missing.")
            # ==============================================================

            res = super(applications, self).write(vals)
            return res
        except Exception as e:
            logger.exception("Application Write Method")
            raise ValidationError(e)

    def unlink(self):
        for rec in self:
            if not rec.state in ['application', 'canceledapplication']:
                raise ValidationError(_("Application can not delete, invalid status."))
        return super(applications, self).unlink()

    def get_application_details_report_values(self, record_type):
        docargs = []
        has_records = 0
        if record_type == 'reservation':
            reservations = self.env['housemaidsystem.applicant.reservations'].search([('application_id', '=', self.id)],
                                                                                     limit=1)
            reservations_lines = []
            for reservation in reservations:
                res = {
                    'reservation_date': reservation.reservation_date,
                    'sponsor': reservation.customer_id.name_ar if reservation.customer_id.name_ar else reservation.customer_id.name,
                    'sponsor_mobile': reservation.customer_id.mobile,
                    'sponsor_mobile2': reservation.customer_id.mobile2,
                    'sponsor_tel': reservation.customer_id.phone,
                    'sponsor_civilid': reservation.customer_id.civil_id,
                    'sponsor_address': reservation.customer_id.street2,
                    'deal_amount': reservation.deal_amount,
                    'down_payment_amount': reservation.down_payment_amount,
                    'remain_amount': reservation.deal_amount - (
                        reservation.down_payment_amount if reservation.down_payment_amount else 0.0),
                }
                reservations_lines.append(res)
            docargs = reservations_lines

        if record_type == 'expectedarrival':
            expectedarrival = self.env['housemaidsystem.applicant.expectedarrival'].search(
                [('application_id', '=', self.id)], limit=1)
            expectedarrival_lines = []
            for myexpectedarrival in expectedarrival:
                res = {
                    'expected_arrival_date': myexpectedarrival.expected_arrival_date,
                }
                expectedarrival_lines.append(res)
                docargs = expectedarrival_lines

        if record_type == 'arrival':
            arrival = self.env['housemaidsystem.applicant.arrival'].search([('application_id', '=', self.id)], limit=1)
            arrival_lines = []
            for myarrival in arrival:

                if arrival.arrival_date:
                    elapsed_timedelta = fields.datetime.now() - fields.Datetime.from_string(arrival.arrival_date)
                    arrival_days = elapsed_timedelta.days
                    if arrival_days < 180:
                        arrival_warantly = 'YES'
                    else:
                        arrival_warantly = 'NO'
                else:
                    arrival_days = 0
                    arrival_warantly = 'NO'

                res = {
                    'arrival_date': myarrival.arrival_date,
                    'arrival_days': arrival_days,
                    'arrival_warantly': arrival_warantly,
                }
                arrival_lines.append(res)
                docargs = arrival_lines

        if record_type == 'visa':
            visa = self.env['housemaidsystem.applicant.visa'].search([('application_id', '=', self.id)], limit=1)
            visa_lines = []

            for myvisa in visa:
                if myvisa.visa_issue_date:
                    elapsed_timedelta = fields.datetime.now() - fields.Datetime.from_string(myvisa.visa_issue_date)
                    visa_days = elapsed_timedelta.days
                    if visa_days < 180:
                        visa_warantly = 'YES'
                    else:
                        visa_warantly = 'NO'
                else:
                    visa_days = 0
                    visa_warantly = 'NO'
                res = {
                    'transaction_date': myvisa.transaction_date,
                    'visa_no': myvisa.visa_no,
                    'unified_no': myvisa.unified_no,
                    'visa_issue_date': myvisa.visa_issue_date,
                    'visa_exp_date': myvisa.visa_exp_date,
                    'visa_rec_date': myvisa.visa_rec_date,
                    'visa_snd_date': myvisa.visa_snd_date,
                    'visa_days': visa_days,
                    'visa_warantly': visa_warantly,
                }
                visa_lines.append(res)
                docargs = visa_lines

        if record_type == 'deliver':
            deliver = self.env['housemaidsystem.applicant.deliver'].search([('application_id', '=', self.id)], limit=1)
            deliver_lines = []
            for mydeliver in deliver:
                res = {
                    'deliver_date': mydeliver.deliver_date,
                    'sponsor': mydeliver.customer_id.name_ar if mydeliver.customer_id.name_ar else mydeliver.customer_id.name,
                    'sponsor_mobile': mydeliver.customer_id.mobile,
                    'sponsor_mobile2': mydeliver.customer_id.mobile2,
                    'sponsor_tel': mydeliver.customer_id.phone,
                    'sponsor_civilid': mydeliver.customer_id.civil_id,
                    'sponsor_address': mydeliver.customer_id.street2,
                    'deal_amount': mydeliver.invoice_total,
                    'paid_amount': mydeliver.paid_amount,
                    'discount_amount': mydeliver.discount_amount,
                    'remain_amount': mydeliver.invoice_due,
                }
                deliver_lines.append(res)
                docargs = deliver_lines

        if record_type == 'returnbackfromfirstsponsor':
            returnbackfromfirstsponsor = self.env['housemaidsystem.applicant.returnbackfromfirstsponsor'].search(
                [('application_id', '=', self.id)], limit=1)
            returnbackfromfirstsponsor_lines = []
            for my_returnbackfromfirstsponsor in returnbackfromfirstsponsor:
                res = {
                    'returnbackfromfirstsponsor_date': my_returnbackfromfirstsponsor.return_date,
                    'sponsor': my_returnbackfromfirstsponsor.customer_id.name_ar if my_returnbackfromfirstsponsor.customer_id.name_ar else my_returnbackfromfirstsponsor.customer_id.name,
                    'sponsor_mobile': my_returnbackfromfirstsponsor.customer_id.mobile,
                    'sponsor_mobile2': my_returnbackfromfirstsponsor.customer_id.mobile2,
                    'sponsor_tel': my_returnbackfromfirstsponsor.customer_id.phone,
                    'sponsor_civilid': my_returnbackfromfirstsponsor.customer_id.civil_id,
                    'sponsor_address': my_returnbackfromfirstsponsor.customer_id.street2,
                    'deal_amount': my_returnbackfromfirstsponsor.invoice_total,
                    'paid_amount': my_returnbackfromfirstsponsor.refund_amount,
                    'discount_amount': 0.0,
                    'remain_amount': 0.0,
                }
                returnbackfromfirstsponsor_lines.append(res)
                docargs = returnbackfromfirstsponsor_lines

        if record_type == 'returnbackfromlastsponsor':
            returnbackfromlastsponsor = self.env['housemaidsystem.applicant.returnbackfromlastsponsor'].search(
                [('application_id', '=', self.id)], limit=1)
            returnbackfromlastsponsor_lines = []
            for my_returnbackfromlastsponsor in returnbackfromlastsponsor:
                res = {
                    'returnbackfromlastsponsor_date': my_returnbackfromlastsponsor.return_date,
                    'sponsor': my_returnbackfromlastsponsor.old_customer_id.name_ar if my_returnbackfromlastsponsor.old_customer_id.name_ar else my_returnbackfromlastsponsor.old_customer_id.name,
                    'sponsor_mobile': my_returnbackfromlastsponsor.old_customer_id.mobile,
                    'sponsor_mobile2': my_returnbackfromlastsponsor.old_customer_id.mobile2,
                    'sponsor_tel': my_returnbackfromlastsponsor.old_customer_id.phone,
                    'sponsor_civilid': my_returnbackfromlastsponsor.old_customer_id.civil_id,
                    'sponsor_address': my_returnbackfromlastsponsor.old_customer_id.street2,
                    'deal_amount': my_returnbackfromlastsponsor.paid_by_sponsor,
                    'paid_amount': my_returnbackfromlastsponsor.refund_amount,
                    'discount_amount': 0.0,
                    'remain_amount': 0.0,
                }
                returnbackfromlastsponsor_lines.append(res)
                docargs = returnbackfromlastsponsor_lines

        if record_type == 'sellastest':
            selltest = self.env['housemaidsystem.applicant.selltest'].search([('application_id', '=', self.id)],
                                                                             limit=100)
            selltest_lines = []
            for myselltest in selltest:
                if myselltest.test_status == 'selectaction':
                    res = {
                        'action': 'Sell As test',
                        'test_date': myselltest.test_date,
                        'sponsor': myselltest.new_customer_id.name_ar if myselltest.new_customer_id.name_ar else myselltest.new_customer_id.name,
                        'selltest_action': "",
                        'sponsor_mobile': myselltest.new_customer_id.mobile,
                        'sponsor_mobile2': myselltest.new_customer_id.mobile2,
                        'sponsor_civilid': myselltest.new_customer_id.civil_id,
                        'sponsor_address': myselltest.new_customer_id.street2,
                        'deal_amount': myselltest.deal_amount,
                        'paid_amount': myselltest.down_payment_amount,
                        'discount_amount': myselltest.sepecial_discount_amount,
                        'remain_amount': myselltest.deal_amount - (
                            myselltest.down_payment_amount if myselltest.down_payment_amount else 0.0),
                    }
                    selltest_lines.append(res)
                docargs = selltest_lines
                if myselltest.test_status == 'accepted':
                    res = {
                        'action': 'Test Accepted',
                        'test_date': myselltest.accept_date,
                        'sponsor': myselltest.new_customer_id.name_ar if myselltest.new_customer_id.name_ar else myselltest.new_customer_id.name,
                        'sponsor_mobile': myselltest.new_customer_id.mobile,
                        'sponsor_mobile2': myselltest.new_customer_id.mobile2,
                        'sponsor_civilid': myselltest.new_customer_id.civil_id,
                        'sponsor_address': myselltest.new_customer_id.street2,
                        'deal_amount': myselltest.deal_amount,
                        'paid_amount': myselltest.complete_payment_amount + myselltest.down_payment_amount,
                        'discount_amount': myselltest.sepecial_discount_amount,
                        'remain_amount': 0,
                    }
                    selltest_lines.append(res)
                docargs = selltest_lines
                if myselltest.test_status == 'rejected':
                    res = {
                        'action': 'Test Rejected',
                        'test_date': myselltest.reject_date,
                        'sponsor': myselltest.new_customer_id.name_ar if myselltest.new_customer_id.name_ar else myselltest.new_customer_id.name,
                        'sponsor_mobile': myselltest.new_customer_id.mobile,
                        'sponsor_mobile2': myselltest.new_customer_id.mobile2,
                        'sponsor_civilid': myselltest.new_customer_id.civil_id,
                        'sponsor_address': myselltest.new_customer_id.street2,
                        'deal_amount': myselltest.deal_amount,
                        'paid_amount': myselltest.down_payment_amount,
                        'discount_amount': 0,
                        'remain_amount': 0,
                    }
                    selltest_lines.append(res)
                docargs = selltest_lines

        return docargs
