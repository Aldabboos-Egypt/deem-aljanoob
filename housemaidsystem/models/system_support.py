# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import ValidationError
from . import accounting_integration
import logging

logger = logging.getLogger(__name__)


class SystemSupport(models.Model):
    _name = 'housemaidsystem.system.support'

    name = fields.Char(string="Name", required=True, )
    description = fields.Text(string="Description", required=True, )
    document_url = fields.Char(string="URL", required=True, )
    document_type = fields.Selection(string="Classifications",
                                     selection=[('sales', 'Sales'), ('accounting', 'Accounting'), ('report', 'Report'),
                                                ('configuration', 'Configuration'), ], default='sales', required=True, )
