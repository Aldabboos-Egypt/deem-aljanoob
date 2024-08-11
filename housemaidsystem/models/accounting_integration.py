from odoo import fields
from datetime import datetime
from odoo import _
from odoo.exceptions import ValidationError
import datetime
import logging
from num2words import num2words
import json
import requests

logger = logging.getLogger(__name__)


# =========================================== MAIN FUNCTIONS ============================================================
def convert_amount_to_word(amount):
    try:
        convert_amount_to_word = ''
        if amount == 0:
            convert_amount_to_word = 'Zero Dinar Kuwaiti'
        else:
            amt_integer = int(amount)
            amt_decimal = (amount - amt_integer) * 1000

            if amt_integer > 0:
                convert_amount_to_word = num2words(amt_integer, lang='en').title() + ' Dinar Kuwaiti'

            if amt_decimal > 0:
                convert_amount_to_word += ' And ' + num2words(amt_decimal, lang='en').title() + ' Fils'

        return convert_amount_to_word
    except Exception as e:
        logger.exception("convert_amount_to_word Method")
        raise ValidationError(e)


def get_setup(self, field_name):
    try:
        sql = 'SELECT %s FROM housemaidsystem_configuration_settings' % (field_name)
        return_value = 0
        self._cr.execute(sql)
        for result in self._cr.fetchall():
            return_value = result[0] if result[0] else 0

        return return_value
    except Exception as e:
        logger.exception("get_setup")
        raise ValidationError(e)


def get_payment_account_id(self, journal_id, account_type='debit'):
    try:
        journal = self.env['account.journal']. \
            search([('id', '=', journal_id)], limit=1)
        if journal and account_type == 'debit':
            account = journal.payment_debit_account_id.id
        else:
            account = journal.payment_credit_account_id.id
        return account
    except Exception as e:
        logger.exception("get_payment_account_id method")
        raise ValidationError(e)


def get_application_branch(self, application_obj):
    office_branch_obj = self.env['housemaidsystem.configuration.officebranches']. \
        search([('id', '=', application_obj.officebranches.id)], limit=1)
    return office_branch_obj


def get_sales_invoice_header(application_obj):
    invoice_header = application_obj.external_office_id + ':' + application_obj.full_name
    return invoice_header


def get_sales_invoice_details(application_obj):
    invoice_details = application_obj.external_office_id + ':' + application_obj.full_name
    return invoice_details


def get_purchase_invoice_header(application_obj):
    invoice_header = application_obj.external_office_id + ':' + application_obj.full_name
    return invoice_header


def get_purchase_invoice_details(application_obj):
    invoice_details = application_obj.external_office_id + ':' + application_obj.full_name
    return invoice_details


def get_commision_currency(self, externaloffices_obj):
    office_main_account = self.env['account.account']. \
        search([('id', '=', externaloffices_obj.account.id)], limit=1)
    return office_main_account.currency_id.id


def housemaid_sales_service(self):
    product_obj = self.env['product.product'].search([('name', '=', 'Housemaid Sales')], limit=1)
    if not product_obj:
        product_obj = self.env['product.product'].create({
            'name': 'Housemaid Sales',
            'sale_ok': True,
            'purchase_ok': False,
            'type': 'service',
            'default_code': False,
            'barcode': False,
            'lst_price': 1.0,
            'standard_price': 0.0,
        })
    return product_obj


def housemaid_purchase_service(self):
    product_obj = self.env['product.product'].search([('name', '=', 'Housemaid Purchases')], limit=1)
    if not product_obj:
        product_obj = self.env['product.product'].create({
            'name': 'Housemaid Purchases',
            'sale_ok': False,
            'purchase_ok': True,
            'type': 'service',
            'default_code': False,
            'barcode': False,
            'lst_price': 1.0,
            'standard_price': 0.0,
        })
    return product_obj


def update_cost_center_for_invoice(self, invoice_sales_obj, application_obj):
    account_move_line_sales_obj = self.env['account.move.line'].search([('move_id', '=', invoice_sales_obj.move_id.id)])
    office_branch_obj = get_application_branch(self, application_obj)
    for rec in account_move_line_sales_obj:
        rec.office_branch = office_branch_obj.id if office_branch_obj.id else 0
        rec.application_id = application_obj.id if application_obj.id else 0


def update_cost_center_for_sales_payment(self, sales_payment_obj, application_obj):
    account_move_line_payment = self.env['account.move.line'].search([('payment_id', '=', sales_payment_obj.id)])
    office_branch_obj = get_application_branch(self, application_obj)
    for rec in account_move_line_payment:
        rec.office_branch = office_branch_obj.id if office_branch_obj.id else 0
        rec.application_id = application_obj.id if application_obj.id else 0


def get_amt_eq(self, eq_amount, currency_id):
    try:
        currency_obj = self.env['res.currency']. \
            search([('id', '=', currency_id)], limit=1)
        date = fields.Date.today()
        rate = currency_obj.with_context(date=date).rate
        amount_eq = round(eq_amount / rate if rate > 0 else 1, currency_id)
        return amount_eq
    except Exception as e:
        logger.exception("get_kwd_eq Method")
        raise ValidationError(e)


def NOT_USED_get_default_debit_account_from_journal(self, journal_id):
    try:
        journal_obj = self.env['account.journal'].search(
            [('id', '=', journal_id)], limit=1)
        return journal_obj.default_debit_account_id.id
    except Exception as e:
        logger.exception("get_default_debit_account_from_journal Method")
        raise ValidationError(e)


