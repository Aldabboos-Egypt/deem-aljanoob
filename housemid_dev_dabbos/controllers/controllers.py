# -*- coding: utf-8 -*-
# from odoo import http


# class HousemidDevDabbos(http.Controller):
#     @http.route('/housemid_dev_dabbos/housemid_dev_dabbos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/housemid_dev_dabbos/housemid_dev_dabbos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('housemid_dev_dabbos.listing', {
#             'root': '/housemid_dev_dabbos/housemid_dev_dabbos',
#             'objects': http.request.env['housemid_dev_dabbos.housemid_dev_dabbos'].search([]),
#         })

#     @http.route('/housemid_dev_dabbos/housemid_dev_dabbos/objects/<model("housemid_dev_dabbos.housemid_dev_dabbos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('housemid_dev_dabbos.object', {
#             'object': obj
#         })
