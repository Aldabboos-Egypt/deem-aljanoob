from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError
import datetime
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class ContractsPrint(models.Model):
    _name = 'housemaidsystem.configuration.contracts_print'
    _rec_name = 'name'
    _description = 'Print housemad contract'

    # Contract Info
    name = fields.Char(string='Contract Name', )
    application_no = fields.Char(string='Application No', )
    contract_date = fields.Date(string="Contract Date", required=False, default=fields.Date.context_today)
    contract_end_date = fields.Date(string="Contract End Date", required=False, default=fields.Date.context_today)
    contract_valid_years = fields.Integer(string="Contract Valid Years", required=False, default=2)
    day_name = fields.Char(string='Day Name (En)', )
    day_ar_name = fields.Char(string='Day Name (Ar)', )
    name_external_office = fields.Char(string="Name of office (En)", )
    name_ar_external_office = fields.Char(string="Name of office (Ar)", )

    # Company Info
    company_id = fields.Many2one('res.company', string='Company', index=False, default=lambda self: self.env.company)
    company_en_name = fields.Char(string="Name (En)", required=False, help="Field Name: company_en_name", )
    company_ar_name = fields.Char(string="Name (Ar)", required=False, help="Field Name: company_ar_name", )
    company_reg_id = fields.Char(string="Commercial Reg", required=False, help="Field Name: company_reg_id", )
    company_unique_num = fields.Char(string="Unique Number", required=False, help="Field Name: company_unique_num", )
    company_unified_num = fields.Char(string="Unified Number", required=False, help="Field Name: company_unified_num", )
    company_address = fields.Char(string="Address (En)", required=False, help="Field Name: company_address", )
    company_address_ar = fields.Char(string="Address (Ar)", required=False, help="Field Name: company_address_ar", )
    company_telephone = fields.Char(string="Telephone", required=False, help="Field Name: company_telephone", )
    company_presenter = fields.Char(string="Presenter (En)", required=False, help="Field Name: company_presenter", )
    company_presenter_ar = fields.Char(string="Presenter (Ar)", required=False,
                                       help="Field Name: company_presenter_ar", )
    company_email = fields.Char(string="Email", required=False, help="Field Name: company_email", )

    # Sponsor Info
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor", required=False, )
    customer_name = fields.Char(string="Name (En)", required=False, help="Field Name: customer_name", )
    customer_name_ar = fields.Char(string="Name (Ar)", required=False, help="Field Name: customer_name_ar", )
    customer_civil_id = fields.Char(string="Civil ID", required=False, help="Field Name: customer_civil_id", )
    customer_civilid_expiry = fields.Date(string="Civil ID Expiry", help="Field Name: customer_civilid_expiry", )
    customer_civil_id_serial = fields.Char(string="Civil ID Serial", required=False,
                                           help="Field Name: customer_civil_id_serial", )
    customer_nationality = fields.Char(string="Nationality", required=False, help="Field Name: customer_nationality", )
    customer_ar_nationality = fields.Char(string="Nationality", required=False,
                                          help="Field Name: customer_ar_nationality", )
    customer_house_type = fields.Char(string="House Type (En)", required=False, help="Field Name: customer_house_type", )
    customer_ar_house_type = fields.Char(string="House Type (Ar)", required=False, help="Field Name: customer_ar_house_type", )
    customer_nationality_no = fields.Char(string="Nationality No", required=False,
                                          help="Field Name: customer_nationality_no", )
    customer_unfied = fields.Char(string="Unified", required=False, help="Field Name: customer_unfied", )
    customer_serial = fields.Char(string="Civil ID Serial", required=False, help="Field Name: customer_serial", )
    customer_mobile = fields.Char(string="Mobile 1", required=False, help="Field Name: customer_mobile", )
    customer_mobile2 = fields.Char(string="Mobile 2", required=False, help="Field Name: customer_mobile2", )
    customer_email = fields.Char(string="Email", required=False, help="Field Name: customer_email", )
    customer_occupation = fields.Char(string="Occupation (En)", required=False,
                                      help="Field Name: customer_occupation", )
    customer_ar_occupation = fields.Char(string="Occupation (Ar)", required=False,
                                         help="Field Name: customer_ar_occupation", )
    customer_salary = fields.Float(string="Salary", required=False, default=0.0, help="Field Name: customer_salary", )
    customer_family_member = fields.Integer(string="Family Member", required=False, default=0,
                                            help="Field Name: customer_family_member", )
    customer_date_birth = fields.Date(string="Date Birth", help="Field Name: customer_date_birth", )
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
    customer_address = fields.Char(string="Address", required=False, help="Field Name: customer_address", )
    customer_ar_address = fields.Char(string="Address", required=False, help="Field Name: customer_address", )
    customer_address_area = fields.Char(string="Address Area", required=False,
                                        help="Field Name: customer_address_area", )
    customer_address_block = fields.Char(string="Address Block", required=False,
                                         help="Field Name: customer_address_block", )
    customer_address_street = fields.Char(string="Address Street", required=False,
                                          help="Field Name: customer_address_street", )
    customer_address_avenue = fields.Char(string="Address Avenue", required=False,
                                          help="Field Name: customer_address_avenue", )
    customer_address_house = fields.Char(string="Address House", required=False,
                                         help="Field Name: customer_address_house", )
    customer_gender = fields.Char(string="Gender", required=False, help="Field Name: customer_gender", )
    customer_address_id = fields.Char(string="Address ID", required=False, help="Field Name: sponsor_address_id", )
    customer_address_floor = fields.Char(string="Floor", required=False, )
    customer_address_flat = fields.Char(string="Flat", required=False, )

    # Housemaid Info
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=False, )
    hm_name = fields.Char(string="Name", required=False, help="Field Name: hm_name", )
    hm_nationality = fields.Char(string="Nationality (En)", required=False, help="Field Name: hm_nationality", )
    hm_ar_nationality = fields.Char(string="Nationality (Ar)", required=False, help="Field Name: hm_nationality", )
    hm_sex = fields.Char(string="Sex", required=False, help="Field Name: hm_sex", )
    hm_ar_sex = fields.Char(string="Sex", required=False, help="Field Name: hm_ar_sex", )
    hm_passport_number = fields.Char(string="Passport Number", required=False, help="Field Name: hm_passport_number", )
    hm_passport_type = fields.Char(string="Passport Type", required=False, help="Field Name: hm_passport_type", )
    hm_passport_expiry = fields.Date(string="Passport Expiry", required=False, help="Field Name: hm_passport_expiry", )
    hm_place_of_issue = fields.Char(string="Place of Issue", required=False, help="Field Name: hm_place_of_issue", )
    hm_passport_courier = fields.Char(string="Passport COR", required=False, help="Field Name: hm_passport_courier", )
    hm_occupation = fields.Char(string="Occupation (En)", required=False, help="Field Name: hm_occupation", )
    hm_ar_occupation = fields.Char(string="Occupation (Ar)", required=False, help="Field Name: hm_ar_occupation", )
    hm_dob = fields.Date(string="DOB", required=False, help="Field Name: hm_dob", )
    hm_office_name = fields.Char(string="External Office Name", required=False, help="Field Name: hm_office_name", )
    hm_salary = fields.Float(string="Salary", help="Field Name: hm_salary", )
    hm_deal_amount = fields.Float(string="Deal Amount", help="Field Name: hm_deal_amount", )

    # Visa Info
    visa_no = fields.Char(string="Visa no", help="Field Name: visa_no", )
    visa_type = fields.Char(string="Visa Type", help="Field Name: visa_type", )
    visa_purpose = fields.Char(string="Visa Purpose", help="Field Name: visa_purpose", )
    visa_unified_no = fields.Char(string="Visa Unified no", help="Field Name: visa_unified_no", )
    visa_place_issue = fields.Char(string="Visa Place off issue", help="Field Name: visa_place_issue", )
    visa_issue_date = fields.Date(string="Visa Issue Date", help="Field Name: visa_issue_date", )
    visa_exp_date = fields.Date(string="Visa Expiry Date", help="Field Name: visa_exp_date", )
    visa_applicant_no = fields.Char(string="Application No.", help="Field Name: visa_applicant_no", )

    # =============================================================

    @api.onchange('contract_date')
    def _update_day_name(self):
        for rec in self:
            rec.day_name = rec.contract_date.strftime("%A")

    def _get_translated(self, module_name, field_name, src):
        lang = 'ar_001'
        tt = 'model'
        name = module_name + ',' + field_name
        translated_value = ['']

        if not src:
            return translated_value[0]

        self._cr.execute("""SELECT value FROM ir_translation
                            WHERE lang=%s AND type=%s AND name=%s AND src=%s""",
                         (lang, tt, name, src))
        for value in self._cr.fetchall():
            if value:
                translated_value = value

        return translated_value[0]

    def update_data_action(self):
        try:
            print('first')

            def _fill_branch_data():
                office_branche = self.env['housemaidsystem.configuration.officebranches'].search(
                    [('id', '=', self.application_id.officebranches.id)], limit=1)
                if office_branche:
                    branch_data = {
                        'company_en_name': office_branche.name if office_branche.name else '',
                        'company_ar_name': office_branche.name_ar if office_branche.name_ar else '',
                        'company_reg_id': office_branche.reg_number if office_branche.reg_number else '',
                        'company_unique_num': office_branche.unique_num if office_branche.unique_num else '',
                        'company_unified_num': office_branche.unified_num if office_branche.unified_num else '',
                        'company_address': office_branche.address if office_branche.address else '',
                        'company_address_ar': office_branche.address_ar if office_branche.address_ar else '',
                        'company_telephone': office_branche.telephones if office_branche.telephones else '',
                        'company_presenter': office_branche.presenter if office_branche.presenter else '',
                        'company_presenter_ar': office_branche.presenter_ar if office_branche.presenter_ar else '',
                        'company_email': office_branche.email if office_branche.email else '',
                    }
                    self.write(branch_data)

            def _fill_visa_data():
                visa_obj = self.env['housemaidsystem.applicant.visa'].search(
                    [('application_id', '=', self.application_id.id)], limit=1)
                if visa_obj:
                    visa_data = {
                        'visa_no': visa_obj.visa_no if visa_obj.visa_no else '',
                        'visa_type': 'Visa Type',
                        'visa_purpose': 'Visa Purpose',
                        'visa_unified_no': visa_obj.unified_no if visa_obj.unified_no else '',
                        'visa_place_issue': 'Visal Place Issue',
                        'visa_issue_date': visa_obj.visa_issue_date if visa_obj.visa_issue_date else '',
                        'visa_exp_date': visa_obj.visa_exp_date if visa_obj.visa_exp_date else '',
                        'visa_applicant_no': visa_obj.applicant_no if visa_obj.applicant_no else '',
                    }
                    self.write(visa_data)

            def _fill_customer_data():
                if self.customer_id:

                    customer_data = {
                        'customer_name': self.customer_id.name if self.customer_id.name else '',
                        'customer_name_ar': self.customer_id.name_ar if self.customer_id.name_ar else '',
                        'customer_civil_id': self.customer_id.civil_id if self.customer_id.civil_id else '',
                        'customer_civilid_expiry': self.customer_id.civil_id_expiry_dt if self.customer_id.civil_id_expiry_dt else '',
                        'customer_nationality': self.customer_id.country_id.name if self.customer_id.country_id.name else '',
                        'customer_ar_nationality': self._get_translated('res.country', 'name',
                                                                        self.customer_id.country_id.name),

                        'customer_house_type': self.customer_id.sponsor_house_type.name if self.customer_id.sponsor_house_type.name else '',
                        'customer_ar_house_type': self._get_translated('housemaidsystem.configuration.sponsor_house_type', 'name',
                                                                        self.customer_id.sponsor_house_type.name),

                        'customer_unfied': self.customer_id.unified_id if self.customer_id.unified_id else '',
                        'customer_serial': self.customer_id.civil_id_serial if self.customer_id.civil_id_serial else '',
                        'customer_nationality_no': self.customer_id.nationality_id if self.customer_id.nationality_id else '',
                        'customer_address': self.customer_id.street if self.customer_id.street else '',
                        'customer_ar_address': self.customer_id.street2 if self.customer_id.street2 else '',
                        'customer_address_id': self.customer_id.sponsor_address_id if self.customer_id.sponsor_address_id else '',
                        'customer_family_member': self.customer_id.num_family if self.customer_id.num_family else '',
                        'customer_occupation': self.customer_id.sponsor_occupation.name if self.customer_id.sponsor_occupation.name else '',
                        'customer_ar_occupation': self._get_translated(
                            'housemaidsystem.configuration.sponsor_occupation', 'name',
                            self.customer_id.sponsor_occupation.name),
                        'customer_mobile': self.customer_id.mobile.replace('+965', '').replace(' ', '') if self.customer_id.mobile else '',
                        'customer_mobile2': self.customer_id.mobile2.replace('+965', '').replace(' ', '') if self.customer_id.mobile2 else '',
                        'customer_email': self.customer_id.email_normalized if self.customer_id.email_normalized else '',
                        'customer_gender': self.customer_id.sponsor_gender.upper() if self.customer_id.sponsor_gender else '',
                        'customer_date_birth': self.customer_id.sponsor_birth_dt if self.customer_id.sponsor_birth_dt else '',
                        'customer_address_area': self.customer_id.area_id.name if self.customer_id.area_id else '',
                        'customer_address_block': self.customer_id.sponsor_block if self.customer_id.sponsor_block else '',
                        'customer_address_avenue': self.customer_id.sponsor_avenue if self.customer_id.sponsor_avenue else '',
                        'customer_address_house': self.customer_id.sponsor_building if self.customer_id.sponsor_building else '',
                        'customer_address_street': self.customer_id.sponsor_street if self.customer_id.sponsor_street else '',
                        'customer_address_floor': self.customer_id.sponsor_floor if self.customer_id.sponsor_floor else '',
                        'customer_address_flat': self.customer_id.sponsor_flat if self.customer_id.sponsor_flat else '',
                        'customer_blood': self.customer_id.customer_blood if self.customer_id.customer_blood else '',
                        'customer_salary': self.customer_id.sponsor_salary if self.customer_id.sponsor_salary else 0.0,
                    }
                    self.write(customer_data)

            def _fill_housemaid_data():
                if self.application_id:
                    reservation = self.env['housemaidsystem.applicant.reservations'].search(
                        [('application_id', '=', self.application_id.id)], limit=1)

                    print(reservation)


                    selltest_obj=self.env['housemaidsystem.applicant.selltest'].search([

                        ('application_id','=',self.application_id.id),
                        ('new_customer_id', '=', self.application_id.customer_id.id)

                    ],limit=1,order="id desc")






                    if reservation:
                        self.hm_deal_amount = reservation.deal_amount if reservation.deal_amount else 0.0

                    if selltest_obj:
                        if self.customer_id.id==selltest_obj.new_customer_id.id:
                            self.hm_deal_amount = selltest_obj.deal_amount if selltest_obj.deal_amount else 0.0

                    if self.application_id.gender.upper() == 'MALE':
                        hm_ar_sex = 'ذكر'
                    else:
                        hm_ar_sex = 'أنثي'

                    application_data = {
                        'name_external_office': self.application_id.office_code.name.upper() if self.application_id.office_code.name else '',
                        'name_ar_external_office': self._get_translated('housemaidsystem.configuration.officebranches', 'name',
                                                                  self.application_id.office_code.name),
                        'hm_name': self.application_id.full_name.upper() if self.application_id.full_name else '',
                        'hm_nationality': self.application_id.country_id.name.upper() if self.application_id.country_id.name else '',
                        'hm_ar_nationality': self._get_translated('res.country', 'name',
                                                                  self.application_id.country_id.name),
                        'hm_sex': self.application_id.gender.upper() if self.application_id.gender else '',
                        'hm_ar_sex': hm_ar_sex,
                        'hm_occupation': self.application_id.post_applied.name if self.application_id.full_name else '',
                        'hm_ar_occupation': self._get_translated('housemaidsystem.configuration.postapplied', 'name',
                                                                 self.application_id.post_applied.name),
                        'hm_dob': self.application_id.birth_date if self.application_id.birth_date else '',
                        'hm_passport_courier': 'PASSPORT HOLDER',
                        'hm_passport_number': self.application_id.passport_id if self.application_id.passport_id else '',
                        'hm_place_of_issue': self.application_id.place_of_birth if self.application_id.place_of_birth else '',
                        'hm_passport_type': 'ORDINARY',
                        'hm_passport_expiry': self.application_id.passport_expiry_date if self.application_id.passport_expiry_date else '',
                        'hm_office_name': self.application_id.external_office_id if self.application_id.external_office_id else '',
                        'hm_salary': self.application_id.hm_salary if self.application_id.hm_salary else 0.0,
                        'hm_deal_amount': self.hm_deal_amount if self.hm_deal_amount else 0.0,
                    }
                    self.write(application_data)

            def _fill_contract_data():
                if self.contract_date:
                    self.day_name = self.contract_date.strftime("%A")
                    if self.day_name.upper() == "SATURDAY":
                        self.day_ar_name = "السبت"
                    if self.day_name.upper() == "SUNDAY":
                        self.day_ar_name = "الأحد"
                    if self.day_name.upper() == "MONDAY":
                        self.day_ar_name = "الاثنين"
                    if self.day_name.upper() == "TUESDAY":
                        self.day_ar_name = "الثلاثاء"
                    if self.day_name.upper() == "WEDNESDAY":
                        self.day_ar_name = "الأربعاء"
                    if self.day_name.upper() == "THURSDAY":
                        self.day_ar_name = "الخميس"
                    if self.day_name.upper() == "FRIDAY":
                        self.day_ar_name = "الجمعة"
            # Update data
            # ============
            _fill_contract_data()
            _fill_branch_data()
            _fill_visa_data()
            _fill_customer_data()
            _fill_housemaid_data()

        except Exception as e:
            logger.exception("Error Title")
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        try:
            obj = super(ContractsPrint, self).create(vals)
        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)
        return obj

    def write(self, vals):
        try:
            obj = super(ContractsPrint, self).write(vals)
        except Exception as e:
            logger.exception("Write Method")
            raise ValidationError(e)
        return obj

    def unlink(self):
        try:
            return super(ContractsPrint, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)