def NOT_USE_add_sponsor_payment(self, object_name, payment_type):
    try:
        application_obj = customer_obj = move_obj = payment_obj = invoice_obj = None
        sposnor_payment = sposnor_total = sposnor_dues = sposnor_previous_paid = sposnor_discount = 0
        payment_ref = payment_reason = amount_to_string = payment_type_str = invoice_ref = payment_prepared_by = ''

        state = 'confirmed'

        officebranches_obj = self.env['housemaidsystem.configuration.officebranches']. \
            search([('id', '=', self.application_id.officebranches.id)], limit=1)

        sponsor_payment_obj = self.env['housemaidsystem.sponsorpayments']

        if object_name == 'reservation':
            if payment_type == 'Payment':

                if self.paid_immediately is False:
                    self.down_payment_invoice.cancel()

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = self.down_payment_amount if self.down_payment_amount > 0 else 0
                payment_ref = self.down_payment_invoice.display_name
                invoice_ref = self.invoice_sales_id.name
                payment_reason = 'New reservation (Down Payment) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(
                    self.down_payment_amount if self.down_payment_amount > 0 else 0)
                sposnor_total = self.invoice_sales_id.amount_total
                sposnor_dues = ((self.invoice_sales_id.amount_total if self.invoice_sales_id.amount_total > 0 else 0) -
                                (self.down_payment_invoice.amount if self.down_payment_invoice.amount > 0 else 0))
                sposnor_previous_paid = 0
                sposnor_discount = 0
                payment_prepared_by = self.sales_man.partner_id.name
                state = 'draft' if self.paid_immediately is False else 'confirmed'
                move_obj = self.paid_immediately_move
                payment_obj = self.down_payment_invoice
                invoice_obj = self.invoice_sales_id

            if payment_type == 'Refund':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                application_obj = self.application_id
                payment_reason = 'Cancel reservation (Refund Down Payment) For ' + get_sales_invoice_header(
                    application_obj)

                new_payment = create_reversed_sponsor_payment(self, self.down_payment_invoice.id, object_name,
                                                              payment_reason)

                payment_type_str = payment_type
                customer_obj = self.customer_id
                sposnor_payment = self.down_payment_amount if self.down_payment_amount > 0 else 0
                payment_ref = new_payment.name
                invoice_ref = sponsorpayments_obj.invoice_ref
                amount_to_string = convert_amount_to_word(
                    self.down_payment_amount if self.down_payment_amount > 0 else 0)
                sposnor_total = self.invoice_sales_id.amount_total
                sposnor_dues = 0
                sposnor_discount = 0
                sposnor_previous_paid = self.down_payment_amount
                payment_prepared_by = self.sales_man.partner_id.name
                state = 'draft'
                move_obj = sponsorpayments_obj.move_obj if sponsorpayments_obj.move_obj else None
                payment_obj = new_payment
                invoice_obj = sponsorpayments_obj.invoice_obj if sponsorpayments_obj.invoice_obj else None

                new_payment.action_cancel()


        elif object_name == 'resell':
            if payment_type == 'Refund':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                application_obj = self.application_id
                payment_reason = 'Re-Sell Housemaid before deliver to first sponsor (Refund Down Payment) - For ' + get_sales_invoice_header(
                    application_obj)

                reservation_obj = self.env['housemaidsystem.applicant.reservations']. \
                    search([('application_id', '=', self.application_id.id)], limit=1)

                new_payment = create_reversed_sponsor_payment(self, reservation_obj.down_payment_invoice.id,
                                                              object_name,
                                                              payment_reason)

                payment_type_str = payment_type
                customer_obj = self.customer_id
                sposnor_payment = sponsorpayments_obj.sposnor_payment
                payment_ref = new_payment.name
                invoice_ref = sponsorpayments_obj.invoice_ref
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = sponsorpayments_obj.sposnor_total
                sposnor_dues = 0
                sposnor_discount = 0.0
                sposnor_previous_paid = sponsorpayments_obj.sposnor_payment
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'draft' if self.paid_immediately is False else 'confirmed'
                move_obj = sponsorpayments_obj.move_obj if sponsorpayments_obj.move_obj else None
                payment_obj = new_payment
                invoice_obj = sponsorpayments_obj.invoice_obj if sponsorpayments_obj.invoice_obj else None

                new_payment.action_cancel()

        elif object_name == 'deliverpaidfull':
            if payment_type == 'Payment':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = self.paid_amount
                payment_ref = self.paid_payment_invoice.display_name
                invoice_ref = sponsorpayments_obj.invoice_ref
                payment_reason = 'New Deliver (Paid Full) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(self.paid_amount)
                sposnor_total = sponsorpayments_obj.sposnor_total
                sposnor_dues = 0
                sposnor_discount = self.discount_amount if self.discount_amount > 0 else 0.0
                sposnor_previous_paid = sponsorpayments_obj.sposnor_payment
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'
                move_obj = None
                payment_obj = self.paid_payment_invoice
                invoice_obj = sponsorpayments_obj.invoice_obj if sponsorpayments_obj.invoice_obj else None

            if payment_type == 'Refund':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                orig_move_obj = self.env['account.move'].search([('name', '=', sponsorpayments_obj.payment_ref)],
                                                                limit=1)
                reversed_move_obj = self.env['account.move'].search(
                    [('id', '=', orig_move_obj.reverse_entry_id.id)], limit=1)

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = sponsorpayments_obj.sposnor_payment
                payment_ref = reversed_move_obj.name
                invoice_ref = sponsorpayments_obj.invoice_ref
                payment_reason = 'Cancel Deliver (Paid Full) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(self.paid_amount)
                sposnor_total = sponsorpayments_obj.sposnor_total
                sposnor_dues = self.invoice_due
                sposnor_discount = self.discount_amount if self.discount_amount > 0 else 0.0
                sposnor_previous_paid = sponsorpayments_obj.sposnor_payment
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'


        elif object_name == 'deliverpaidpartial':
            if payment_type == 'Payment':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = self.paid_amount
                payment_ref = self.paid_payment_invoice.display_name
                invoice_ref = sponsorpayments_obj.invoice_ref
                payment_reason = 'New Deliver (Paid Partial) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(self.paid_amount)
                sposnor_total = sponsorpayments_obj.sposnor_total
                sposnor_dues = self.invoice_due
                sposnor_discount = 0
                sposnor_previous_paid = sponsorpayments_obj.sposnor_payment
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'

            if payment_type == 'Refund':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                orig_move_obj = self.env['account.move'].search([('name', '=', sponsorpayments_obj.payment_ref)],
                                                                limit=1)
                reversed_move_obj = self.env['account.move'].search(
                    [('id', '=', orig_move_obj.reverse_entry_id.id)], limit=1)

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = sponsorpayments_obj.sposnor_payment
                payment_ref = reversed_move_obj.name
                invoice_ref = sponsorpayments_obj.invoice_ref
                payment_reason = 'Cancel Deliver (Paid Partial) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(self.paid_amount)
                sposnor_total = sponsorpayments_obj.sposnor_total
                sposnor_dues = self.invoice_due
                sposnor_discount = self.discount_amount if self.discount_amount > 0 else 0.0
                sposnor_previous_paid = sponsorpayments_obj.sposnor_payment
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'

        elif object_name == 'deliverpaidfullafterpartial':
            if payment_type == 'Payment':
                sponsorpayments_obj = self.env['housemaidsystem.sponsorpayments']. \
                    search([('application_id', '=', self.application_id.id),
                            ('customer_id', '=', self.customer_id.id),
                            ('payment_type', '=', 'Payment')], order='id desc', limit=1)

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = sponsorpayments_obj.sposnor_dues
                payment_ref = self.paid_payment_invoice.display_name
                invoice_ref = sponsorpayments_obj.invoice_ref
                payment_reason = 'New Deliver (Paid Remain Amount) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = sponsorpayments_obj.sposnor_total
                sposnor_dues = 0
                sposnor_discount = 0
                sposnor_previous_paid = sponsorpayments_obj.sposnor_payment
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'

        elif object_name == 'returnback':

            if payment_type == 'Payment':
                # Salary
                if self.paid_immediately is False:
                    self.hm_salary_move.button_cancel()

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = self.hm_salary
                payment_ref = self.hm_salary_move.name
                invoice_ref = self.invoice_id.number
                payment_reason = 'Return Back From First Sponsor (Salary Payment) For ' + get_sales_invoice_header(
                    application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.invoice_total
                sposnor_dues = 0
                sposnor_discount = 0
                sposnor_previous_paid = self.invoice_total
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'draft' if self.paid_immediately is False else 'confirmed'
                move_obj = self.hm_salary_move
                payment_obj = None
                invoice_obj = None

            if payment_type == 'Refund':
                # Down Payment
                if self.paid_immediately is False:
                    self.refund_payment_invoice.action_cancel()

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.customer_id
                sposnor_payment = self.refund_amount
                payment_ref = self.refund_payment_invoice.display_name
                invoice_ref = self.invoice_id.number
                payment_reason = 'Return Back From First Sponsor (Refund Payment) For ' + get_sales_invoice_header(
                    application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.invoice_total
                sposnor_dues = 0
                sposnor_discount = 0
                sposnor_previous_paid = self.invoice_total
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'draft' if self.paid_immediately is False else 'confirmed'
                move_obj = None
                payment_obj = self.refund_payment_invoice
                invoice_obj = None


        elif object_name == 'sellastest':
            if payment_type == 'Payment':
                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.new_customer_id
                sposnor_payment = self.down_payment_amount
                payment_ref = self.down_payment_invoice.display_name
                invoice_ref = self.new_invoice_id.name
                payment_reason = 'Sell As Test (Down Payment) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.new_invoice_id.amount_total
                sposnor_dues = self.new_invoice_id.amount_residual
                sposnor_discount = 0
                sposnor_previous_paid = 0
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'
                move_obj = None
                payment_obj = self.down_payment_invoice
                invoice_obj = self.new_invoice_id

            if payment_type == 'Refund':
                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.new_customer_id
                sposnor_payment = self.rejection_refund_amount
                payment_ref = self.rejection_refund_amount_payment.display_name
                invoice_ref = self.new_invoice_id.name
                payment_reason = 'Sell As Test (Refund Down Payment) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.new_invoice_id.amount_total
                sposnor_dues = self.new_invoice_id.amount_residual
                sposnor_discount = 0
                sposnor_previous_paid = 0
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'
                move_obj = None
                payment_obj = self.rejection_refund_amount_payment
                invoice_obj = self.new_invoice_id

        elif object_name == 'sellastest_accept':

            if payment_type == 'Payment':
                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.new_customer_id
                sposnor_payment = self.complete_payment_amount
                payment_ref = self.complete_payment_invoice.display_name
                invoice_ref = self.new_invoice_id.name
                payment_reason = 'Sell As Test (Remain Amount) For ' + get_sales_invoice_header(application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.new_invoice_id.amount_total
                sposnor_dues = 0
                sposnor_discount = self.sepecial_discount_amount
                sposnor_previous_paid = self.down_payment_amount
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'
                payment_obj = self.complete_payment_invoice
                invoice_obj = self.new_invoice_id


        elif object_name == 'sellastest_reject':

            if payment_type == 'Payment':
                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.new_customer_id
                sposnor_payment = self.hm_salary
                payment_ref = self.hm_salary_move.name
                invoice_ref = self.new_invoice_id.name
                payment_reason = 'Sell As Test Rejection (Salary Payment) For ' + get_sales_invoice_header(
                    application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.new_invoice_id.amount_total
                sposnor_dues = 0
                sposnor_discount = self.sepecial_discount_amount
                sposnor_previous_paid = self.down_payment_amount
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'confirmed'


        elif object_name == 'returnbackagain':

            if payment_type == 'Payment':
                # Salary
                if self.paid_immediately is False:
                    self.hm_salary_move.button_cancel()

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.old_customer_id
                sposnor_payment = self.hm_salary
                payment_ref = self.hm_salary_move.name
                invoice_ref = self.old_invoice_id.number
                payment_reason = 'Return Back From Sponsor (Salary Payment) For ' + get_sales_invoice_header(
                    application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.old_invoice_total
                sposnor_dues = 0
                sposnor_discount = 0
                sposnor_previous_paid = self.old_invoice_total
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'draft' if self.paid_immediately is False else 'confirmed'
                move_obj = self.hm_salary_move
                payment_obj = None
                invoice_obj = self.old_invoice_id

            if payment_type == 'Refund':
                # Down Payment
                if self.paid_immediately is False:
                    self.refund_payment_invoice.action_cancel()

                payment_type_str = payment_type
                application_obj = self.application_id
                customer_obj = self.old_customer_id
                sposnor_payment = self.refund_amount
                payment_ref = self.resell_move_id.name
                invoice_ref = self.old_invoice_id.number
                payment_reason = 'Return Back From Sponsor (Refund Payment) For ' + get_sales_invoice_header(
                    application_obj)
                amount_to_string = convert_amount_to_word(sposnor_payment)
                sposnor_total = self.old_invoice_total
                sposnor_dues = 0
                sposnor_discount = 0
                sposnor_previous_paid = self.old_invoice_total
                payment_prepared_by = self.create_uid.partner_id.name
                state = 'draft' if self.paid_immediately is False else 'confirmed'
                move_obj = None
                payment_obj = self.refund_payment_invoice
                invoice_obj = self.old_invoice_id

        new_payment = post_sponsor_payment(self, sponsor_payment_obj, officebranches_obj, application_obj, customer_obj,
                                           sposnor_payment,
                                           payment_ref, invoice_ref, payment_reason, amount_to_string,
                                           sposnor_total, sposnor_dues, sposnor_discount, sposnor_previous_paid,
                                           payment_type_str, payment_prepared_by, state, move_obj, payment_obj,
                                           invoice_obj)

        return new_payment
    except Exception as e:
        logger.exception("add_sponsor_payment Method")
        raise ValidationError(e)


def post_sponsor_payment(self, sponsor_payment_obj, officebranches_obj, application_obj, customer_obj, sposnor_payment,
                         payment_ref, invoice_ref, payment_reason, amount_to_string,
                         sposnor_total, sposnor_dues, sposnor_discount, sposnor_previous_paid, payment_type_str,
                         payment_prepared_by, state, move_obj, payment_obj, invoice_obj):
    try:

        new_payment = sponsor_payment_obj.create({
            'OfficeBranches': officebranches_obj.id,
            'application_id': application_obj.id,
            'customer_id': customer_obj.id,
            'sposnor_payment_dt': datetime.datetime.now(),
            'sposnor_payment': sposnor_payment,
            'payment_ref': payment_ref,
            'invoice_ref': invoice_ref,
            'payment_reason': payment_reason,
            'convert_amount_to_word': amount_to_string,
            'sposnor_total': sposnor_total,
            'sposnor_dues': sposnor_dues,
            'sposnor_discount': sposnor_discount,
            'sposnor_previous_paid': sposnor_previous_paid,
            'payment_type': payment_type_str,
            'payment_prepared_by': payment_prepared_by,
            'app_state': application_obj.state,
            'state': state,
            'move_obj': move_obj.id if move_obj else None,
            'payment_obj': payment_obj.id if payment_obj else None,
            'invoice_obj': invoice_obj.id if invoice_obj else None,
        })
        return new_payment
    except Exception as e:
        logger.exception("post_sponsor_payment Method")
        raise ValidationError(e)


def NOT_USED_post_draft_sponsor_payment(self):
    try:
        payment_refund_str = ''
        canceled_invoice = self.env['account.move'].search([('display_name', '=', self.invoice_ref)], limit=1)

        # if not canceled_invoice:
        #     canceled_invoice = self.env['account.payment'].search([('display_name', '=', self.payment_ref)], limit=1)

        if canceled_invoice:
            if self.app_state == 'reservation' or self.app_state == 'arrival':
                cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') \
                    if get_setup(self, 'direct_journal_arrival_cash') else 0
            else:
                cash_journal_id = get_setup(self, 'return_journal_cash') \
                    if get_setup(self, 'return_journal_cash') else 0

            payment_refund = self.env['account.payment'].create(
                {'payment_type': 'outbound' if self.payment_type == 'Refund' else 'inbound',
                 'partner_type': 'customer',
                 'amount': self.sposnor_payment,
                 # 'communication': self.payment_reason,
                 'currency_id': canceled_invoice.currency_id.id,
                 'journal_id': cash_journal_id,
                 'payment_method_id': self.env.ref(
                     'account.account_payment_method_manual_out').id,
                 # 'destination_journal_id': False,
                 'partner_id': canceled_invoice.partner_id.id})
            payment_refund.action_post()
            payment_refund_str = payment_refund.name

        return payment_refund_str
    except Exception as e:
        logger.exception("Ccreate_sales_invoice_refund_payment Method")
        raise ValidationError(e)


def create_reversed_sponsor_payment(self, payment_id, object_name, payment_reason):
    try:
        payment_refund = None
        cash_journal_id = 0
        original_payment = self.env['account.payment'].search([('id', '=', payment_id)], limit=1)

        if object_name == 'reservation' or object_name == 'resell':
            cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') \
                if get_setup(self, 'direct_journal_arrival_cash') else 0
        else:
            cash_journal_id = get_setup(self, 'return_journal_cash') \
                if get_setup(self, 'return_journal_cash') else 0

        payment_refund = self.env['account.payment'].create(
            {'payment_type': 'outbound' if original_payment.payment_type == 'inbound' else 'inbound',
             'partner_type': 'customer',
             'amount': original_payment.amount,
             'payment_reference': payment_reason,
             'currency_id': original_payment.currency_id.id,
             'journal_id': cash_journal_id,
             'payment_method_id': self.env.ref(
                 'account.account_payment_method_manual_out').id,
             # 'destination_journal_id': False,
             'partner_id': original_payment.partner_id.id})
        payment_refund.action_post()
        return payment_refund
    except Exception as e:
        logger.exception("create_reversed_sponsor_payment Method")
        raise ValidationError(e)


def reverse_move(self, move_id, refund_method, refund_reason):
    try:
        credit_note_wizard = self.env['account.move.reversal'].with_context(
            {'active_ids': move_id.ids, 'active_id': move_id,
             'active_model': 'account.move'}).create({
            'refund_method': refund_method,
            'reason': refund_reason,
        })
        account_move = self.env['account.move'].browse(credit_note_wizard.reverse_moves()['res_id'])
        return account_move
    except Exception as e:
        logger.exception("Reverse Move")
        raise ValidationError(e)


# ======================== SALES INVOICE / PURCHASE INVOICE / PAYMENTS  / MOVEMENT ======================================
def create_sales_invoice(self, journal, acc_deffered_income, invoice_header, deal_amount, customer_id, product_obj, analytic_account=None, analytic_tag=None):

    try:
        inv_obj = self.env['account.move']
        vals = {
            'move_type': 'out_invoice',
            'journal_id': journal,
            'partner_id': customer_id,
            'ref': invoice_header,
            'invoice_line_ids': [(0, 0, {
                'price_unit': deal_amount,
                'quantity': 1.0,
                'discount': 0.0,
                'product_id': product_obj.id,
                'account_id': acc_deffered_income,
                'analytic_account_id': analytic_account.id if analytic_account else False,
                'analytic_tag_ids': [analytic_tag.id] if analytic_tag else False,
            })],
        }
        invoice = inv_obj.create(vals)
        invoice.action_post()

        return invoice
    except Exception as e:
        logger.exception("create_sales_invoice Method")
        raise ValidationError(e)


def create_purchase_invoice(self, invoice_header, purchase_journal_obj, invoice_amount, offset_account, vendor_obj,
                            product_obj,analytic_account=None,analytic_tag=None):
    try:
        invoice_obj = self.env['account.move']
        invoice = invoice_obj.create({
            'move_type': 'in_invoice',
            'journal_id': purchase_journal_obj.id,
            'ref': invoice_header,
            'invoice_date': fields.Date.today(),
            'currency_id': offset_account.currency_id.id,
            'partner_id': vendor_obj.id,
            'invoice_line_ids': [(0, 0, {
                'price_unit': invoice_amount,
                'quantity': 1.0,
                'discount': 0.0,
                'product_id': product_obj.id,
                'analytic_account_id': analytic_account.id if analytic_account else False,
                'analytic_tag_ids': [analytic_tag.id] if analytic_tag else False,
            })],
        })
        invoice.action_post()
        return invoice
    except Exception as e:
        logger.exception("create_purchase_invoice Method")
        raise ValidationError(e)


def NOT_USED_create_sales_invoice_payment(self, amount, invoice_obj, cash_journal_id, partner_id):
    try:
        sales_invoice_payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'amount': amount,
            'payment_reference': invoice_obj.name,
            'currency_id': invoice_obj.currency_id.id,
            'journal_id': cash_journal_id,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'partner_id': partner_id,
        })
        sales_invoice_payment.action_post()
        credit_line_a = sales_invoice_payment.line_ids.filtered(lambda l: l.credit)
        invoice_obj.js_assign_outstanding_line(credit_line_a.id)

        return sales_invoice_payment
    except Exception as e:
        logger.exception("create_sales_invoice_payment Method")
        raise ValidationError(e)


def post_cash_payment(self, amount, payment_reference, partner_id, payment_direction='inbound', memo=None):
    try:
        acc_rec = get_setup(self, 'direct_accounts_receivable') if get_setup(self, 'direct_accounts_receivable') else 0
        journal_cash = get_setup(self, 'return_journal_cash') if get_setup(self, 'return_journal_cash') else 0
        sales_invoice_payment = self.env['account.payment'].create({
            'payment_type': payment_direction,
            'partner_type': 'customer',
            'amount': amount,
            'ref': memo if memo else '',
            'journal_id': journal_cash,
            'destination_account_id': acc_rec,
            'payment_reference': payment_reference,
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'partner_id': partner_id,
        })
        sales_invoice_payment.action_post()
        return sales_invoice_payment
    except Exception as e:
        logger.exception("create_sales_invoice_payment Method")
        raise ValidationError(e)


def create_sales_invoice_payment_with_discount(self, action_name, amount, invoice_obj, journal_id, discount=0.0,
                                               discount_expense_obj=None, payment_difference_handling='open'):
    try:
        memo = 'Down Payment for %s' % (action_name) \
            if payment_difference_handling == 'open' \
            else 'Complete Payment %s' % (action_name)

        account_payment_registered = self.env['account.payment.register'].with_context(active_model='account.move',
                                                                                       dont_redirect_to_payments=True,
                                                                                       active_ids=invoice_obj.ids).create(
            {
                'amount': amount,
                'payment_difference_handling': payment_difference_handling,
                'writeoff_account_id': discount_expense_obj.id if discount_expense_obj else None,
                'writeoff_label': 'Sales Discount for %s' % (action_name) if discount != 0.0 else '',
                'journal_id': journal_id,
            })
        payment = self.env['account.payment']
        if account_payment_registered.action_create_payments():
            line_move = account_payment_registered.line_ids
            matched_credit_ids = line_move.matched_credit_ids
            for matched_credit_id in matched_credit_ids:
                if matched_credit_id.credit_amount_currency == (amount + discount):
                    credit_move_id = matched_credit_id.credit_move_id
                    payment = credit_move_id.payment_id
                    payment.ref = memo

        return payment
    except Exception as e:
        logger.exception("create_sales_invoice_payment Method")
        raise ValidationError(e)


def NOT_USED_create_sales_invoice_pay_and_reconcile(self, action_name, invoice_obj, paid_amount, discount_amount,
                                                    cash_journal_obj, discount_expense_obj, partner_id,
                                                    application_obj):
    # payments = self.env['account.payment.register'].with_context(active_model='account.move',
    #                                                              active_ids=active_ids).create({
    #     'amount': 800.0,
    #     'group_payment': True,
    #     'payment_difference_handling': 'open',
    #     'currency_id': self.currency_data['currency'].id,
    #     'payment_method_id': self.custom_payment_method_in.id,
    # })._create_payments()

    try:
        payment_id = 0
        if discount_amount > 0:
            invoice_obj.pay_and_reconcile(cash_journal_obj, paid_amount, None, discount_expense_obj)
        else:
            invoice_obj.pay_and_reconcile(cash_journal_obj, paid_amount, None, None)

        query = "select max(id) from account_payment where communication = (select number from account_invoice where id = %s)"

        self._cr.execute(query, (invoice_obj.id,))
        for result in self._cr.fetchall():
            payment_id = result[0] if result[0] else 0

        payment_obj = self.env['account.payment'].search([('id', '=', payment_id)], limit=1)
        payment_obj.payment_reference = action_name + get_sales_invoice_header(
            application_obj) + ' ' + payment_obj.payment_reference

        move_lines_obj = self.env['account.move.line'].search([('payment_id', '=', payment_obj.id)], limit=1)
        if move_lines_obj:
            move_obj = self.env['account.move'].search([('id', '=', move_lines_obj.move_id.id)], limit=1)
            if move_obj:
                move_obj.ref = action_name + get_sales_invoice_header(application_obj) + ' ' + move_obj.ref

        return payment_obj
    except Exception as e:
        logger.exception("create_sales_invoice_pay_and_reconcile Method")
        raise ValidationError(e)


def create_sales_invoice_refund_payment(self, amount, communication, cash_journal_id, partner_id, memo=None):
    try:
        payment_refund = self.env['account.payment'].create({'payment_type': 'outbound',
                                                             'partner_type': 'customer',
                                                             'amount': amount,
                                                             'payment_reference': communication,
                                                             'ref': memo if memo else '',
                                                             'journal_id': cash_journal_id,
                                                             'payment_method_id': self.env.ref(
                                                                 'account.account_payment_method_manual_out').id,
                                                             'partner_id': partner_id})
        payment_refund.action_post()
        return payment_refund
    except Exception as e:
        logger.exception("create_sales_invoice_refund_payment Method")
        raise ValidationError(e)


def create_account_move_single(self, journal_id, move_header, partner_id, amount, debit_account, credit_account,
                               move_ref, partner_id_2=None):
    try:
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal_id,
            'line_ids': [(0, 0, {
                'name': move_header if move_header else None,
                'partner_id': partner_id if partner_id else None,
                'debit': amount if amount else 0.0,
                'account_id': debit_account if debit_account else None,
                'ref': move_ref if move_ref else None,
            }), (0, 0, {
                'name': move_header if move_header else None,
                'partner_id': partner_id_2 if partner_id_2 else partner_id,
                'credit': amount if amount else 0.0,
                'account_id': credit_account if credit_account else None,
            })]
        })
        move.action_post()
        return move
    except Exception as e:
        logger.exception("create_account_move Method")
        raise ValidationError(e)


def create_account_move_dr_cr_single(self, journal_id, partner_id, amount, debit_account, credit_account, move_ref):
    try:
        move = self.env['account.move'].create({
            'journal_id': journal_id,
            'ref': move_ref if move_ref else None,
            'line_ids': [(0, 0, {
                'partner_id': partner_id if partner_id else None,
                'debit': amount if amount else 0.0,
                'account_id': debit_account if debit_account else None,
            }), (0, 0, {
                'partner_id': partner_id if partner_id else None,
                'credit': amount if amount else 0.0,
                'account_id': credit_account if credit_account else None,
            })]
        })
        move.action_post()
        return move
    except Exception as e:
        logger.exception("create_account_move_dr_cr_single Method")
        raise ValidationError(e)


def create_account_move_with_currency(self, journal_id, move_header, partner_id, amount, debit_account, credit_account,
                                      move_ref, application_id, officebranches_id):
    try:
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal_id,
            'line_ids': [(0, 0, {
                'name': move_header if move_header else None,
                'partner_id': partner_id if partner_id else None,
                'debit': amount if amount else 0.0,
                'account_id': debit_account if debit_account else None,
                'ref': move_ref if move_ref else None,
                'application_id': application_id if application_id else None,
                'office_branch': officebranches_id if officebranches_id else None,
            }), (0, 0, {
                'name': move_header if move_header else None,
                'partner_id': partner_id if partner_id else None,
                'credit': amount if amount else 0.0,
                'account_id': credit_account if credit_account else None,
                'application_id': application_id if application_id else None,
                'office_branch': officebranches_id if officebranches_id else None,
            })]
        })
        move.action_post()
        return move
    except Exception as e:
        logger.exception("create_account_move Method")
        raise ValidationError(e)


