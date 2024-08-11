# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class Housemaidlist(http.Controller):

    @http.route('/list/', auth='public', type='http', website=True)
    def index(self, **kw):
        return "Hello, worlds"






    @http.route('/applicationslist/', auth='public', type='http', website=True)
    def render_example_page(self, **kw):
        applications = http.request.env['housemaidsystem.applicant.applications'].sudo().search(
            [('state', '=', 'application')])
        return http.request.render('housemaidsystem.website_applicationslist_template', {'applications': applications})



    # def patient_webform(self, **kw):
    #     print("Execution Here.........................")
    #     doctor_rec = request.env['hospital.doctor'].sudo().search([])
    #     print("doctor_rec...", doctor_rec)
    #     return http.request.render('om_hospital.create_patient', {'patient_name': 'Odoo Mates Test 123',
    #                                                               'doctor_rec': doctor_rec})

# return http.request.render('housemaidsystem.website_applicationslist_template', {'applications': applications}

    @http.route('/housemaidlist/details', auth='public', type='http', website=True)
    def navigate_to_detail_page(self):
        return http.request.render('housemaidsystem.housemaidlist_detail_page', {})



# class Housemaid(http.Controller):
#     @http.route('/housemaidsystem/housemaidsystem/', auth='public')
#     def index(self, **kw):
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
