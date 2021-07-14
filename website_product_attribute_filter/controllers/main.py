# -*- coding: utf-8 -*-

from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main

main.PPG = 18
PPG = main.PPG


# class WebsiteSale(BisWebsiteSale):

#     def _get_search_domain_new(self, search, category):
#         domain = request.website.sale_product_domain()
#         if search:
#             for srch in search.split(" "):
#                 domain += [
#                     '|', '|', '|', ('name', 'ilike',
#                                     srch), ('description', 'ilike', srch),
#                     ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

#         if category:
#             domain += [('public_categ_ids', 'child_of', int(category))]
#         return domain

#     @http.route([
#         '''/shop''',
#         '''/shop/page/<int:page>''',
#         '''/shop/category/<model("product.public.category"):category>''',
#         '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
#     ], type='http', auth="public", website=True, sitemap=BisWebsiteSale.sitemap_shop)
#     def shop(self, page=0, category=None, search='', ppg=False, **post):
#         Product = request.env['product.template']
#         res = super(BisWebsiteSale, self).shop(
#             page, category, search, ppg, **post)
#         domain_1 = self._get_search_domain_new(search, category)
#         if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
#             domain_1.append(('is_hide_b2c', '=', False))
#         elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
#             domain_1.append(('is_hide_b2b', '=', False))
#         product_withaout_filter = Product.search(domain_1)
#         attrib_list = request.httprequest.args.getlist('attrib')
#         attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
#         attributes_ids = {v[0] for v in attrib_values}
#         attrib_set = {v[1] for v in attrib_values}
#         # attrib_set = res.qcontext['attrib_set']
#         # attributes_ids = res.qcontext['attributes_ids']
#         ProductAttribute = request.env['product.attribute']
#         attributes_ids_b = request.env[
#             'product.attribute'].browse(set(attributes_ids))
#         res.qcontext['appied_filter_result'] = attributes_ids_b
#         res.qcontext['applied_filter_values'] = attrib_set
#         attrib_category_ids = []
#         variant_count = {}

#         if product_withaout_filter:
#             attributes_ids_all = ProductAttribute.search(
#                 [('attribute_line_ids.product_tmpl_id', 'in', product_withaout_filter.ids)])
#         else:
#             attributes_ids_all = res.qcontext['attributes']
#         # domain = self._get_search_domain(search, category, attrib_values)
#         for i in range(len(attributes_ids_all)):
#             if attributes_ids_all[i].category_id and attributes_ids_all[i].value_ids and len(attributes_ids_all[i].value_ids) > 1 and attributes_ids_all[i].category_id.id not in attrib_category_ids:
#                 attrib_category_ids.append(
#                     attributes_ids_all[i].category_id.id)

#             for v in attributes_ids_all[i].value_ids:
#                 actual_domain = domain_1 + \
#                     [('attribute_line_ids.value_ids', 'in', [v.id])]
#                 variant_count.update(
#                     {v.id: Product.search_count(actual_domain)})

#         res.qcontext['attrib_category'] = request.env[
#             'product.attribute.category'].browse(set(attrib_category_ids))
#         res.qcontext['variant_counts'] = variant_count

#         return res
