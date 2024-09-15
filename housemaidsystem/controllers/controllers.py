# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class HousemaidSystemController(http.Controller):

    @http.route('/readyapplications/', auth='public', website=True)
    def ready3(self, **kw):
        results = []
        applications = http.request.env['housemaidsystem.applicant.applications'].sudo().search(
            [('id', '!=', 0)])
        if applications:
            for application in applications:
                results.append({
                    'name': application.full_name,
                    'nationality': application.country_id.name,
                    'test_field': '<h1>sss</h1>',
                })

        return request.render('housemaidsystem.readyapplications_template', {'results': results})


# class Housemaid(http.Controller):
#     @http.route('/housemaidsystem/housemaidsystem/', auth='public')
#     def index(self, **kw):
#         print('sssssssssssssssss')
#         return "Hello, world"


#     @http.route('/housemaidsystem/housemaidsystem/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('housemaidsystem.listing', {
#             'root': '/housemaidsystem/housemaidsystem',
#             'objects': http.request.env['housemaidsystem.housemaidsystem'].search([]),
#         })

#     @http.route('/housemaidsystem/housemaidsystem/objects/<model("housemaidsystem.housemaidsystem"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('housemaidsystem.object', {
#             'object': obj
#         })