def create_account_move_dr_cr_with_currency(self, journal_id, move_type, partner_id, amount, debit_account,
                                            credit_account, move_ref, currency_id, amount_currency):
    try:
        # move_type =>> entry / out_invoice / in_invoice
        move = self.env['account.move'].create({
            'journal_id': journal_id,
            'move_type': move_type,
            'ref': move_ref if move_ref else None,
            'line_ids': [(0, 0, {
                'ref': move_ref if move_ref else None,
                'journal_id': journal_id,
                'partner_id': partner_id if partner_id else None,
                'debit': amount if amount else 0.0,
                'account_id': debit_account if debit_account else None,
                'amount_currency': amount_currency,
                'currency_id': currency_id,
            }), (0, 0, {
                'ref': move_ref if move_ref else None,
                'partner_id': partner_id if partner_id else None,
                'credit': amount if amount else 0.0,
                'account_id': credit_account if credit_account else None,
                'amount_currency': amount_currency * -1,
                'currency_id': currency_id,
            })]
        })
        move.action_post()
        return move
    except Exception as e:
        logger.exception("create_account_move_dr_cr_with_currency Method")
        raise ValidationError(e)


def create_account_move_single_with_currency_convert(self, journal_id, move_header, partner_id, amount, debit_account,
                                                     credit_account, move_ref, application_id, officebranches_id,
                                                     currency_id, amount_currency):
    try:
        kd_amount = get_amt_eq(self, amount, currency_id)
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal_id,
            'line_ids': [(0, 0, {
                'name': move_header if move_header else None,
                'partner_id': partner_id if partner_id else None,
                'debit': kd_amount if amount else 0.0,
                'account_id': debit_account if debit_account else None,
                'ref': move_ref if move_ref else None,
                'amount_currency': amount_currency,
                'currency_id': currency_id,
            }), (0, 0, {
                'name': move_header if move_header else None,
                'partner_id': partner_id if partner_id else None,
                'credit': kd_amount if amount else 0.0,
                'account_id': credit_account if credit_account else None,
                'amount_currency': amount_currency * -1,
                'currency_id': currency_id,
            })]
        })
        move.action_post()
        return move
    except Exception as e:
        logger.exception("create_account_move_single_with_currency_convert Method")
        raise ValidationError(e)


def remove_attached_payments_from_sales_invoice(self, invoice):
    try:
        if invoice:
            move_lines = self.env['account.move.line'].search([('move_id', '=', invoice.id)])
            for move_line in move_lines:
                partial_id = self.env['account.partial.reconcile'].search([('debit_move_id', '=', move_line.id)],
                                                                          limit=1)
                if partial_id:
                    invoice.js_remove_outstanding_partial(partial_id.id)
    except Exception as e:
        logger.exception("remove_attached_payments_from_sales_invoice Title")
        raise ValidationError(e)


def attached_payments_from_sales_invoice(self, invoice):
    try:
        account_payments_registered = self.env['account.payment.register'].search([])
        account_payments_registered.line_ids.filtered(
            lambda line: line.id == invoice.line_ids.filtered(lambda l: l.debit))

        for account_payment_registered in account_payments_registered:
            invoice.js_assign_outstanding_line(account_payment_registered)

        # print(account_payments_registered.id)

        # invoice.line_ids.filtered(lambda line: line.account_id == self.receivable_account)

        # credit_line_a = invoice.line_ids.filtered(lambda l: l.debit)    #ID = 3775

        # credit_line_a = payment_obj.move_line_ids.filtered(
        #     lambda l: l.credit)
        # move.js_assign_outstanding_line(credit_line_a.id)

        # account_payments_registered = self.env['account.payment.register'].with_context(active_model='account.move.line',
        #                                                                                dont_redirect_to_payments=True,
        #                                                                                active_ids=invoice.ids)
        # print(account_payments_registered)

        #
        # if account_payments_registered:
        #     for account_payment_registered in account_payments_registered:
        #         print(account_payment_registered.id)

        # for invoice in posted.filtered(lambda move: move.is_invoice()):
        #     payments = invoice.mapped('transaction_ids.payment_id')
        #     move_lines = payments.line_ids.filtered(lambda line: line.account_internal_type in ('receivable', 'payable') and not line.reconciled)
        #     for line in move_lines:
        #         invoice.js_assign_outstanding_line(line.id)
        # return posted
        #

        # if invoice:
        #     credit_line_a = invoice.line_ids.filtered(lambda l: l.credit)
        #     invoice.js_assign_outstanding_line(credit_line_a.id)

        # if invoice:
        #     move_lines = self.env['account.move.line'].search([('move_id', '=', invoice.id)])
        #     for move_line in move_lines:
        #         if move_line.credit != 0:
        #             invoice.js_assign_outstanding_line(move_line.id)

        # partial_id = self.env['account.partial.reconcile'].search([('credit_move_id', '=', move_line.id)], limit=1)
        # if partial_id:
        #     invoice.js_assign_outstanding_line(partial_id.id)
    except Exception as e:
        logger.exception("remove_attached_payments_from_sales_invoice Title")
        raise ValidationError(e)


