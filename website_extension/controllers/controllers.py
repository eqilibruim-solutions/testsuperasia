# -*- coding: utf-8 -*-
# from odoo import http


# class WebsiteExtension(http.Controller):
#     @http.route('/website_extension/website_extension/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/website_extension/website_extension/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_extension.listing', {
#             'root': '/website_extension/website_extension',
#             'objects': http.request.env['website_extension.website_extension'].search([]),
#         })

#     @http.route('/website_extension/website_extension/objects/<model("website_extension.website_extension"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_extension.object', {
#             'object': obj
#         })
