import json
import logging
import time

import werkzeug
# from odoo.addons.website_sale.controllers.main import TableCompute as ts
from odoo import SUPERUSER_ID, _, api, fields, http, models, registry
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.controllers.main import WebsiteSale as ws
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound

_logger = logging.getLogger(__name__)

class TableCompute(object):

    def __init__(self):
        self.table = {}
    def _check_place(self, posx, posy, sizex, sizey, ppr):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= ppr:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(ppr):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=20, ppr=6):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        x = 0
        for p in products:
            x = min(max(p.website_size_x, 1), ppr)
            y = min(max(p.website_size_y, 1), ppr)
            if index >= ppg:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % ppr, pos // ppr, x, y, ppr):
                pos += 1
            # if 21st products (index 20) and the last line is full (ppr products in it), break
            # (pos + 1.0) / ppr is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) // ppr) > maxy:
                break

            if x == 1 and y == 1:   # simple heuristic for CPU optimization
                minpos = pos // ppr

            # for y2 in range(y):
            #     for x2 in range(x):
            #         self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False

            self.table[pos // ppr][pos % ppr] = {
                'product': p, 'x': x, 'y': y,
                'class': " ".join(x.html_class for x in p.website_style_ids if x.html_class)
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos // ppr))
            index += 1

        # Format table according to HTML needs
        rows = sorted(self.table.items())

        rows = [r[1] for r in rows]

        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            x += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]

        return rows