def remove_move_lines(self, move_obj):
    if move_obj:
        move_obj.button_cancel()
        move_obj.unlink()


def reverse_move_payment(self, payment_obj):
    if payment_obj:
        move_line_obj = self.env['account.move.line'].search(
            [('payment_id', '=', payment_obj.id)])
        for move_line in move_line_obj:
            move_obj = self.env['account.move'].search([('id', '=', move_line.move_id.id)], limit=1)
            if move_obj:
                move_obj.reverse_moves()
                break


def cancel_reverse_move_payment(self, payment_obj):
    if payment_obj:
        move_line_obj = self.env['account.move.line'].search(
            [('payment_id', '=', payment_obj.id)])
        for move_line in move_line_obj:
            move_obj = self.env['account.move'].search([('id', '=', move_line.move_id.id)], limit=1)
            if move_obj:
                move_obj.button_cancel()
                break


def unreconcile_invoice_move_lines(self, invoice_obj):
    # Un-Reconcile all movement
    invoice_move_lines = self.env['account.move.line'].search \
        ([('move_id', '=', invoice_obj.id)])
    for invoice_move_line in invoice_move_lines:
        invoice_move_line.remove_move_reconcile()


def reverse_invoice_payments(self, invoice_obj):
    if invoice_obj:
        self._cr.execute(
            """ SELECT payment_id FROM account_invoice_payment_rel where invoice_id = %s """ % invoice_obj.id)
        for result in self._cr.fetchall():
            payment_id = result[0] if result[0] else 0
            payment_obj = self.env['account.payment'].search(
                [('id', '=', payment_id)])
            reverse_move_payment(self, payment_obj)


def cancel_reverse_invoice_payments(self, invoice_obj):
    if invoice_obj:
        self._cr.execute(
            """ SELECT payment_id FROM account_invoice_payment_rel where invoice_id = %s """ % invoice_obj.id)
        for result in self._cr.fetchall():
            payment_id = result[0] if result[0] else 0
            payment_obj = self.env['account.payment'].search(
                [('id', '=', payment_id)])
            move_payment_obj = self.env['account.move'].search(
                [('ref', '=', 'Reversal of: ' + payment_obj.display_name)])
            if move_payment_obj:
                move_payment_obj.button_cancel()


def move_between_cash_box(self, from_cash_box, to_cash_box, journal_id, move_header, partner_id, amount, move_ref):
    try:
        from_cash_box_account_id = to_cash_box_account_id = 0
        from_cash_box_obj = self.env['account.journal'].search(
            [('id', '=', from_cash_box)], limit=1)
        if from_cash_box_obj:
            from_cash_box_account_id = from_cash_box_obj.default_debit_account_id.id

        to_cash_box_obj = self.env['account.journal'].search(
            [('id', '=', to_cash_box)], limit=1)

        if to_cash_box_obj:
            to_cash_box_account_id = to_cash_box_obj.default_debit_account_id.id

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          from_cash_box_account_id, to_cash_box_account_id, move_ref)
        return move
    except Exception as e:
        logger.exception("move_between_cash_box Method")
        raise ValidationError(e)


def activate_canceled_invoice(self, invoice_obj):
    try:
        invoice_obj.action_invoice_draft()
        invoice_obj.action_move_create()
        invoice_obj.invoice_validate()
        invoice_obj.action_invoice_open()

    except Exception as e:
        logger.exception("activate_canceled_invoice Method")
        raise ValidationError(e)


# ==================================== RESERVATIONS OPERATIONS =========================================================
def reservation_sales_invoice(self, application_obj, deal_amount, customer_id):
    try:
        journal = get_setup(self, 'direct_journal_deferred_income') if get_setup(self,
                                                                                 'direct_journal_deferred_income') else 0
        acc_deffered_income = get_setup(self, 'direct_deferred_income') if get_setup(self,
                                                                                     'direct_deferred_income') else 0
        acc_rec = get_setup(self, 'direct_accounts_receivable') if get_setup(self, 'direct_accounts_receivable') else 0

        if (journal == 0) or (acc_rec == 0) \
                or (acc_deffered_income == 0):
            raise ValidationError(
                _('Please review sales accounts setup, '
                  'Housemaid setting page (Sales Joural OR Deffered Account Or Receivable Account) is missing.'))

        invoice_header = 'New Reservation for ' + get_sales_invoice_header(application_obj)
        product_obj = housemaid_sales_service(self)

        analytic_account = application_obj.analytic_account if application_obj.analytic_account else None
        analytic_tag = application_obj.analytic_tag if application_obj.analytic_tag else None

        sales_invoice = create_sales_invoice(self, journal, acc_deffered_income,
                                             invoice_header, deal_amount,
                                             customer_id, product_obj,analytic_account,analytic_tag)
        return sales_invoice.id
    except Exception as e:
        logger.exception("reservation_sales_invoice Method")
        raise ValidationError(e)


def NOT_USE_reservation_purchase_invoice(self, application_obj):
    # Create purchase movement
    # ==========================
    #  Cr: External office - Suspense A/C
    #  Dr: Goods on trans
    #  Amount = Purchase Amount
    try:
        purchase_deferred_account_id = get_setup(self, 'direct_deferred_purchase') \
            if get_setup(self, 'direct_deferred_purchase') else 0
        office_suspense_account_id = 0
        vendor_obj = None
        purchase_journal_obj = None

        invoice_header = 'New Reservation For ' + get_purchase_invoice_header(application_obj)
        invoice_details = get_purchase_invoice_details(application_obj)
        product_obj = housemaid_purchase_service(self)
        invoice_amount = application_obj.office_commission if application_obj.office_commission else 0
        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            purchase_journal_obj = externaloffices_obj.journal
            office_suspense_account_id = externaloffices_obj.suspense_account
            vendor_obj = self.env['res.partner'].search(
                [('id', '=', externaloffices_obj.vendor_id.id)], limit=1)

        if not vendor_obj:
            raise ValidationError(
                _('No vendor is defined, please ensure the name of external office match with vendor name.'))

        if purchase_journal_obj.id == 0:
            raise ValidationError(
                _('Please review purchase deferred accounts setup, '
                  'Housemaid setting page (Purchase Journal is missing).'))

        if office_suspense_account_id == 0:
            raise ValidationError(
                _('Please review purchase deferred accounts setup, External office page.'))

        if invoice_amount == 0:
            raise ValidationError(
                _('No office commission is defined.'))

        invoice = create_purchase_invoice(self, invoice_header, purchase_journal_obj,
                                          invoice_amount, office_suspense_account_id,
                                          vendor_obj, product_obj)
        return invoice.id
    except Exception as e:
        logger.exception("reservation_purchase_invoice Method")
        raise ValidationError(e)


def reservation_sales_invoice_payment(self, application_obj, amount, invoice_id, journal):
    try:
        action_name = 'new reservation of %s' % (get_sales_invoice_header(application_obj))
        invoice_obj = self.env['account.move'].search([('id', '=', invoice_id)], limit=1)
        # cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,'direct_journal_arrival_cash') else 0

        if journal == 0:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Cash Journal Missing).'))

        if not invoice_obj:
            raise ValidationError(
                _('Sales Invoice is missing.'))

        sales_invoice_payment = create_sales_invoice_payment_with_discount(self, action_name,
                                                                           amount, invoice_obj, journal)

        return sales_invoice_payment.id
    except Exception as e:
        logger.exception("reservation_sales_invoice_payment Method")
        raise ValidationError(e)


def reservation_refund_down_payment(self, down_payment_invoice):
    try:
        amount = self.down_payment_amount
        if amount == 0.0:
            return
        communication = 'Refund payment of %s' % down_payment_invoice.move_id.name
        memo = 'Refund down payment of %s' % get_sales_invoice_header(self.application_id)
        partner_id = self.customer_id.id
        journal_id = down_payment_invoice.journal_id.id

        sales_invoice_refund_payment = create_sales_invoice_refund_payment(self, amount, communication, journal_id,
                                                                           partner_id, memo)

        return sales_invoice_refund_payment.id
    except Exception as e:
        logger.exception("reservation_refund_down_payment Title")
        raise ValidationError(e)


def reservation_purchases_move(self, application_obj):
    # Create purchase movement
    # ==========================
    #  Cr: External office - Suspense A/C
    #  Dr: Goods on trans
    #  Amount = Purchase Amount
    try:
        purchase_journal_obj = None
        journal_id = debit_account = credit_account = officebranches_id = 0
        move_header = 'New Reservation For ' + get_sales_invoice_header(application_obj)
        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)
        move_ref = move_header
        partner_id = externaloffices_obj.vendor_id.id
        amount = application_obj.office_commission
        currency_id = get_commision_currency(self, externaloffices_obj)
        application_id = application_obj.id
        officebranches_obj = get_application_branch(self, application_obj)

        if externaloffices_obj:
            purchase_journal_obj = externaloffices_obj.journal
            debit_account = get_setup(self, 'direct_deferred_purchase') if get_setup(self,
                                                                                     'direct_deferred_purchase') else 0
            credit_account = externaloffices_obj.suspense_account

        if purchase_journal_obj:
            journal_id = purchase_journal_obj.id

        if officebranches_obj:
            officebranches_id = officebranches_obj.id

        move = create_account_move_single_with_currency_convert(self, journal_id, move_header, partner_id, amount,
                                                                debit_account, credit_account.id, move_ref,
                                                                application_id, officebranches_id, currency_id,
                                                                application_obj.office_commission)

        return move.id
    except Exception as e:
        logger.exception("reservation_purchases_move Method")
        raise ValidationError(e)


def NOT_USE_reservation_move_dr_cash_cr_acctred(self, post_refund_amount, pay_due_date, customer_id, application_id):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', application_id)], limit=1)

        move_header = 'Reservation - Suspend sponsor payment till (' + pay_due_date + ') ' + get_sales_invoice_header(
            application_obj)
        move_ref = move_header

        partner_id = customer_id
        amount = post_refund_amount

        officebranches_obj = get_application_branch(self, application_obj)

        cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') \
            if get_setup(self, 'direct_journal_arrival_cash') else 0
        journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,
                                                                                 'direct_journal_arrival_cash') else 0
        credit_account = get_payment_account_id(self, cash_journal_id, 'credit')
        debit_account = get_setup(self, 'return_accounts_receivable') if get_setup(self,
                                                                                   'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)

        return move.id
    except Exception as e:
        logger.exception("return_back_first_sponsor_move_dr_cash_cr_acctred Method")
        raise ValidationError(e)


# ==================================== ARRIVAL OPERATIONS ===============================================================
def arrival_sales_move(self):
    try:

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        if invoice_sal.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sal.display_name)))

        move_header = 'New Arrival For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.name
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total

        journal_id = get_setup(self, 'direct_journal_recognized_income') \
            if get_setup(self, 'direct_journal_recognized_income') else 0

        debit_account = get_setup(self, 'direct_deferred_income') \
            if get_setup(self, 'direct_deferred_income') else 0

        credit_account = get_setup(self, 'direct_recognized_income') \
            if get_setup(self, 'direct_recognized_income') else 0

        move = create_account_move_dr_cr_single(self, journal_id, partner_id, amount,
                                                debit_account, credit_account, move_ref)

        return move
    except Exception as e:
        logger.exception("arrival_sales_move Method")
        raise ValidationError(e)


def NOT_USED_arrival_sales_move(self, application_obj, purchase_invoice):
    try:
        purchase_journal_obj = None
        journal_id = officebranches_id = 0
        move_header = 'New Arrival For ' + get_sales_invoice_header(application_obj)
        move_ref = purchase_invoice.number
        partner_id = purchase_invoice.partner_id.id
        amount = purchase_invoice.amount_untaxed_signed
        application_id = application_obj.id
        officebranches_obj = get_application_branch(self, application_obj)

        credit_account = get_setup(self, 'direct_deferred_purchase') \
            if get_setup(self, 'direct_deferred_purchase') else 0

        debit_account = get_setup(self, 'direct_arrival_purchase') \
            if get_setup(self, 'direct_arrival_purchase') else 0

        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            purchase_journal_obj = externaloffices_obj.journal_recognized

        if purchase_journal_obj:
            journal_id = purchase_journal_obj.id

        if officebranches_obj:
            officebranches_id = officebranches_obj.id

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("arrival_sales_move Method")
        raise ValidationError(e)


