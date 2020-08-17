# -*- coding: utf-8 -*-
# from odoo import http


# class FontReduce(http.Controller):
#     @http.route('/font_reduce/font_reduce/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/font_reduce/font_reduce/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('font_reduce.listing', {
#             'root': '/font_reduce/font_reduce',
#             'objects': http.request.env['font_reduce.font_reduce'].search([]),
#         })

#     @http.route('/font_reduce/font_reduce/objects/<model("font_reduce.font_reduce"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('font_reduce.object', {
#             'object': obj
#         })
