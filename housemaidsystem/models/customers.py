# -*- coding: utf-8 -*-

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


class SponsorHouseType(models.Model):
    _name = 'housemaidsystem.configuration.sponsor_house_type'
    _description = 'Sponsor House Type'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char(string="House type", required=False, translate=True, )


class SponsorOccupation(models.Model):
    _name = 'housemaidsystem.configuration.sponsor_occupation'
    _description = 'Sponsor Occupation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char(string="Sponsor Occupation", required=False, translate=True, )


class StateArea(models.Model):
    _description = "State area"
    _name = 'housemaidsystem.configuration.area'
    _order = 'code'

    state_id = fields.Many2one('res.country.state', string='State', required=True)
    name = fields.Char(string='Area Name', required=True,)
    code = fields.Char(string='Area Code', help='The area code.', required=True)




class HousemaidResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    name_ar = fields.Char(string="Name (En)")
    is_black_list = fields.Boolean(string="Is Black list?")
    civil_id = fields.Char(string="Civil ID", size=12, required=False)
    civil_id_expiry_dt = fields.Date(string="Civil ID Expiry Date", required=False, )
    unified_id = fields.Char(string="Unified ID", size=40, required=False)
    civil_id_serial = fields.Char(string="Civil ID Serial", size=50, required=False)
    nationality_id = fields.Char(string="Nationality ID Serial", size=50, required=False)
    hm_count = fields.Integer("Housemaid Count", compute='_compute_hm_count')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self._default_country_id())
    nationality = fields.Many2one('res.country', string='Nationality', default=lambda self: self._default_country_id())
    contracts_count = fields.Integer("Contracts Count", compute='_compute_contracts_count')
    civil_id_copy = fields.Binary("Civil ID Copy", attachment=True,
                                  help="This field holds the image used as photo for "
                                       "the housemaidsystem, limited to 1024x1024px.")
    sponsor_gender = fields.Selection(string="Sponsor Gender", selection=[('male', 'Male'), ('female', 'Female'), ],
                                      required=False, default='male')
    mobile2 = fields.Char(string="Mobile 2", required=False)
    mobile3 = fields.Char(string="Mobile 3", required=False)
    mobile4 = fields.Char(string="Mobile 4", required=False)
    sponsor_salary = fields.Float(string="Salary",  required=False, )
    # =====================================================================================================
    sponsor_birth_dt = fields.Date(string="Birth Date", required=False, )
    num_family = fields.Integer("Family Members", required=False, default=0, )
    occupation = fields.Char(string="Occupation Description", required=False, )
    sponsor_occupation = fields.Many2one(comodel_name="housemaidsystem.configuration.sponsor_occupation",
                                         string="Occupation", required=False, )
    sponsor_house_type = fields.Many2one(comodel_name="housemaidsystem.configuration.sponsor_house_type",
                                         string="House Type", required=False, )
    customer_blood = fields.Selection(string="Blood Group",
                                      selection=[('A+', 'A+'),
                                                 ('A-', 'A-'),
                                                 ('B+', 'B+'),
                                                 ('B-', 'B-'),
                                                 ('AB+', 'AB+'),
                                                 ('AB-', 'AB-'),
                                                 ('O+', 'O+'),
                                                 ('O-', 'O-'),
                                                 ],
                                      required=False, help="Field Name: customer_blood", )
    # =====================================================================================================
    state_id = fields.Many2one(comodel_name="res.country.state",
                                         string="States", required=False, )
    area_id = fields.Many2one(comodel_name="housemaidsystem.configuration.area",string="Areas", required=False, )
    sponsor_block = fields.Char(string="Block", required=False, )
    sponsor_street = fields.Char(string="Street", required=False, )
    sponsor_avenue = fields.Char(string="Avenue", required=False, )
    sponsor_building = fields.Char(string="Building", required=False, )
    sponsor_zip = fields.Char(string="Zip", required=False, )
    sponsor_address_id = fields.Char(string="Address ID", required=False, )
    sponsor_floor = fields.Char(string="Floor", required=False, )
    sponsor_flat = fields.Char(string="Flat", required=False, )

    _sql_constraints = [
        ('civil_id', 'unique (civil_id)', "Sponsor Civil ID already exists !")
    ]

    # @api.onchange('state_id')
    # def onchange_states(self):
    #     self.area_id = [
    #         (6, 0, self.area_id.filtered(lambda state: state.id in self.area_id.mapped('state_id').ids).ids)]

    # @api.onchange('state_id')
    # def _onchange_state(self):
    #     if self.state_id:
    #         self.areas.state_id = self.state_id


    def _default_country_id(self):
        return self.env.ref('base.kw').id

    def _compute_hm_count(self):
        for partner in self:
            operator = 'child_of' if partner.is_company else '='
            partner.hm_count = self.env['housemaidsystem.applicant.applications']. \
                search_count([('customer_id', operator, partner.id)])

    def _compute_contracts_count(self):
        for partner in self:
            operator = 'child_of' if partner.is_company else '='
            partner.contracts_count = self.env['housemaidsystem.configuration.contracts_print']. \
                search_count([('customer_id', operator, partner.id)])

    # ================ Create / write / unlink functions================
    def validate(self, vals):
        company_obj = self.env['res.company'].search([('id', '!=', 0)], limit=1)
        if company_obj:
            currency_name = company_obj.currency_id.name.upper() if company_obj.currency_id.name else 'KWD'
        else:
            currency_name = 'KWD'
        if not vals.get('is_compnay', False):
            if vals.get('name') and vals.get('name').isnumeric():
                raise ValidationError("Wrong Sponsor Name.")

            if vals.get('civil_id') and len(vals.get('civil_id')) != 12:
                raise ValidationError("Sponsor Civil ID is wrong.")

            if vals.get('mobile'):
                if currency_name == 'KWD':
                    mobile = vals.get('mobile')
                    if '+965' in mobile:
                        mobile = vals.get('mobile').replace('+965', '').replace(' ', '')
                    if len(mobile) != 8:
                        raise ValidationError("Mobile 1 length should be 8 digits")
                    if mobile.startswith('1') or mobile.startswith('2'):
                        raise ValidationError("Mobile 1 should not start with 1 & 2")

                vals['mobile'] = vals.get('mobile').replace('+965', '').replace(' ', '')

            if vals.get('mobile2'):
                if currency_name == 'KWD':
                    mobile2 = vals.get('mobile2')
                    if '+965' in mobile2:
                        mobile2 = vals.get('mobile2').replace('+965', '').replace(' ', '')
                    if len(mobile2) != 8:
                        raise ValidationError("Mobile 2 length should be 8 digits")
                    if mobile2.startswith('1') or mobile2.startswith('2'):
                        raise ValidationError("Mobile 2 should not start with 1 & 2")

                vals['mobile2'] = vals.get('mobile2').replace('+965', '').replace(' ', '')

            if vals.get('mobile3'):
                if currency_name == 'KWD':
                    mobile3 = vals.get('mobile3')
                    if '+965' in mobile3:
                        mobile3 = vals.get('mobile3').replace('+965', '').replace(' ', '')
                    if len(mobile3) != 8:
                        raise ValidationError("Mobile 3 length should be 8 digits")
                    if mobile3.startswith('1') or mobile3.startswith('2'):
                        raise ValidationError("Mobile 3 should not start with 1 & 2")
                vals['mobile3'] = vals.get('mobile3').replace('+965', '').replace(' ', '')

            if vals.get('mobile4'):
                if currency_name == 'KWD':
                    mobile4 = vals.get('mobile4')
                    if '+965' in mobile4:
                        mobile4 = vals.get('mobile4').replace('+965', '').replace(' ', '')
                    if len(mobile4) != 8:
                        raise ValidationError("Mobile 4 length should be 8 digits")
                    if mobile4.startswith('1') or mobile4.startswith('2'):
                        raise ValidationError("Mobile 4 should not start with 1 & 2")
                vals['mobile3'] = vals.get('mobile3').replace('+965', '').replace(' ', '')

            if vals.get('phone'):
                if currency_name == 'KWD':
                    phone = vals.get('phone')
                    if '+965' in phone:
                        phone = vals.get('phone').replace('+965', '').replace(' ', '')
                    if len(phone) != 8:
                        raise ValidationError("Phone length should be 8 digits")
                    if not (phone.startswith('1') or phone.startswith('2')):
                        raise ValidationError("Phone should not start with 1 & 2")
                vals['phone'] = vals.get('phone').replace('+965', '').replace(' ', '')

    @api.model
    def create(self, vals):
        try:
            self.validate(vals)
            housemaidrespartner_obj = super(HousemaidResPartner, self).create(vals)
            return housemaidrespartner_obj
        except Exception as e:
            logger.exception("Create Method")
            raise ValidationError(e)

    def write(self, vals):
        try:
            self.validate(vals)
            housemaidrespartner_obj = super(HousemaidResPartner, self).write(vals)
            return housemaidrespartner_obj
        except Exception as e:
            logger.exception("Sponsor Write Method")
            raise ValidationError(e)

    def unlink(self):
        try:
            return super(HousemaidResPartner, self).unlink()
        except Exception as e:
            logger.exception("Unlink Sponsor")
            raise ValidationError(e)