def NOT_USED_arrival_purchases_move(self, application_obj, purchase_invoice):
    try:
        purchase_journal_obj = None
        journal_id = debit_account = credit_account = officebranches_id = 0
        move_header = 'New Arrival For ' + get_sales_invoice_header(application_obj)
        move_ref = purchase_invoice.number
        partner_id = purchase_invoice.partner_id.id
        amount = purchase_invoice.amount_untaxed_signed
        application_id = application_obj.id
        officebranches_obj = get_application_branch(self, application_obj)

        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            purchase_journal_obj = externaloffices_obj.journal_recognized
            debit_account = externaloffices_obj.suspense_account
            credit_account = externaloffices_obj.account

        if purchase_journal_obj:
            journal_id = purchase_journal_obj.id

        if officebranches_obj:
            officebranches_id = officebranches_obj.id

        # if purchase_journal_obj.update_posted != True:
        #     purchase_journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account.id, credit_account.id, move_ref)

        return move
    except Exception as e:
        logger.exception("arrival_purchases_move Method")
        raise ValidationError(e)


def NOT_USED_arrival_reverse_purchase_invoice(self, application_obj):
    try:
        # Cancel Current Invoice
        if self.invoice_purchase_actual:
            self.invoice_purchase_actual.action_cancel()
            self.invoice_purchase_actual.reference = ''

        # Get deferred purchase invoice from reservation object
        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        # Activate canceled invoice
        if reservation_obj:
            reservation_obj.invoice_purchase_id.action_invoice_draft()
            reservation_obj.invoice_purchase_id.action_move_create()
            reservation_obj.invoice_purchase_id.invoice_validate()
            reservation_obj.invoice_purchase_id.action_invoice_open()

    except Exception as e:
        logger.exception("arrival_renew_purchase_invoice Method")
        raise ValidationError(e)


def arrival_renew_purchase_invoice(self, application_obj):
    try:
        # Get deferred purchase invoice from reservation object
        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        # Cancel deferred purchase invoice
        # if reservation_obj:
        #     invoice_purchase_obj = reservation_obj.invoice_purchase_id
        #     if invoice_purchase_obj:
        #         invoice_purchase_obj.action_cancel()

        # Create new purchase invoice based on deferred purchase invoice
        purchase_arrival_account_id = get_setup(self, 'direct_arrival_purchase') \
            if get_setup(self, 'direct_arrival_purchase') else 0
        office_main_account_id = 0
        vendor_obj = None
        purchase_journal_obj = None

        invoice_header = 'New Arrival For ' + get_purchase_invoice_header(application_obj)
        invoice_details = get_purchase_invoice_details(application_obj)
        product_obj = housemaid_purchase_service(self)
        invoice_amount = application_obj.office_commission if application_obj.office_commission else 0
        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            purchase_journal_obj = externaloffices_obj.journal_recognized
            office_main_account_id = externaloffices_obj.account
            vendor_obj = self.env['res.partner'].search(
                [('id', '=', externaloffices_obj.vendor_id.id)], limit=1)

        if not vendor_obj:
            raise ValidationError(
                _('No vendor is defined, please ensure the name of external office match with vendor name.'))

        if purchase_journal_obj.id == 0:
            raise ValidationError(
                _('Please review purchase deferred accounts setup, '
                  'Housemaid setting page (Purchase Journal is missing).'))

        if office_main_account_id == 0:
            raise ValidationError(
                _('Please review purchase deferred accounts setup, External office page.'))

        if invoice_amount == 0:
            raise ValidationError(
                _('No office commission is defined.'))

        analytic_account = application_obj.analytic_account if application_obj.analytic_account else None
        analytic_tag = application_obj.analytic_tag if application_obj.analytic_tag else None
        invoice = create_purchase_invoice(self, invoice_header, purchase_journal_obj,
                                          invoice_amount, office_main_account_id,
                                          vendor_obj, product_obj,analytic_account,analytic_tag)
        return invoice.id

    except Exception as e:
        logger.exception("arrival_renew_purchase_invoice Method")
        raise ValidationError(e)


def NOT_USED_arrival_remove_move_sales(self, move_obj):
    remove_move_lines(self, move_obj)


def NOT_USED_arrival_remove_move_purchase(self, move_obj):
    remove_move_lines(self, move_obj)


# ==================================== DELIVERS OPERATIONS ==============================================================
def NOT_USED_deliver_purchase_move(self):
    try:

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_purchase = self.env['account.move'].search \
            ([('id', '=', arrival_obj.invoice_purchase_actual.id)], limit=1)

        if invoice_purchase.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_purchase.display_name)))

        move_header = 'New Deliver For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_purchase.name
        partner_id = invoice_purchase.partner_id.id
        amount = invoice_purchase.amount_untaxed_signed

        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            journal_obj = externaloffices_obj.journal_recognized
            currency_id = externaloffices_obj.suspense_account.currency_id.id
        else:
            raise ValidationError(_(
                "Purchase journal is missing."))

        debit_account = get_setup(self, 'direct_recognized_purchase') \
            if get_setup(self, 'direct_recognized_purchase') else 0

        credit_account = get_setup(self, 'direct_arrival_purchase') \
            if get_setup(self, 'direct_arrival_purchase') else 0

        move_type = 'entry'

        # self, journal_id, move_type, partner_id, amount,debit_account, credit_account, move_ref, currency_id, amount_currency):
        move = create_account_move_dr_cr_with_currency(self, journal_obj.id, move_type, partner_id, amount,
                                                       debit_account, credit_account, move_ref, currency_id,
                                                       application_obj.office_commission)

        return move
    except Exception as e:
        logger.exception("deliver_purchase_move Method")
        raise ValidationError(e)


def deliver_sales_payment(self):
    try:
        # Cash Journal
        # cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,
        #                                                                               'direct_journal_arrival_cash') else 0
        # cash_journal_obj = self.env['account.journal'].search([('id', '=', cash_journal_id)],
        #                                                       limit=1)
        cash_journal_id = self.journal.id
        if not cash_journal_id:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Cash Journal Is Missing).'))

        # Discount Account
        discount_expense_id = get_setup(self, 'direct_discount_expense') if get_setup(self,
                                                                                      'direct_discount_expense') else 0
        discount_expense_obj = self.env['account.account'].search([('id', '=', discount_expense_id)],
                                                                  limit=1)
        if discount_expense_obj == 0:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Discount Account Is Missing).'))

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        # Invoice Sales
        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        invoice_obj = self.env['account.move'].search([('id', '=', invoice_sal.id)],
                                                      limit=1)
        if not invoice_obj:
            raise ValidationError(
                _('Sales Invoice is missing.'))

        paid_amount = self.paid_amount if self.paid_amount else 0.0
        discount_amount = self.discount_amount if self.discount_amount else 0.0
        action_name = 'New Deliver of %s' % (get_sales_invoice_header(application_obj))

        if self.paid_amount + self.discount_amount == self.invoice_due:
            payment_difference_handling = 'reconcile'
        else:
            payment_difference_handling = 'open'

        sales_invoice_payment = create_sales_invoice_payment_with_discount(self, action_name, paid_amount, invoice_obj,
                                                                           cash_journal_id,
                                                                           discount_amount, discount_expense_obj,
                                                                           payment_difference_handling)

        return sales_invoice_payment

    except Exception as e:
        logger.exception("deliver_sales_payment Method")
        raise ValidationError(e)


def deliver_sales_second_payment(self):
    try:
        # Cash Journal
        cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,
                                                                                      'direct_journal_arrival_cash') else 0
        cash_journal_obj = self.env['account.journal'].search([('id', '=', cash_journal_id)],
                                                              limit=1)
        if not cash_journal_obj:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Cash Journal Is Missing).'))

        # Discount Account
        discount_expense_id = get_setup(self, 'direct_discount_expense') if get_setup(self,
                                                                                      'direct_discount_expense') else 0
        discount_expense_obj = self.env['account.account'].search([('id', '=', discount_expense_id)],
                                                                  limit=1)
        if discount_expense_obj == 0:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Discount Account Is Missing).'))

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        # Invoice Sales
        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        invoice_obj = self.env['account.move'].search([('id', '=', invoice_sal.id)],
                                                      limit=1)
        if not invoice_obj:
            raise ValidationError(
                _('Sales Invoice is missing.'))

        paid_amount = reservation_obj.invoice_sales_id.amount_residual
        discount_amount = 0
        action_name = 'New Deliver - %s' % (get_sales_invoice_header(application_obj))

        sales_invoice_payment = create_sales_invoice_payment_with_discount(self, action_name, paid_amount,
                                                                           invoice_obj, cash_journal_id,
                                                                           discount_amount, discount_expense_obj,
                                                                           'reconcile')

        return sales_invoice_payment

    except Exception as e:
        logger.exception("deliver_sales_second_payment Method")
        raise ValidationError(e)


def deliver_refund_complete_payment(self, paid_payment_invoice):
    try:

        amount = self.paid_amount
        communication = 'Refund complete payment of %s' % paid_payment_invoice.move_id.name
        memo = 'Refund complete payment of %s' % (get_sales_invoice_header(self.application_id))
        partner_id = self.customer_id.id
        journal_id = paid_payment_invoice.journal_id.id

        sales_invoice_refund_payment = create_sales_invoice_refund_payment(self, amount, communication, journal_id,
                                                                           partner_id, memo)

        return sales_invoice_refund_payment.id
    except Exception as e:
        logger.exception("reservation_refund_down_payment Title")
        raise ValidationError(e)


def deliver_sales_invoice_unlink_payment(self, invoice):
    try:
        remove_attached_payments_from_sales_invoice(self, invoice)
    except Exception as e:
        logger.exception("deliver_sales_invoice_reverse_payment Method")
        raise ValidationError(e)


def deliver_sales_invoice_link_payments(self, invoice):
    try:
        attached_payments_from_sales_invoice(self, invoice)
    except Exception as e:
        logger.exception("deliver_sales_invoice_reverse_payment Method")
        raise ValidationError(e)


# ==================================== Re-Sell OPERATIONS ==============================================================
def NOT_USED_resell_refund_down_payment(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        amount = self.refund
        communication = 'Re-Sell Housemaid before deliver to first sponsor (Refund Payment) for ' + get_sales_invoice_header(
            application_obj)
        currency_id = self.invoice_id.currency_id.id
        cash_journal_id = get_setup(self, 'return_journal_cash') if get_setup(self,
                                                                              'return_journal_cash') else 0
        destination_journal_id = get_setup(self, 'journal_reject_after_deliver') if get_setup(self,
                                                                                              'journal_reject_after_deliver') else 0
        partner_id = self.customer_id.id

        payment_refund = create_sales_invoice_refund_payment(self, amount, communication, cash_journal_id, partner_id)

        return payment_refund.id
    except Exception as e:
        logger.exception("resell_refund_down_payment Method")
        raise ValidationError(e)


def NOT_USED_resell_move_dr_return_cr_acctrec(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Re-Sell Housemaid before deliver to first sponsor For ' + get_sales_invoice_header(
            application_obj)
        move_ref = move_header + invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        credit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move

    except Exception as e:
        logger.exception("return_back_from_first_sponsor_move_to_return Method")
        raise ValidationError(e)


def NOT_USED_resell_move_dr_cash_cr_acctred(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Re-Sell Housemaid before deliver to first sponsor - Suspend Sponsor Refund till (' + (
            self.pay_due_date).strftime(
            '%Y-%m-%d') + ') ' + get_sales_invoice_header(application_obj)
        move_ref = move_header

        partner_id = self.customer_id.id
        amount = self.refund

        cash_journal_id = get_setup(self, 'direct_journal_arrival_cash') \
            if get_setup(self, 'direct_journal_arrival_cash') else 0
        journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,
                                                                                 'direct_journal_arrival_cash') else 0
        credit_account = get_payment_account_id(self, cash_journal_id, 'credit')
        debit_account = get_setup(self, 'return_accounts_receivable') if get_setup(self,
                                                                                   'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)

        return move.id
    except Exception as e:
        logger.exception("resell_move_dr_cash_cr_acctred Method")
        raise ValidationError(e)


def NOT_USED_resell_sales_invoice_reverse_payment(self):
    try:
        payment_obj = self.complete_payment_invoice
        if payment_obj:
            reverse_move_payment(self, payment_obj)
    except Exception as e:
        logger.exception("resell_sales_invoice_reverse_payment Method")
        raise ValidationError(e)


def resell_transfer_sales_to_return(self):
    try:

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        if invoice_sal.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sal.display_name)))

        move_header = 'New Resell For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.name
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total

        journal_id = get_setup(self, 'journal_deliver_reject') \
            if get_setup(self, 'journal_deliver_reject') else 0

        credit_account = get_setup(self, 'direct_recognized_income') \
            if get_setup(self, 'direct_recognized_income') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        move = create_account_move_dr_cr_single(self, journal_id, partner_id, amount,
                                                debit_account, credit_account, move_ref)

        return move
    except Exception as e:
        logger.exception("resell_transfer_sales_to_return Method")
        raise ValidationError(e)


