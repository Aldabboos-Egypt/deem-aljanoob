# -*- coding: utf-8 -*-

from odoo import models, fields, api



class HousemaidsystemApplications(models.Model):
    _inherit = 'housemaidsystem.applicant.applications'

    einv_number= fields.Char(string='Electronic  Invoice Number', tracking=True)
    einv_date= fields.Date(string='Electronic  Invoice Date', tracking=True )
    work_permit_number= fields.Char(string='Work permit number', tracking=True)
    work_permit_date= fields.Date(string='Work permit Date', tracking=True )
    visa_grant_request= fields.Selection(string='Visa grant request', selection=[('ar', 'Arabs'),         ('fo', 'foreigners'), ], tracking=True)
    visa_grant_request_number= fields.Char(string='  Number', tracking=True)
    visa_grant_request_date= fields.Date(string='  Date', tracking=True )
    project_id= fields.Many2one(
        comodel_name='project.project',
        string='Project',
        )



class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.depends('electronic_list_ids')
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in purchase order lines.
        Then we add 1 to this value for the next sequence.
        This value is given to the context of the o2m field in the view.
        So when we create new purchase order lines, the sequence is automatically
        added as :  max_sequence + 1
        """
        for line in self:
            line.max_line_sequence = (
                    max(line.mapped('electronic_list_ids.name') or [0]) + 1)

    max_line_sequence = fields.Integer(
        string='Max sequence in lines',
        compute='_compute_max_line_sequence',
        store=True
    )

    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.electronic_list_ids:
                line.name = current_sequence
                current_sequence += 1

    def write(self, line_values):
        res = super(ProjectTask, self).write(line_values)
        self._reset_sequence()
        return res

    def copy(self, default=None):
        return super(ProjectTask, ).copy(default)

    elist_number = fields.Char(string='Electronic  List', tracking=True )
    elist_date = fields.Date(string='Electronic  List    Date', tracking=True )

    barcode_elist_number = fields.Char(string='Barcode Electronic  List', tracking=True )
    barcode_elist_date = fields.Date(string='Barcode Electronic  List Date', tracking=True )

    work_permit_number = fields.Char(string='Work permit number', tracking=True )
    work_permit_date = fields.Date(string='Work permit Date', tracking=True )

    visa_grant_request_number = fields.Char(string='Visa Number', tracking=True )
    visa_grant_request_date = fields.Date(string='  Visa Date', tracking=True )

    invoice_ids= fields.Many2many(
        comodel_name='account.move',
        string='Invoices',domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]")


    #enter

    recruitment_request   = fields.Char(string='Recruitment request   ', tracking=True )
    recruitment_request_date   = fields.Date(string='Recruitment request Date ', tracking=True )
    ministry_fees = fields.Char(string='Ministry fees  ', tracking=True )
    ministry_fees_date = fields.Date(string='fees to the Ministry Date', tracking=True )
    arab_workers_section = fields.Char(string='Arab Workers  ', tracking=True )
    arab_workers_section_date = fields.Date(string='Arab Workers   Date', tracking=True )
    workers_department_forigner = fields.Char(string=' foreign workers  ', tracking=True )
    workers_department_forigner_date = fields.Date(string='Department of foreign workers Date', tracking=True )
    a2N_email = fields.Char(string='A2N email', tracking=True )
    a2N_email_date = fields.Date(string='A2N email Date', tracking=True )
    arabs_in_residence = fields.Char(string='residence Arabs   ', tracking=True )
    arabs_in_residence_date = fields.Date(string='Book section of the Arabs in residence Date', tracking=True )
    foreigners_in_residence= fields.Char(string='residence Foreigners    ', tracking=True )
    foreigners_in_residence_date= fields.Date(string='Foreigners section book in residence Date', tracking=True )
    office_book_minister   = fields.Char(string="  office book Minister  " , tracking=True)
    office_book_minister_date   = fields.Date(string="  office book Minister  Date" , tracking=True)
    jake_insurance_ministry   = fields.Char(string='Ministry Jake     ', tracking=True )
    jake_insurance_ministry_date   = fields.Date(string='Jake Insurance to the Ministry Date', tracking=True )
    ticket_validity_book   = fields.Char(string='Ticket validity book ', tracking=True )
    ticket_validity_book_date   = fields.Date(string='Ticket validity book Date', tracking=True )

    enter_card_ids= fields.One2many(
        comodel_name='enter.card.line',
        inverse_name='task_id',
        string='Enter Card Lines', tracking=True
        )
    electronic_list_ids= fields.One2many(
        comodel_name='electronic.list',
        inverse_name='task_id',
        string='Electronic List', tracking=True
        )

    #exit
    sponsorship_transfer_date = fields.Date(string='Sponsorship Transfer Date', )
    residence_address= fields.Char(string='Residence address',)
    wish_book = fields.Char(string='wish book')
    wish_book_date = fields.Date(string='wish book Date')
    operating_request = fields.Char(string='Operating Request')
    operating_request_date = fields.Date(string='Operating Request Date')
    work_permit_request = fields.Char(string='Work Permit Request')
    work_permit_request_date = fields.Date(string='Work Permit Request Date')

    work_permit_issuing = fields.Char(string='Work Permit Issuing')
    work_permit_issuing_date = fields.Date(string='Work Permit Issuing Date')

    registering_work_id = fields.Char(string='Registering Work ID')
    registering_work_id_date = fields.Date(string='Registering Work ID Date')

    iqama_issuance = fields.Char(string='Iqama Issuance')
    iqama_issuance_date = fields.Date(string='Iqama Issuance Date')
    iqama_effective_date = fields.Date(string='Iqama effective Date')

    fine_number = fields.Char(string='Fine Number')
    fine_date = fields.Date(string='Fine Date')

    fine_reason = fields.Char(string='Fine Reason', )
    residency_transfer_place = fields.Char(string='Residency Transfer Place', )

    lawsuit= fields.Selection(
        string='Is there a lawsuit',
        selection=[('yes', 'Yes'),
                   ('no', 'NO'), ],
        )
    lawyer_name= fields.Char(string='Lawyer ', )

    exit_line_ids= fields.One2many(
        comodel_name='exit.line.card',
        inverse_name='task_id',
        string='Exit Line ', tracking=True
        )















class enter_card_line(models.Model):
    _name = 'enter.card.line'
    unknown_type_id= fields.Many2one(
        comodel_name='unknown.type',
        string='key',
        required=True)
    value= fields.Char(
        string='Value', tracking=True,
        required=True)
    date = fields.Date(
        string='Date', tracking=True,
        required=True)
    task_id= fields.Many2one(
        comodel_name='project.task', tracking=True,
        string='Task',
        required=False)


class UnknownType(models.Model):
    _name = 'unknown.type'
    name = fields.Char(required=True)





class ElectronicList(models.Model):
    _name = 'electronic.list'

    name = fields.Integer(
        help="Gives the sequence of this line  .", default=lambda self: self.task_id._reset_sequence(),
        tracking=True,readonly=True,store=True,
        string="List Number"
    )



    @api.model
    def create(self, values):
        line = super(ElectronicList, self).create(values)
        line.task_id._reset_sequence()
        return line


    employee = fields.Char(required=False, tracking=True, string="Employee")
    passport_number = fields.Char(required=False, tracking=True, string="Passport Number")
    passport_expiry_date = fields.Char(required=False, tracking=True, string="Passport Expiry Date")
    country_id = fields.Many2one(string="Country", comodel_name='res.country', tracking=True,  )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),

    ],   default="male", tracking=True)
    age = fields.Integer(required=False, tracking=True, string="Age")
    work_info = fields.Char(required=False, tracking=True, string="Work Info")
    order_state = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),

    ],   tracking=True)
    refused_reason= fields.Char(
        string='Refused Reason',
        required=False)
    notes = fields.Char(required=False, tracking=True, string="Notes")
    task_id= fields.Many2one(
        comodel_name='project.task', tracking=True,
        string='Task',
        required=False)


class ExitLineCard(models.Model):
    _name = 'exit.line.card'
    employee = fields.Char(required=False, tracking=True, string="Employee")
    passport_number = fields.Char(required=False, tracking=True, string="Passport Number")
    passport_expiry_date = fields.Char(required=False, tracking=True, string="Passport Expiry Date")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),

    ], default="male", tracking=True)
    birth_date= fields.Date(
        string='Birth Date',
        )
    nationality= fields.Char(
        string='Nationality',
        required=False)
    work = fields.Char(
        string='Work',
        required=False)
    iraq_enter_date= fields.Date(
        string='Iraq Enter Date',
        required=False)

    task_id = fields.Many2one(
        comodel_name='project.task', tracking=True,
        string='Task',
        required=False)