class WebsiteSale(ws):

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        print (":::::::::::::::post.get('order')::::::::::::::::::::::::::::::",post.get('order'))

        _logger.info('========post========= %s' % post)
        b2c = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')
        userobj = request.env['res.users']
        b2cusers = userobj.search([('id','=',request.uid),('groups_id','in',b2c.id)])

        public = request.env.user
        publicuser = False
        if public.partner_id.name == 'Public user':            
            publicuser = public

        if b2cusers or publicuser:
            ####add compute field on product temp from b2cprice
            order_str = post.get('order') or 'name ASC,website_sequence ASC'
            order = order_str.replace("list_price", "b2c_pricelist_price")
            # order = 'name ASC,website_sequence ASC'

        else:
            order = post.get('order') or 'name ASC,website_sequence ASC'
        _logger.info('========order111=========== %s' % post.get('order'))

        return 'priority_sequence ASC, is_published desc, %s, id desc' % order

    def _get_search_domain_new(self, search, category):
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike',
                                    srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        return domain

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']

        # When user remove category form filter
        # Redirect to shop page with all filter except category
        if int(post.get('category_remove',-1)) == 0:
            redirect_url = '/shop'
            args_dict = dict(request.httprequest.args)
            if args_dict:
                redirect_url += '?'
                for args in args_dict:
                    if args.lower() not in ['category','category_attrib','category_remove']:
                        args_value_list = request.httprequest.args.getlist(args)
                        for v in args_value_list:
                            redirect_url += f"{args}={v}&"
            return werkzeug.utils.redirect(redirect_url)
            
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            # ppg = request.env['website'].get_current_website().shop_ppg or 90
            ppg = 90
        # ppr = request.env['website'].get_current_website().shop_ppr or 90

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values)

        if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            domain.append(('is_hide_b2c', '=', False))
        elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
            domain.append(('is_hide_b2b', '=', False))

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list,
                        order=post.get('order'))
        print (":::::::::::::::::::::::::::keep:::::::::::keep::::::::::::::::::::::::::::",post.get('order'))
        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)
        print(":::::::::::self._get_search_order(post):::::::::::::::",self._get_search_order(post))
        search_product = Product.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]
        print("::::::::::::::::::::::::ppg::::::::::::::::",ppg)
        print("::::::::::::::::::::::::products::::::::::::::::",products)
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'
        ppr = 6

        domain_1 = self._get_search_domain_new(search, category)
        if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            domain_1.append(('is_hide_b2c', '=', False))
        elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
            domain_1.append(('is_hide_b2b', '=', False))
        product_without_filter = Product.search(domain_1)
        ProductAttribute = request.env['product.attribute']
        attributes_ids_b = request.env[
            'product.attribute'].browse(set(attributes_ids))
        appied_filter_result = attributes_ids_b
        applied_filter_values = attrib_set
        attrib_category_ids = []
        variant_count = {}

        if product_without_filter:
            attributes_ids_all = ProductAttribute.search(
                [('attribute_line_ids.product_tmpl_id', 'in', product_without_filter.ids)])
        else:
            attributes_ids_all = attributes
        for i in range(len(attributes_ids_all)):
            if attributes_ids_all[i].category_id and attributes_ids_all[i].value_ids and len(attributes_ids_all[i].value_ids) > 1 and attributes_ids_all[i].category_id.id not in attrib_category_ids:
                attrib_category_ids.append(
                    attributes_ids_all[i].category_id.id)

            for v in attributes_ids_all[i].value_ids:
                actual_domain = domain_1 + \
                    [('attribute_line_ids.value_ids', 'in', [v.id])]
                variant_count.update(
                    {v.id: Product.search_count(actual_domain)})

        attrib_category = request.env[
            'product.attribute.category'].browse(set(attrib_category_ids))
        variant_counts = variant_count
    
        values = {
            'search': search,
            'category': category,
            'current_category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, 90, ppr),
            'ppg': 90,
            'ppr': ppr,
            'categories': categs,
            'public_categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            
            'appied_filter_result': appied_filter_result,
            'applied_filter_values': applied_filter_values,
            'attrib_category': attrib_category,
            'variant_counts': variant_counts
        }
        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)



    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        user_obj=request.env['res.users']

        b2bid = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
        group_list = [b2bid.id]

        comments = post.get('comments')

        _logger.info('========comments=========== %s' % comments)
        order.write({'note':comments})  

        user_data=user_obj.search([('id','=',request.uid),('groups_id','in',group_list)])
        if user_data:
            order.b2b_confirmed = True
            order.action_quotation_sent()
            mail_template = request.env.ref('sale.mail_template_sale_confirmation')
            mail_template.send_mail(order.id, force_send=True)
            order.action_draft()
            return request.redirect('/shop/confirmation')


        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if order and not order.amount_total and not tx:
            order.with_context(send_email=True).action_confirm()
            return request.redirect(order.get_portal_url())

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        _logger.info('========PaymentProcessing=========== %s' % PaymentProcessing)   
        PaymentProcessing.remove_payment_transaction(tx)
        return request.redirect('/shop/confirmation')

    def _get_products_recently_viewed(self):
        """
        Returns list of recently viewed products according to current user
        """
        max_number_of_product_for_carousel = 12
        visitor = request.env['website.visitor']._get_visitor_from_request()
        is_user_public_b2c = False
        is_user_admin_b2b = False
        if visitor:
            excluded_products = request.website.sale_get_order().mapped('order_line.product_id.id')
            products = request.env['website.track'].sudo().read_group(
                [('visitor_id', '=', visitor.id), ('product_id', '!=', False), ('product_id.website_published', '=', True), ('product_id', 'not in', excluded_products)],
                ['product_id', 'visit_datetime:max'], ['product_id'], limit=max_number_of_product_for_carousel, orderby='visit_datetime DESC')
            products_ids = [product['product_id'][0] for product in products]
            if products_ids:
                viewed_products = request.env['product.product'].with_context(display_default_code=False).browse(products_ids)
                if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
                    is_user_public_b2c = True
                    viewed_products = [x for x in viewed_products if not x.product_tmpl_id.is_hide_b2c]
                elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount') or request.env.user.user_has_groups('base.group_system'):
                    is_user_admin_b2b = True
                    viewed_products = [x for x in viewed_products if not x.product_tmpl_id.is_hide_b2b]

                FieldMonetary = request.env['ir.qweb.field.monetary']
                monetary_options = {
                    'display_currency': request.website.get_current_pricelist().currency_id,
                }
                rating = request.website.viewref('website_sale.product_comment').active
                res = {'products': []}
                for product in viewed_products:
                    pricelist_context, pricelist = self._get_pricelist_context()
                    combination_info = product._get_combination_info_variant(pricelist=pricelist)
                    res_product = product.read(['id', 'name', 'website_url', 'b2c_old_price', 'b2b_old_price', 'b2c_pricelist_price'])[0]
                    res_product.update(combination_info)
                    res_product['price'] = FieldMonetary.value_to_html(res_product['price'], monetary_options)
                    res_product['b2c_old_price_html'] = FieldMonetary.value_to_html(res_product['b2c_old_price'], monetary_options)
                    res_product['b2b_old_price_html'] = FieldMonetary.value_to_html(res_product['b2b_old_price'], monetary_options)
                    if rating:
                        res_product['rating'] = request.env["ir.ui.view"].render_template('website_rating.rating_widget_stars_static', values={
                            'rating_avg': product.rating_avg,
                            'rating_count': product.rating_count,
                        })
                    res_product['is_user_public_b2c'] = is_user_public_b2c
                    res_product['is_user_admin_b2b'] = is_user_admin_b2b
                    res['products'].append(res_product)

                return res
        return {}

    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        """
        Returns list of products according to the term and product options

        Params:
            term (str): search term written by the user
            options (dict)
                - 'limit' (int), default to 5: number of products to consider
                - 'display_description' (bool), default to True
                - 'display_price' (bool), default to True
                - 'order' (str)
                - 'max_nb_chars' (int): max number of characters for the
                                        description if returned

        Returns:
            dict (or False if no result)
                - 'products' (list): products (only their needed field values)
                        note: the prices will be strings properly formatted and
                        already containing the currency
                - 'products_count' (int): the number of products in the database
                        that matched the search query
        """
        ProductTemplate = request.env['product.template']

        display_description = options.get('display_description', True)
        display_price = options.get('display_price', True)
        order = self._get_search_order(options)
        max_nb_chars = options.get('max_nb_chars', 999)

        category = options.get('category')
        attrib_values = options.get('attrib_values')

        domain = self._get_search_domain(term, category, attrib_values, display_description)

        if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            domain.append(('is_hide_b2c', '=', False))
        elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
            domain.append(('is_hide_b2b', '=', False))

        products = ProductTemplate.search(
            domain,
            limit=min(20, options.get('limit', 5)),
            order=order
        )

        fields = ['id', 'name', 'website_url']
        if display_description:
            fields.append('description_sale')

        res = {
            'products': products.read(fields),
            'products_count': ProductTemplate.search_count(domain),
        }

        if display_description:
            for res_product in res['products']:
                desc = res_product['description_sale']
                if desc and len(desc) > max_nb_chars:
                    res_product['description_sale'] = "%s..." % desc[:(max_nb_chars - 3)]

        if display_price:
            FieldMonetary = request.env['ir.qweb.field.monetary']
            monetary_options = {
                'display_currency': request.website.get_current_pricelist().currency_id,
            }
            for res_product, product in zip(res['products'], products):
                combination_info = product._get_combination_info(only_template=True)
                res_product.update(combination_info)
                res_product['list_price'] = FieldMonetary.value_to_html(res_product['list_price'], monetary_options)
                res_product['price'] = FieldMonetary.value_to_html(res_product['price'], monetary_options)
        return res
    

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(product, category, search, **kwargs)
        if res.qcontext.get('categories'):
            res.qcontext.update({
                'public_categories': res.qcontext.get('categories'),
                'current_category': res.qcontext.get('category')
            })
        return res
    
    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def checkout(self, **post):
        res = super(WebsiteSale, self).checkout(**post)

        if post.get('express'):
            # If user write qty directly in qty box and click process checkout
            # Wait some time for update qty in backend before going to payment page
            time.sleep(3)
            # return request.redirect('/shop/confirm_order')

        return res
    
    @http.route('/check_delivery_address', type='json', auth='public', website=True)
    def check_delivery_address(self, postal_code, **kwargs):
        """
        Free delivery or not based on zip code/postal code
        """
        gta_code_obj = request.env['gta.code']
        free_delivery = False
        if postal_code:
            value = str(postal_code)[:3].strip()
            postal_code_exits = gta_code_obj.search([('postal_code','ilike',value)])
            if postal_code_exits:
                free_delivery = True
        return {'free_delivery': free_delivery}
   
    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        res = super(WebsiteSale, self).payment(**post)
        order = request.website.sale_get_order()
        deliveries = res.qcontext['deliveries']
        gta_shipping_method = deliveries.filtered(lambda x: x.is_gta_code)
        select_free_delivery = False
        if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            zip_code = order.partner_shipping_id.zip
            if zip_code:
                select_free_delivery = self.check_delivery_address(zip_code)['free_delivery']
                       
        if gta_shipping_method:
            if select_free_delivery:
                # Check the shipping method true based on price ruled
                status_based_rule = gta_shipping_method.base_on_rule_rate_shipment(order)
                if status_based_rule.get('success'):
                    order.carrier_id = gta_shipping_method[0].id
                    res.qcontext['deliveries'] = gta_shipping_method[0]
            else:
                res.qcontext['deliveries'] = deliveries.filtered(
                                            lambda x: x.id != gta_shipping_method[0].id)

        return res
    

    @http.route(['/check-postal-code'], type='http', auth="public", website=True)
    def check_postal_code(self, **post):
        if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            return request.render("bista_superasia_theme.check_postal_code", {})
            
        return request.not_found()