# ==================================== Retun Back From First Sponsor OPERATIONS ========================================
def NOT_USED_return_back_from_first_sponsor_move_to_return(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        if invoice_sal.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sal.display_name)))

        move_header = get_sales_invoice_header(application_obj)
        move_ref = invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        credit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move

    except Exception as e:
        logger.exception("return_back_from_first_sponsor_move_to_return Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_move_dr_return_cr_acctrec(self, post_return_amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Return Back from First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = post_return_amount
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        credit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move

    except Exception as e:
        logger.exception("return_back_from_first_sponsor_move_to_return Method")
        raise ValidationError(e)


def NOT_USED_return_back_pay_from_return_cash_box(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        if invoice_sal.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sal.display_name)))

        move_header = get_sales_invoice_header(application_obj)
        move_ref = invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        from_cash_box = get_setup(self, 'direct_journal_arrival_cash') \
            if get_setup(self, 'direct_journal_arrival_cash') else 0

        to_cash_box = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        move = move_between_cash_box(self, from_cash_box, to_cash_box, journal_id, move_header, partner_id, amount,
                                     move_ref)

        return move

    except Exception as e:
        logger.exception("return_back_pay_from_return_cash_box Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_refund_payment(self, post_refund_amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        amount = post_refund_amount
        communication = 'Return Back From First Sponsor (Refund Payment) for ' + get_sales_invoice_header(
            application_obj)
        currency_id = self.invoice_id.currency_id.id
        cash_journal_id = get_setup(self, 'return_journal_cash') if get_setup(self, 'return_journal_cash') else 0

        # destination_journal_id = get_setup(self, 'journal_reject_after_deliver') if get_setup(self,
        #                                                                                       'journal_reject_after_deliver') else 0

        # partner_id = self.customer_id.id

        payment_refund = create_sales_invoice_refund_payment(self, amount, communication, currency_id, cash_journal_id)

        return payment_refund.id
    except Exception as e:
        logger.exception("return_back_first_sponsor_refund_payment Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_move_dr_acctrec_cr_discount(self, post_discount_amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Return Back From First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From First Sponsor For ' + get_sales_invoice_header(application_obj)
        partner_id = self.invoice_id.partner_id.id
        amount = post_discount_amount

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        credit_account = get_setup(self, 'direct_discount_expense') \
            if get_setup(self, 'direct_discount_expense') else 0

        debit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move

    except Exception as e:
        logger.exception("return_back_from_first_sponsor_move_to_return Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_reverse_all_entries(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        deliver_obj = self.env['housemaidsystem.applicant.deliver'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sale = self.env['account.move'].search([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)
        invoice_purchase = self.env['account.move'].search([('id', '=', arrival_obj.invoice_purchase_actual.id)],
                                                           limit=1)

        if invoice_sale.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sale.display_name)))

        # 1) Reverse Sales invoice payments
        # unreconcile_invoice_move_lines(self, invoice_sale)
        reverse_invoice_payments(self, invoice_sale)

        # 2) Reverse Purchase invoice payments
        reverse_invoice_payments(self, invoice_purchase)

        # 3) Cancel Invoice sale
        invoice_sale.action_cancel()

        # 4) Cancel Invoice purchase
        invoice_purchase.action_cancel()

        # 5) Reverse move of Deliver :
        deliver_obj.invoice_sales_recong_id.button_cancel()
        deliver_obj.invoice_sales_recong_id.unlink()

        # 5) Reverse move of Deliver
        deliver_obj.invoice_po_recong_id.button_cancel()
        deliver_obj.invoice_po_recong_id.unlink()


    except Exception as e:
        logger.exception("return_back_first_sponsor_reverse_all_entries Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_remove_reversed_all_entries(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        deliver_obj = self.env['housemaidsystem.applicant.deliver'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sale = self.env['account.move'].search([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)
        invoice_purchase = self.env['account.move'].search([('id', '=', arrival_obj.invoice_purchase_actual.id)],
                                                           limit=1)

        # 1) Reverse Sales invoice payments
        cancel_reverse_invoice_payments(self, invoice_sale)

        # 2) Reverse Purchase invoice payments
        cancel_reverse_invoice_payments(self, invoice_purchase)

        # 3) Activate Canceled Invoice sale
        activate_canceled_invoice(self, invoice_sale)

        # 4) Activate Canceled Invoice purchase
        activate_canceled_invoice(self, invoice_purchase)

        # 5) Reverse move of Deliver :
        # deliver_obj.invoice_sales_recong_id.button_cancel()
        # deliver_obj.invoice_sales_recong_id.unlink()

        # 5) Reverse move of Deliver
        # deliver_obj.invoice_po_recong_id.button_cancel()
        # deliver_obj.invoice_po_recong_id.unlink()

    except Exception as e:
        logger.exception("return_back_first_sponsor_remove_reversed_all_entries Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_move_reverse_sales(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Return Back From First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'direct_journal_recognized_income') \
            if get_setup(self, 'direct_journal_recognized_income') else 0

        debit_account = get_setup(self, 'direct_sales_returned') \
            if get_setup(self, 'direct_sales_returned') else 0

        credit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move

    except Exception as e:
        logger.exception("return_back_first_sponsor_move_reverse_sales Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_move_reverse_purchase(self):
    try:
        move = None

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_purchase = self.env['account.move'].search \
            ([('id', '=', arrival_obj.invoice_purchase_actual.id)], limit=1)

        invoice_purchase_move_line = self.env['account.move.line'].search \
            ([('move_id', '=', invoice_purchase.move_id.id)], limit=1)

        move_header = 'Return Back From First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + invoice_purchase.number
        partner_id = invoice_purchase.partner_id.id
        amount = invoice_purchase_move_line.credit if invoice_purchase_move_line.credit > 0 else invoice_purchase_move_line.debit
        officebranches_obj = get_application_branch(self, application_obj)

        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            journal_obj = externaloffices_obj.journal_recognized
            # if journal_obj.update_posted != True:
            #     journal_obj.update_posted = True
            debit_account = externaloffices_obj.account.id

            credit_account = get_setup(self, 'direct_purchase_returned') \
                if get_setup(self, 'direct_purchase_returned') else 0

            # move = create_account_move_single_with_currency(self, journal_obj.id, move_header, partner_id, amount,
            #                                                 debit_account, credit_account, move_ref, application_obj.id,
            #                                                 officebranches_obj.id, journal_obj.currency_id.id,
            #                                                 application_obj.office_commission)
        if move == None:
            raise ValidationError("return_back_first_sponsor_move_reverse_sales method error.")

        return move

    except Exception as e:
        logger.exception("return_back_first_sponsor_move_reverse_sales Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_move_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From First Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From First Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        partner_id = self.customer_id.id
        amount = self.hm_salary
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        credit_account = get_setup(self, 'return_sales_hm_dues') \
            if get_setup(self, 'return_sales_hm_dues') else 0

        debit_account = get_payment_account_id(self, journal_id, 'debit')

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("return_back_first_sponsor_move_hm_salary Method")
        raise ValidationError(e)


def NOT_USED_return_back_first_sponsor_move_dr_cash_cr_acctred(self, post_refund_amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From First Sponsor - Suspend sponsor payment till (' + (self.pay_due_date).strftime(
            '%Y-%m-%d') + ') ' + get_sales_invoice_header(application_obj)
        move_ref = move_header

        partner_id = self.customer_id.id
        amount = post_refund_amount

        officebranches_obj = get_application_branch(self, application_obj)

        cash_journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0
        journal_id = get_setup(self, 'journal_reject_after_deliver') if get_setup(self,
                                                                                  'journal_reject_after_deliver') else 0
        debit_account = get_payment_account_id(self, cash_journal_id, 'debit')
        credit_account = get_setup(self, 'return_accounts_receivable') if get_setup(self,
                                                                                    'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)

        return move
    except Exception as e:
        logger.exception("return_back_first_sponsor_move_dr_cash_cr_acctred Method")
        raise ValidationError(e)


def return_back_refund_discount(self, discount_amount):
    try:

        journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,
                                                                                 'direct_journal_arrival_cash') else 0
        partner_id = self.customer_id.id

        debit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        credit_account = get_setup(self, 'direct_discount_expense') \
            if get_setup(self, 'direct_discount_expense') else 0

        move_ref = 'Discount reversal'

        # journal_id, partner_id, amount, debit_account, credit_account, move_ref
        sales_invoice_refund_payment = create_account_move_dr_cr_single(self, journal_id, partner_id, discount_amount,
                                                                        debit_account, credit_account,
                                                                        move_ref)

        return sales_invoice_refund_payment.id
    except Exception as e:
        logger.exception("return_back_refund_discount Title")
        raise ValidationError(e)


def return_back_move_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From First Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From First Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        partner_id = self.customer_id.id
        amount = self.hm_salary

        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        credit_account = get_setup(self, 'return_sales_hm_dues') \
            if get_setup(self, 'return_sales_hm_dues') else 0

        partner_id_2 = get_setup(self, 'return_hm_dues_contact') \
            if get_setup(self, 'return_hm_dues_contact') else 0

        debit_account = journal_id

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref, partner_id_2
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref, partner_id_2)
        return move
    except Exception as e:
        logger.exception("return_back_move_hm_salary Method")
        raise ValidationError(e)


def return_back_post_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Return Back From First Sponsor - ' + get_sales_invoice_header(application_obj)
        memo = 'Housemaid salary payment of ' + get_sales_invoice_header(application_obj)

        partner_id = self.customer_id.id
        amount = self.hm_salary
        payment = post_cash_payment(self, amount, move_header, partner_id, 'inbound', memo)

        return payment
    except Exception as e:
        logger.exception("return_back_post_hm_salary Method")
        raise ValidationError(e)


def return_back_transfer_sales_to_return(self):
    try:

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        if invoice_sal.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sal.display_name)))

        move_header = 'Return Back From First Sponsor - ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.name
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        credit_account = get_setup(self, 'direct_recognized_income') \
            if get_setup(self, 'direct_recognized_income') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        move = create_account_move_dr_cr_single(self, journal_id, partner_id, amount,
                                                debit_account, credit_account, move_ref)

        return move
    except Exception as e:
        logger.exception("return_back_transfer_sales_to_return Method")
        raise ValidationError(e)


def return_back_pay_extra(self, amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Return back from first sponsor for ' + get_sales_invoice_header(application_obj)
        memo = 'Payment paid extra to sponsor - ' + get_sales_invoice_header(application_obj)
        partner_id = self.customer_id.id

        payment = post_cash_payment(self, amount, move_header, partner_id, 'outbound', memo)

        return payment
    except Exception as e:
        logger.exception("return_back_pay_extra Method")
        raise ValidationError(e)


def return_back_pay_less(self, amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Return back from first sponsor for ' + get_sales_invoice_header(application_obj)
        memo = 'Payment paid less to sponsor - ' + get_sales_invoice_header(application_obj)
        partner_id = self.customer_id.id

        payment = post_cash_payment(self, amount, move_header, partner_id, 'inbound', memo)

        return payment
    except Exception as e:
        logger.exception("return_back_pay_less Method")
        raise ValidationError(e)


def return_back_move_register_gain_loss(self, amount, gain_loss):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From First Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From First Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        partner_id = self.customer_id.id

        if gain_loss == 'loss':
            credit_account = get_setup(self, 'direct_accounts_receivable') \
                if get_setup(self, 'direct_accounts_receivable') else 0

            debit_account = get_setup(self, 'return_pay_extra_loss') \
                if get_setup(self, 'return_pay_extra_loss') else 0
        else:
            credit_account = get_setup(self, 'return_pay_extra_loss') \
                if get_setup(self, 'return_pay_extra_loss') else 0

            debit_account = get_setup(self, 'direct_accounts_receivable') \
                if get_setup(self, 'direct_accounts_receivable') else 0

        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref, partner_id_2
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("return_back_move_register_gain_loss Method")
        raise ValidationError(e)


# ==================================== Back To Country After Back From First Sponsor ====================================
def NOT_USED_back_to_country_after_first_sponsor_move_dr_acctrec_cr_discount(self, post_discount_amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Back To Country After First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = 'Back To Country After First Sponsor For ' + get_sales_invoice_header(application_obj)
        partner_id = self.invoice_id.partner_id.id
        amount = post_discount_amount
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        credit_account = get_setup(self, 'direct_discount_expense') \
            if get_setup(self, 'direct_discount_expense') else 0

        debit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move

    except Exception as e:
        logger.exception("back_to_country_after_first_sponsor_move_dr_acctrec_cr_discount Method")
        raise ValidationError(e)


def back_to_country_after_first_sponsor_move_reverse_sales_in_sales_retun(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Back To Country After First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'direct_journal_recognized_income') \
            if get_setup(self, 'direct_journal_recognized_income') else 0

        debit_account = get_setup(self, 'direct_sales_returned') \
            if get_setup(self, 'direct_sales_returned') else 0

        credit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("back_to_country_after_first_sponsor_move_reverse_sales Method")
        raise ValidationError(e)


def back_to_country_after_first_sponsor_move_reverse_purchase(self):
    try:
        move = None

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        arrival_obj = self.env['housemaidsystem.applicant.arrival'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_purchase = self.env['account.move'].search \
            ([('id', '=', arrival_obj.invoice_purchase_actual.id)], limit=1)

        invoice_purchase_move_line = self.env['account.move.line'].search \
            ([('move_id', '=', invoice_purchase.move_id.id)], limit=1)

        move_header = 'Back To Country After First Sponsor ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + invoice_purchase.number
        partner_id = invoice_purchase.partner_id.id
        amount = invoice_purchase_move_line.credit if invoice_purchase_move_line.credit > 0 else invoice_purchase_move_line.debit
        officebranches_obj = get_application_branch(self, application_obj)

        externaloffices_obj = self.env['housemaidsystem.configuration.externaloffices'].search(
            [('id', '=', application_obj.office_code.id)], limit=1)

        if externaloffices_obj:
            journal_obj = externaloffices_obj.journal_recognized
            # if journal_obj.update_posted != True:
            #     journal_obj.update_posted = True
            debit_account = externaloffices_obj.account.id

            credit_account = get_setup(self, 'direct_purchase_returned') \
                if get_setup(self, 'direct_purchase_returned') else 0

            # move = create_account_move_single_with_currency(self, journal_obj.id, move_header, partner_id, amount,
            #                                                 debit_account, credit_account, move_ref,
            #                                                 application_obj.id,
            #                                                 officebranches_obj.id, journal_obj.currency_id.id,
            #                                                 application_obj.office_commission)
            if move == None:
                raise ValidationError("back_to_country_after_first_sponsor_move_reverse_purchase method error.")

        return move

    except Exception as e:
        logger.exception("back_to_country_after_first_sponsor_move_reverse_purchase Method")
        raise ValidationError(e)


def NOT_USED_back_to_country_after_first_refund_payment(self, post_refund_amount):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        amount = post_refund_amount
        communication = 'Back To Country After First Sponsor ' + get_sales_invoice_header(application_obj)
        currency_id = self.invoice_id.currency_id.id
        cash_journal_id = get_setup(self, 'return_journal_cash') if get_setup(self,
                                                                              'return_journal_cash') else 0
        destination_journal_id = get_setup(self, 'journal_reject_after_deliver') if get_setup(self,
                                                                                              'journal_reject_after_deliver') else 0
        partner_id = self.customer_id.id

        payment_refund = create_sales_invoice_refund_payment(self, amount, communication, cash_journal_id, partner_id)

        return payment_refund.id
    except Exception as e:
        logger.exception("back_to_country_after_first_refund_payment Method")
        raise ValidationError(e)


def back_to_country_after_first_diff_posting(self, posting_amount, action):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move']. \
            search([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Back To Country After First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.number
        partner_id = invoice_sal.partner_id.id

        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'direct_journal_recognized_income') \
            if get_setup(self, 'direct_journal_recognized_income') else 0

        if action == 'insurance-greater':
            amount = posting_amount - invoice_sal.amount_total

            debit_account = get_setup(self, 'return_sales_unrecognized_profit_loss') \
                if get_setup(self, 'return_sales_unrecognized_profit_loss') else 0

            credit_account = get_setup(self, 'reject_after_deliver') \
                if get_setup(self, 'reject_after_deliver') else 0
        else:
            amount = invoice_sal.amount_total - posting_amount

            debit_account = get_setup(self, 'reject_after_deliver') \
                if get_setup(self, 'reject_after_deliver') else 0

            credit_account = get_setup(self, 'return_sales_unrecognized_profit_loss') \
                if get_setup(self, 'return_sales_unrecognized_profit_loss') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        if amount > 0.0:
            move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                              debit_account, credit_account, move_ref)
        else:
            move = None

        return move
    except Exception as e:
        logger.exception("back_to_country_after_first_diff_posting Method")
        raise ValidationError(e)


def back_to_country_after_first_sponsor_move_reverse_sales_in_retun_office(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Back To Country After First Sponsor For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.number
        partner_id = invoice_sal.partner_id.id
        amount = invoice_sal.amount_total
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'direct_journal_recognized_income') \
            if get_setup(self, 'direct_journal_recognized_income') else 0

        debit_account = get_setup(self, 'direct_recognized_income') \
            if get_setup(self, 'direct_recognized_income') else 0

        credit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("back_to_country_after_first_sponsor_move_reverse_sales Method")
        raise ValidationError(e)


# ==================================== return back from last sponsor OPERATIONS =========================================
def return_back_last_sponsor_resell(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        # latest_selltest = self.env['housemaidsystem.applicant.selltest'].search(
        #     [('application_id', '=', self.application_id.id)], order="id desc",
        #         limit=1)
        #
        # if latest_selltest:
        #     post_amount = latest_selltest.previous_refund
        # else:
        #     post_amount = self.refund_amount

        move_header = 'Return Back From Last Sponsor for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From Last Sponsor for ' + get_sales_invoice_header(application_obj)
        partner_id = self.old_customer_id.id
        amount = self.refund_amount

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        credit_account = get_setup(self, 'return_accounts_receivable') \
            if get_setup(self, 'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("return_back_last_sponsor_resell Method")
        raise ValidationError(e)


def NOT_USED_return_back_last_sponsor_move_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From Last Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From Last Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        partner_id = self.old_customer_id.id
        amount = self.hm_salary
        officebranches_obj = get_application_branch(self, application_obj)

        # if self.paid_immediately:
        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0
        credit_account = get_setup(self, 'return_sales_hm_dues') \
            if get_setup(self, 'return_sales_hm_dues') else 0
        debit_account = get_payment_account_id(self, journal_id, 'debit')
        # else:
        #     journal_id = get_setup(self, 'journal_reject_after_deliver') \
        #         if get_setup(self, 'journal_reject_after_deliver') else 0
        #     credit_account = get_setup(self, 'return_sales_hm_dues') \
        #         if get_setup(self, 'return_sales_hm_dues') else 0
        #     debit_account = get_setup(self, 'return_accounts_receivable') if get_setup(self,
        #                                                                                'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("return_back_last_sponsor_move_hm_salary Method")
        raise ValidationError(e)


def return_back_last_sponsor_move_dr_cash_cr_acctred(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From Last Sponsor - Suspend sponsor payment till (' + (self.pay_due_date).strftime(
            '%Y-%m-%d') + ') ' + get_sales_invoice_header(application_obj)
        move_ref = move_header

        partner_id = self.old_customer_id.id
        amount = self.refund_amount

        officebranches_obj = get_application_branch(self, application_obj)

        cash_journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0
        journal_id = get_setup(self, 'journal_reject_after_deliver') if get_setup(self,
                                                                                  'journal_reject_after_deliver') else 0
        debit_account = get_payment_account_id(self, cash_journal_id, 'debit')
        credit_account = get_setup(self, 'return_accounts_receivable') if get_setup(self,
                                                                                    'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)

        return move
    except Exception as e:
        logger.exception("return_back_first_sponsor_move_dr_cash_cr_acctred Method")
        raise ValidationError(e)


def return_back_last_sponsor_refund_payment(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        amount = self.refund_amount
        communication = 'Return Back From Last Sponsor (Refund Payment) for ' + get_sales_invoice_header(
            application_obj)
        currency_id = self.old_invoice_id.currency_id.id
        cash_journal_id = get_setup(self, 'return_journal_cash') if get_setup(self, 'return_journal_cash') else 0

        destination_journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        partner_id = self.old_customer_id.id

        payment_refund = create_sales_invoice_refund_payment(self, amount, communication, cash_journal_id, partner_id)

        return payment_refund.id
    except Exception as e:
        logger.exception("return_back_last_sponsor_refund_payment Method")
        raise ValidationError(e)


def return_back_last_sponsor_move_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Return Back From Last Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Return Back From Last Sponsor - Salary for ' + get_sales_invoice_header(application_obj)
        partner_id = self.old_customer_id.id
        amount = self.hm_salary

        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        credit_account = get_setup(self, 'return_sales_hm_dues') \
            if get_setup(self, 'return_sales_hm_dues') else 0

        partner_id_2 = get_setup(self, 'return_hm_dues_contact') \
            if get_setup(self, 'return_hm_dues_contact') else 0

        debit_account = journal_id

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref, partner_id_2
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref, partner_id_2)
        return move
    except Exception as e:
        logger.exception("return_back_last_sponsor_move_hm_salary Method")
        raise ValidationError(e)


def return_back_last_sponsor_post_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Return Back From Last Sponsor - ' + get_sales_invoice_header(application_obj)
        memo = 'Housemaid salary payment of ' + get_sales_invoice_header(application_obj)

        partner_id = self.old_customer_id.id
        amount = self.hm_salary
        payment = post_cash_payment(self, amount, move_header, partner_id, 'inbound', memo)

        return payment
    except Exception as e:
        logger.exception("return_back_post_hm_salary Method")
        raise ValidationError(e)


def return_back_last_sponsor_refund_down_payment(self, down_payment_invoice):
    try:
        amount = self.down_payment_amount
        communication = 'Refund payment of %s' % down_payment_invoice.move_id.name
        memo = 'Refund down payment of %s' % get_sales_invoice_header(self.application_id)
        partner_id = self.new_customer_id.id
        journal_id = down_payment_invoice.journal_id.id

        sales_invoice_refund_payment = create_sales_invoice_refund_payment(self, amount, communication, journal_id,
                                                                           partner_id, memo)

        return sales_invoice_refund_payment.id
    except Exception as e:
        logger.exception("return_back_last_sponsor_refund_down_payment method")
        raise ValidationError(e)


def return_back_last_sponsor_refund_complete_payment(self, paid_payment_invoice):
    try:

        amount = self.complete_payment_amount
        communication = 'Refund complete payment of %s' % paid_payment_invoice.move_id.name
        memo = 'Refund complete payment of %s' % (get_sales_invoice_header(self.application_id))
        partner_id = self.new_customer_id.id
        journal_id = paid_payment_invoice.journal_id.id

        sales_invoice_refund_payment = create_sales_invoice_refund_payment(self, amount, communication, journal_id,
                                                                           partner_id, memo)

        return sales_invoice_refund_payment.id
    except Exception as e:
        logger.exception("reservation_refund_down_payment Title")
        raise ValidationError(e)


def return_back_last_sponsor_sales_invoice_unlink_payment(self, invoice):
    try:
        remove_attached_payments_from_sales_invoice(self, invoice)
    except Exception as e:
        logger.exception("return_back_last_sponsor_sales_invoice_unlink_payment Method")
        raise ValidationError(e)


def return_back_last_sponsor_transfer_sales_to_return(self, sellastest):
    try:

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        invoice_sal = self.env['account.move'].search \
            ([('id', '=', sellastest.new_invoice_id.id)], limit=1)

        if invoice_sal.state == 'cancel':
            raise ValidationError(_(
                "Sales invoice %s should be full paid or partial paid, the current status is canceled." % (
                    invoice_sal.display_name)))

        move_header = 'Return Back From Last Sponsor - ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.name
        partner_id = sellastest.new_customer_id.id
        amount = invoice_sal.amount_total

        journal_id = get_setup(self, 'journal_reject_after_deliver') \
            if get_setup(self, 'journal_reject_after_deliver') else 0

        credit_account = get_setup(self, 'return_sales_recognized') \
            if get_setup(self, 'return_sales_recognized') else 0

        debit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        move = create_account_move_dr_cr_single(self, journal_id, partner_id, amount,
                                                debit_account, credit_account, move_ref)

        return move
    except Exception as e:
        logger.exception("return_back_last_sponsor_transfer_sales_to_return Method")
        raise ValidationError(e)


def return_back_last_sponsor_refund_discount(self, discount_amount):
    try:

        journal_id = get_setup(self, 'direct_journal_arrival_cash') if get_setup(self,
                                                                                 'direct_journal_arrival_cash') else 0
        partner_id = self.new_customer_id.id

        debit_account = get_setup(self, 'direct_accounts_receivable') \
            if get_setup(self, 'direct_accounts_receivable') else 0

        credit_account = get_setup(self, 'direct_discount_expense') \
            if get_setup(self, 'direct_discount_expense') else 0

        move_ref = 'Discount reversal'

        # journal_id, partner_id, amount, debit_account, credit_account, move_ref
        sales_invoice_refund_payment = create_account_move_dr_cr_single(self, journal_id, partner_id, discount_amount,
                                                                        debit_account, credit_account,
                                                                        move_ref)

        return sales_invoice_refund_payment.id
    except Exception as e:
        logger.exception("return_back_refund_discount Title")
        raise ValidationError(e)


# ==================================== Sell As Test \ Rejected \ Accepted ===============================================
def selltest_invoice_inoice_creation(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        return_journal_deferred = get_setup(self, 'return_journal_deferred') \
            if get_setup(self, 'return_journal_deferred') else 0

        return_accounts_receivable = get_setup(self, 'return_accounts_receivable') \
            if get_setup(self, 'return_accounts_receivable') else 0

        return_sales_deferred = get_setup(self, 'return_sales_deferred') \
            if get_setup(self, 'return_sales_deferred') else 0

        if return_journal_deferred == 0 \
                or return_accounts_receivable == 0 or return_sales_deferred == 0:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page.'))

        return_journal_deferred_obj = self.env['account.journal'].search([('id', '=', return_journal_deferred)],
                                                                         limit=1)
        if not return_journal_deferred_obj:
            raise ValidationError(
                _('Sales return journal is not define, please define it using settings page.'))

        invoice_header = 'Sell As Test For ' + get_sales_invoice_header(application_obj)
        invoice_details = 'Sell As Test For ' + get_sales_invoice_details(application_obj)
        product_obj = housemaid_sales_service(self)
        customer_id = self.new_customer_id.id

        analytic_account = application_obj.analytic_account if application_obj.analytic_account else None
        analytic_tag = application_obj.analytic_tag if application_obj.analytic_tag else None

        # journal, acc_deffered_income, invoice_header, deal_amount, customer_id, product_obj
        sales_invoice = create_sales_invoice(self, return_journal_deferred, return_sales_deferred,
                                             invoice_header, self.deal_amount,
                                             customer_id, product_obj,analytic_account,analytic_tag)

        return sales_invoice.id
    except Exception as e:
        logger.exception("selltest_invoice_inoice_creation Method")
        raise ValidationError(e)


def selltest_sales_invoice_payment(self, amount, invoice_obj):
    try:
        cash_journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        if cash_journal_id == 0:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Cash Journal Missing).'))

        if not invoice_obj:
            raise ValidationError(
                _('Sales Invoice is missing.'))

        sales_invoice_payment = create_sales_invoice_payment_with_discount(self, 'New Sell as test for ', amount,
                                                                           invoice_obj, cash_journal_id)

        return sales_invoice_payment.id
    except Exception as e:
        logger.exception("selltest_sales_invoice_payment Method")
        raise ValidationError(e)


def selltest_rejection_sales_invoice_reverse_payment(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        if self.down_payment_amount:
            amount = self.down_payment_amount
            communication = 'Sell As Test (Rejected) Refund Down Payment for ' + get_sales_invoice_header(
                application_obj)
            currency_id = self.new_invoice_id.currency_id.id
            cash_journal_id = get_setup(self, 'return_journal_cash') if get_setup(self,
                                                                                  'return_journal_cash') else 0
            destination_journal_id = get_setup(self, 'journal_reject_after_deliver') if get_setup(self,
                                                                                                  'journal_reject_after_deliver') else 0
            partner_id = self.new_invoice_id.partner_id.id

            # amount, communication, cash_journal_id, partner_id
            payment_refund = create_sales_invoice_refund_payment(self, amount, communication,
                                                                 cash_journal_id, partner_id)
            return payment_refund.id
        else:
            return None
    except Exception as e:
        logger.exception("selltest_rejection_sales_invoice_reverse_payment Method")
        raise ValidationError(e)


def selltest_accept_move_sales_recongnized(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Sell As Test (Accepted) for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Sell As Test (Accepted) for ' + get_sales_invoice_header(application_obj)
        partner_id = self.new_invoice_id.partner_id.id
        amount = self.deal_amount

        journal_id = get_setup(self, 'return_journal_recognized') \
            if get_setup(self, 'return_journal_recognized') else 0

        debit_account = get_setup(self, 'return_sales_deferred') \
            if get_setup(self, 'return_sales_deferred') else 0

        credit_account = get_setup(self, 'return_sales_recognized') \
            if get_setup(self, 'return_sales_recognized') else 0

        # journal_obj = self.env['account.journal'].search \
        #     ([('id', '=', journal_id)], limit=1)

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("selltest_accept_move_sales_recongnized Method")
        raise ValidationError(e)


def selltest_accept_sales_invoice_complete_payment(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        invoice_obj = self.new_invoice_id
        partner_id = invoice_obj.partner_id.id
        paid_amount = self.complete_payment_amount
        discount_amount = self.sepecial_discount_amount if self.sepecial_discount_amount > 0.0 else 0.0

        cash_journal_id = get_setup(self, 'return_journal_cash') if get_setup(self, 'return_journal_cash') else 0
        cash_journal_obj = self.env['account.journal'].search([('id', '=', cash_journal_id)],
                                                              limit=1)

        discount_expense_id = get_setup(self, 'direct_discount_expense') if get_setup(self,
                                                                                      'direct_discount_expense') else 0
        discount_expense_obj = self.env['account.account'].search([('id', '=', discount_expense_id)],
                                                                  limit=1)

        action_name = 'New Sell As test (Acceptance) For '

        if cash_journal_id == 0:
            raise ValidationError(
                _('Please review sales accounts setup, Housemaid setting page (Cash Journal Missing).'))

        if not invoice_obj:
            raise ValidationError(
                _('Sales Invoice is missing.'))

        # action_name, amount, invoice_obj, journal_id, discount = 0.0,discount_expense_obj = None, payment_difference_handling = 'open'
        sales_invoice_payment = create_sales_invoice_payment_with_discount(self, action_name, paid_amount, invoice_obj,
                                                                           cash_journal_obj.id,
                                                                           discount_amount, discount_expense_obj,
                                                                           'reconcile')

        # Old Code >> 5/1/2020
        # sales_invoice_payment = create_sales_invoice_payment(self, amount, invoice_obj,
        #                                                      cash_journal_id, partner_id, application_obj)

        return sales_invoice_payment.id
    except Exception as e:
        logger.exception("selltest_accept_sales_invoice_complete_payment Method")
        raise ValidationError(e)


def selltest_accept_maove_sales_close_deliver(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Sell As Test (Accepted) for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Sell As Test (Accepted) for ' + get_sales_invoice_header(application_obj)
        partner_id = self.new_customer_id.id
        amount = self.old_invoice_id.amount_total

        journal_id = get_setup(self, 'return_journal_recognized') \
            if get_setup(self, 'return_journal_recognized') else 0

        debit_account = get_setup(self, 'return_recognized_purchase') \
            if get_setup(self, 'return_recognized_purchase') else 0

        credit_account = get_setup(self, 'reject_after_deliver') \
            if get_setup(self, 'reject_after_deliver') else 0

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("selltest_accept_sales_close_deliver Method")
        raise ValidationError(e)


def NOT_USED_selltest_accept_sales_invoice_discount(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Sell As Test (Accepted) for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Sell As Test (Accepted) for ' + get_sales_invoice_header(application_obj)
        partner_id = self.new_customer_id.id
        amount = self.sepecial_discount_amount
        officebranches_obj = get_application_branch(self, application_obj)

        journal_id = get_setup(self, 'return_journal_recognized') \
            if get_setup(self, 'return_journal_recognized') else 0

        debit_account = get_setup(self, 'direct_discount_expense') \
            if get_setup(self, 'direct_discount_expense') else 0

        credit_account = get_setup(self, 'return_accounts_receivable') \
            if get_setup(self, 'return_accounts_receivable') else 0

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # if journal_obj.update_posted != True:
        #     journal_obj.update_posted = True

        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("selltest_accept_sales_invoice_complete_payment Method")
        raise ValidationError(e)


def selltest_rejection_move_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        move_header = 'Sell As Test (Rejected) - Salary for ' + get_sales_invoice_header(application_obj)
        move_ref = 'Sell As Test (Rejected) - Salary for ' + get_sales_invoice_header(application_obj)
        partner_id = self.new_customer_id.id
        amount = self.hm_salary

        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        credit_account = get_setup(self, 'return_sales_hm_dues') \
            if get_setup(self, 'return_sales_hm_dues') else 0

        debit_account = journal_id

        journal_obj = self.env['account.journal'].search \
            ([('id', '=', journal_id)], limit=1)

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("selltest_rejection_move_hm_salary Method")
        raise ValidationError(e)


def selltest_rejection_move_diff_posting(self, action):
    try:
        amount = debit_account = credit_account = 0

        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)

        reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(
            [('application_id', '=', application_obj.id)], limit=1)

        invoice_sal = self.env['account.move']. \
            search([('id', '=', reservation_obj.invoice_sales_id.id)], limit=1)

        move_header = 'Sell As Test (Rejected) - Profit\Loss For ' + get_sales_invoice_header(application_obj)
        move_ref = move_header + ' ' + invoice_sal.number
        partner_id = invoice_sal.partner_id.id

        journal_id = get_setup(self, 'return_journal_cash') \
            if get_setup(self, 'return_journal_cash') else 0

        if action == 'loss':
            amount = self.rejection_refund_amount - self.down_payment_amount

            debit_account = get_setup(self, 'return_re_sales_profit_loss') \
                if get_setup(self, 'return_re_sales_profit_loss') else 0

            credit_account = get_payment_account_id(self, journal_id, 'credit')

        if action == 'profit':
            amount = self.down_payment_amount - self.rejection_refund_amount

            debit_account = get_payment_account_id(self, journal_id, 'debit')

            credit_account = get_setup(self, 'return_re_sales_profit_loss') \
                if get_setup(self, 'return_re_sales_profit_loss') else 0

        # journal_obj = self.env['account.journal'].search \
        #     ([('id', '=', journal_id)], limit=1)

        # journal_id, move_header, partner_id, amount, debit_account, credit_account, move_ref
        move = create_account_move_single(self, journal_id, move_header, partner_id, amount,
                                          debit_account, credit_account, move_ref)
        return move
    except Exception as e:
        logger.exception("selltest_rejection_move_diff_posting Method")
        raise ValidationError(e)


def selltest_post_hm_salary(self):
    try:
        application_obj = self.env['housemaidsystem.applicant.applications'].search(
            [('id', '=', self.application_id.id)], limit=1)
        move_header = 'Sell As Test (Rejected) - Salary for ' + get_sales_invoice_header(application_obj)
        memo = 'Housemaid salary payment of ' + get_sales_invoice_header(application_obj)
        partner_id = self.new_customer_id.id
        amount = self.hm_salary
        payment = post_cash_payment(self, amount, move_header, partner_id, 'inbound', memo)

        return payment
    except Exception as e:
        logger.exception("selltest_rejection_move_hm_salary Method")
        raise ValidationError(e)


# ==================================== Contracting ===============================================
def add_contract(self, application_obj, sponsorcustomer_id):
    try:
        contracts_print = self.env['housemaidsystem.configuration.contracts_print'].search(
            [('application_id', '=', application_obj.id)], limit=1)
        if not contracts_print:
            contracts_print_data = {
                'name': 'Contract of customer# ' + sponsorcustomer_id.name + ' For Housemaid #' + application_obj.full_name,
                'application_id': application_obj.id,
                'customer_id': sponsorcustomer_id.id,
            }
            contracts_print.create(contracts_print_data)

    except Exception as e:
        logger.exception("add_contract")
        raise ValidationError(e)


def remove_contract(self, application_obj):
    try:
        contracts_print = self.env['housemaidsystem.configuration.contracts_print'].search(
            [('application_id', '=', application_obj.id)])
        if contracts_print:
            for rec in contracts_print:
                rec.unlink()

    except Exception as e:
        logger.exception("remove_contract")
        raise ValidationError(e)


# ==================================== WhatsApp ===============================================
def send_whatsapp(self, partner_obj, message):
    try:
        whatsapp_service_status = get_setup(self, 'whatsapp_service_status')
        if whatsapp_service_status:

            if not partner_obj:
                raise ValidationError(_('Customer is missing.'))

            if not partner_obj.mobile:
                raise ValidationError(_('Customer mobile is missing.'))

            # URL Endpoint
            whatsapp_endpoint = get_setup(self, 'whatsapp_endpoint')
            whatsapp_token = get_setup(self, 'whatsapp_token')
            url = str(whatsapp_endpoint) + '/sendMessage?token=' + str(whatsapp_token)

            # Format Mobile
            whatsapp_msg_number = partner_obj.mobile
            whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "")
            whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace(
                '+' + str(partner_obj.country_id.phone_code), "")
            mobile = "+" + str(partner_obj.country_id.phone_code) + "" + whatsapp_msg_number_without_code

            # Header
            headers = {
                "Content-Type": "application/json",
            }

            # Message Body
            tmp_dict = {
                "phone": mobile,
                "body": message
            }

            response = requests.post(url, json.dumps(tmp_dict), headers=headers)

            if response.status_code == 201 or response.status_code == 200:
                logger.info("\nSend Message successfully")
            else:
                logger.info(str(response.status_code))



    except Exception as e:
        logger.exception("Error Title")
        raise ValidationError(e)
