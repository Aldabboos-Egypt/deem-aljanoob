from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError


logger = logging.getLogger(__name__)

class DataMigration(models.Model):
    _name = 'housemaidsystem.data_migration'
    _rec_name = 'host'
    _description = 'Data Migration'

    host = fields.Char(string="HOST", required=True, )
    db_name = fields.Char(string="DB Name", required=True, )
    user_name = fields.Char(string="DB Name", required=True, )
    password = fields.Char(string="Password", required=True, )

    # tran_date_time = fields.Datetime(string="Transaction Date", required=True, )
    # dbconnection = fields.Many2one(comodel_name="dbconnection", string="DB Connection", required=False, )
    # action_type = fields.Selection(string="Action", selection=[('vendor_upload', 'Vendor upload'),
    #                                                            ('customer_upload', 'Customer upload'),
    #                                                            ('product_upload', 'Product Upload'),
    #                                                            ('product_categ_upload', 'Product Category Upload'),
    #                                                            ('product_invoices', 'Invoices Upload'),
    #                                                            ('product_brand_upload', 'Product Brand Upload'),
    #                                                            ('error', 'Error While Executing'),
    #                                                            ('database_connection', 'Database Connection'), ],
    #                                required=False, )
    # description = fields.Text(string="Description", required=False, )



    def _cron_data_migration(self, host, db,user_name,password):
        import xmlrpc.client
        info = xmlrpc.client.ServerProxy('https://demo.odoo.com/start').start()
        url = info['host']
        db = info['database']
        username = info['user']
        password = info['password']
        return print(info)




    @api.model
    def create(self, vals):
        try:
            obj = super(DataMigration, self).create(vals)
        except Exception as e:
            logger.exception("create Method")
            raise ValidationError(e)
        return obj

    def write(self, vals):
        try:
            obj = super(DataMigration, self).write(vals)
        except Exception as e:
            logger.exception("Write Method")
            raise ValidationError(e)
        return obj

    def unlink(self):
        try:
            return super(DataMigration, self).unlink()
        except Exception as e:
            logger.exception("unlink Method")
            raise ValidationError(e)