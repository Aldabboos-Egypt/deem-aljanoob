# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from odoo.modules.module import get_module_resource
from odoo import tools, _
from odoo.exceptions import ValidationError
import datetime
from dateutil import parser
import logging


logger = logging.getLogger(__name__)

class ReturnBack(models.Model):
    _name = 'housemaidsystem.applicant.returnback'
    _description = 'Return Back'

    # ================ constraints =================================
    _sql_constraints = [
            ('application_id_uniqe', 'unique (application_id)', "Tag application already exists !"),
      ]

    # ==================  Main Functions ==========================

    def action_cancel_returnback(self):
        application_id = self.application_id
        if application_id:
            application_id.state = 'deliver'
        self.unlink()

    # ================ Compute functions=================================

    @api.depends('application_id')
    def _compute_name(self):
        for record in self:
            self.name = self.application_id.name


    def _get_labor_dtl(self):
        for record in self:
            if not record.application_id == None:
                self.labor_image = record.application_id.labor_image
                self.full_name = record.application_id.full_name
                self.code = record.application_id.code
                self.office_code = record.application_id.office_code
                domain = [('application_id', '=', record.application_id.id)]
                reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(domain)
                if reservation_obj:
                    record.invoice_id = reservation_obj.invoice_id

    # ================ Create / write / unlink functions================
    @api.model
    def create(self, vals):
        try:
            if not (vals.get('customer_id', False) or vals.get('invoice_id', False)):
                domain = [('application_id', '=', vals['application_id'])]
                reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(domain)
                if reservation_obj:
                    vals['customer_id'] = reservation_obj.customer_id.id
                    vals['invoice_id'] = reservation_obj.invoice_id.id

            returnback_obj = super(ReturnBack, self).create(vals)

            if vals.get('application_id'):
                applications_obj = self.env['housemaidsystem.applicant.applications'].browse(vals.get('application_id'))
                applications_obj.state = 'deliver'

            return returnback_obj
        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)




    def write(self, vals):
        try:
            if not (vals.get('customer_id', False) or vals.get('invoice_id', False)):
                domain = [('application_id', '=', vals['application_id'])]
                reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(domain)
                if reservation_obj:
                    vals['customer_id'] = reservation_obj.customer_id.id
                    vals['invoice_id'] = reservation_obj.invoice_id.id
            res = super(ReturnBack, self).write(vals)
            return res

        except Exception as e:
            logger.exception("write Method")
            raise ValidationError(e)





    def unlink(self):
        try:
            for record in self:
                if record.application_id:
                    applications_obj = record.application_id
                    applications_obj.state = 'arrival'
            return super(ReturnBack, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)

    # ================ On Change Functions =================================

    @api.onchange('application_id')
    @api.depends('customer_id')
    def onchange_get_customer_name(self):
        for rec in self:
            # ------------------------------------------------------
            # get customer details
            if rec.application_id:
                domain = [('application_id', '=', rec.application_id.id)]
                reservation_obj = self.env['housemaidsystem.applicant.reservations'].search(domain)
                if reservation_obj:
                    rec.customer_id = reservation_obj.customer_id.id
                    rec.invoice_id = reservation_obj.invoice_id.id

    # ================ Fields =================================
    name = fields.Char(string="Name", compute='_compute_name')
    return_back_date = fields.Date(string="Return Back Date", required=True, default=fields.Date.context_today)
    application_id = fields.Many2one(comodel_name="housemaidsystem.applicant.applications", string="Applications",
                                     required=True, domain=[('state', '=', 'deliver')])
    refund = fields.Float(string="Refund", default=0)
    notes = fields.Text(string="Notes")
    customer_id = fields.Many2one(comodel_name="res.partner", string="Sponsor")
    state = fields.Selection(string='Application Status', readonly=True,
                                          related='application_id.state')
    # ================== Related Fields====================================================
    labor_image = fields.Binary("Photo",compute='_get_labor_dtl')
    full_name = fields.Char(string="Full Name", compute='_get_labor_dtl')
    code = fields.Char(string="Code", compute='_get_labor_dtl')
    office_code = fields.Many2one('housemaidsystem.configuration.externaloffices',
                                  string="External Office", compute='_get_labor_dtl')
    invoice_id = fields.Many2one('account.move', 'Invoice',store='True')