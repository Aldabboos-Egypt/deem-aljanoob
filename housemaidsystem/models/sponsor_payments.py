from odoo import models, fields, api
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging
from . import accounting_integration

logger = logging.getLogger(__name__)

app_stages = [('application', 'Application'),
              ('cancelapplication', 'Cancel Application'),
              ('reservation', 'Reservation'),
              ('visa', 'Visa'),
              ('expectedarrival', 'Expected Arrival'),
              ('arrival', 'Arrival'),
              ('deliverpaidfull', 'Delivered Paid Full'),
              ('deliverpaidpartial', 'Delivered Paid Partial'),
              ('resell', 'Re-Sell'),
              ('returnback', 'Return Back From Fist Sponsor'),
              ('sellastest','Sell As Test'),
              ('sellasfinall','Sell As Final'),
              ('rejectedbysponsor','Rejected By Sponsor'),
              ('returnbackagain', 'Return Back From Last Sponsor'),
              ]


class SponsorPayments(models.Model):
    _name = 'housemaidsystem.sponsorpayments'
    _description = 'Sponsor Payments'
    _rec_name = 'payment_reason'

    # ================ Fields =================================
    effective_dt = fields.Datetime(string="Print Date", required=True, default=fields.Datetime.now)

    OfficeBranches = fields.Many2one(comodel_name="housemaidsystem.configuration.officebranches", string="OfficeBranches", required=True, )
    OfficeBranches_name = fields.Char(related="OfficeBranches.name", string="Office Branch Name")
    OfficeBranches_address = fields.Char(related="OfficeBranches.address", string="Office Branch Address")
    OfficeBranches_telephones = fields.Char(related="OfficeBranches.telephones", string="Office Branch Telephones")
    OfficeBranches_reg_number = fields.Char(related="OfficeBranches.reg_number", string="Office Branch Reg num")

    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications", required=True, )
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor")

    move_obj = fields.Many2one(comodel_name="account.move", string="Move")
    payment_obj = fields.Many2one(comodel_name="account.payment", string="Payment")
    invoice_obj = fields.Many2one(comodel_name="account.move", string="Invoice")

    sposnor_payment_dt = fields.Datetime(string="Payment Date", required=True, default=fields.Date.context_today)
    sposnor_payment = fields.Float(string="Sponsor Payment", required=True, default=0)
    payment_ref = fields.Char(string="Payment ref", required=False, size=200, )
    invoice_ref = fields.Char(string="Invoice ref", required=False, size=200, )
    payment_reason = fields.Char(string="Payment reason", required=False, size=200, )

    convert_amount_to_word = fields.Char(string="Payment In Words", required=False, size=400, )
    sposnor_total = fields.Float(string="Sponsor Total", required=False, default=0)
    sposnor_dues = fields.Float(string="Sponsor dues", required=False, default=0)
    sposnor_previous_paid = fields.Float(string="Sponsor previous paid", required=False, default=0)
    sposnor_discount = fields.Float(string="Sponsor Discount", required=False, default=0)

    payment_type = fields.Char(string="payment Type", required=True, size=20, )
    payment_prepared_by = fields.Char(string="Payment Prepared By", required=False, size=20, )
    app_state = fields.Selection(app_stages, string='Application Status', )
    state = fields.Selection(string='Payment Status', selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ],
                             required=False, track_visibility='onchange', default='draft')

    def post_pending_action(self):
        try:
            if self.state == 'draft':

                payment_obj = self.env['account.payment'].search([('id', '=', self.payment_obj.id)], limit=1)
                if payment_obj and payment_obj.state == 'cancelled':
                    payment_obj.action_draft()
                if payment_obj and payment_obj.state == 'draft':
                    payment_obj.post()

                move_obj = self.env['account.move'].search([('id', '=', self.move_obj.id)], limit=1)
                if move_obj and move_obj.state == 'draft':
                    move_obj.action_post()


            self.write({'state': 'confirmed'})

        except Exception as e:
            logger.exception("post_pending_action Method")
            raise ValidationError(e)





