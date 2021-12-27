from werkzeug import Response
import werkzeug.utils
import logging
_logger = logging.getLogger(__name__)

from odoo import http, fields, tools, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.bista_superasia_theme.controllers.main import TableCompute, WebsiteSale as BistaWebsiteSale
from odoo.addons.web.controllers.main import Home
from odoo.addons.superasiab2b_b2c.controllers.main import superasiab2b_b2c
from odoo.addons.website.controllers.main import QueryURL
from werkzeug.exceptions import Forbidden, NotFound

class Extension_Home(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        response = super(Extension_Home, self).web_login()
        request.session['sales_rep_user'] = False
        if request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            request.session['sales_rep_user'] = True
            return werkzeug.utils.redirect('/sales-rep/home')
        return response


class SalesAgentDashboard(WebsiteSale):
    def is_assigned(self, partner_id):
        """ Check is the partner assigned to current logged in sales rep"""
        partner_obj = request.env['res.partner'].browse(partner_id)
        return partner_obj.assigned_sale_rep.id == request.env.user.id

    def account_form_values_preprocess(self, values):
        # Convert the values for many2one fields to integer since they are used as IDs
        partner_fields = request.env['res.partner']._fields
        return {
            k: (bool(v) and int(v)) if k in partner_fields and partner_fields[k].type == 'many2one' else v
            for k, v in values.items()
        }

    def add_account_form_validate(self, all_form_values):
        """Check validation of form.

        Args:
            all_form_values ([dict]): form values

        Returns:
            error [dict]: {'field_name': 'error_type[missing/error]'}
            error_message [list]: details about error message
        """
        error = dict()
        error_message = []

        # Required fields from form
        required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
        # Required fields from mandatory field function
        required_fields += self._get_mandatory_billing_fields()
        # Check if state required
        country = request.env['res.country']
        if all_form_values.get('country_id'):
            country = country.browse(int(all_form_values.get('country_id')))
            if 'state_code' in country.get_address_fields() and country.state_ids:
                required_fields += ['state_id']

        # error message for empty required fields
        for field_name in required_fields:
            if not all_form_values.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if all_form_values.get('email') and not tools.single_email_re.match(all_form_values.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        return error, error_message

    def account_form_values_postprocess(self, mode, values, errors, error_msg):
        new_values = {}
        authorized_fields = request.env['ir.model']._get('res.partner')._get_form_writable_fields()
        for k, v in values.items():
            # don't drop empty value, it could be a field to reset
            if k in authorized_fields and v is not None:
                new_values[k] = v
            else:  # DEBUG ONLY
                if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
                    _logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)
        new_values['mobile'] = values.get('mobile')
        new_values['b2b_customer_type'] = values.get('b2b_customer_type')
        new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
        new_values['user_id'] = request.website.salesperson_id and request.website.salesperson_id.id

        if request.website.specific_user_account:
            new_values['website_id'] = request.website.id

        if mode[0] == 'new':
            new_values['company_id'] = request.website.company_id.id

        lang = request.lang.code if request.lang.code in request.website.mapped('language_ids.code') else None
        if lang:
            new_values['lang'] = lang
        return new_values, errors, error_msg

    @http.route(['/sales-rep/home'], type='http', methods=['GET'], auth="user", website=True, csrf=False)
    def sales_agent_home(self, **post):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        b2b_user_group = request.env['ir.model.data'].sudo().get_object(
            'superasiab2b_b2c', 'group_b2baccount')
        userobj = request.env['res.users'].sudo()
        b2b_users = userobj.search([('groups_id','in',b2b_user_group.id)])
        b2b_partner_ids = []
        if b2b_users:
            b2b_partner_ids = b2b_users.mapped('partner_id').filtered(
                lambda p: p.assigned_sale_rep == request.env.user)

        request.website.sale_reset()
        request.session['selected_partner_id'] = False
        return request.render('superasia_salesrep_app.sales_agent_home',{
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
             
            'b2b_partner_ids': b2b_partner_ids,
        })
    
    @http.route(['/sales-rep/all-accounts'], type='http', methods=['GET'], auth="user", website=True, csrf=False)
    def sales_agent_accounts(self, **post):
        """
        Path/page for show list of b2b account.
        """
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        b2b_user_group = request.env['ir.model.data'].sudo().get_object(
            'superasiab2b_b2c', 'group_b2baccount')
        # if b2b_user_group:
        #     b2b_partner_ids = b2b_user_group.users.mapped('partner_id')
        userobj = request.env['res.users'].sudo()
        b2b_users = userobj.search([('groups_id','in',b2b_user_group.id)])
        b2b_partner_ids = []
        if b2b_users:
            b2b_partner_ids = b2b_users.mapped('partner_id').filtered(
                lambda p: p.assigned_sale_rep == request.env.user)

        # Filter
        if post.get('city'):
            filter_city_list = request.httprequest.args.getlist('city')
            b2b_partner_ids = b2b_partner_ids.filtered(
                lambda x: x.city in filter_city_list)
        context = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'b2b_partner_ids': b2b_partner_ids,
        }
        return request.render('superasia_salesrep_app.sales_rep_accounts', context)
    

    @http.route(['/sales-rep/account/create'], type='http', methods=['GET', 'POST'], auth="user", website=True, sitemap=False)
    def sales_agent_create_account(self, **post):
        """
        Path/page for creating b2b user account by sales rep.
        """
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        
        values, errors = {}, {}
        partner_id = False
        mode = 'new'

        # IF POSTED
        if 'submitted' in post:
            pre_values = self.account_form_values_preprocess(post)
            errors, error_msg = self.add_account_form_validate(pre_values)
            post, errors, error_msg = self.account_form_values_postprocess(mode, pre_values, errors, error_msg)
            if errors:
                errors['error_message'] = error_msg
                values = post
            else:
                user_obj = request.env['res.users'].sudo()
                exists_user = user_obj.search([('login','=',post.get('email'))])
                if exists_user:
                    # TODO: modified repeat_user path template for sales rep user
                    return request.redirect('/repeat_user')

                b2b_group = request.env['ir.model.data'].sudo().get_object('superasiab2b_b2c','group_b2baccount')
                portal_group = request.env['ir.model.data'].sudo().get_object('base','group_portal')

                group_list = [b2b_group.id, portal_group.id]

                email = post.get('email')
                company_name = post.get('name')
                user_val = {
                    'name': post.get('name'),
                    'login' : email ,
                    'password':'Admin@123',
                    'groups_id':[(6,0,group_list)],
                    'active':False
                }
            
                user_data = user_obj.create(user_val)
                user_id = user_data.id

                partner_id = user_data.partner_id

                post.update({
                    'company_type': 'company',
                    'assigned_sale_rep': request.env.user.id
                })
                partner_id.write(post)

            
                if partner_id:
                    ir_mail_server = request.env['ir.mail_server']
                    mail_server_id = ir_mail_server.sudo().search([('name','=','Superasia')])
                    smtp_user = str(mail_server_id.smtp_user)
                    temp_obj = request.env['mail.template']
                    template_data = temp_obj.sudo().search([('name','=','Account Activation')])
                    if template_data:
                        replaced_data = template_data.body_html.replace(
                            '${object.company_name}', company_name)
                        replaced_dataone = replaced_data.replace(
                            '${object.email}', email)
                        msg = ir_mail_server.build_email(
                            email_from=smtp_user,
                            email_to=[email],
                            subject="Account Activation",
                            body=replaced_dataone,
                            body_alternative="",
                            object_id=1,
                            subtype='html'
                        )
                        res = mail_server_id.send_email(msg)
                        admin_mail_template = "B2B Account Activation Request"
                        superasiab2b_b2c.send_admin_activation_mail(
                            admin_mail_template, company_name, email, user_id, company_name, company_name, "", post.get('mobile'), post.get('street'))
                    else:
                        # TODO: raise an error to user
                        print("Account activation mail to admin not sent")
                    # TODO: made a confirmation page for successfully create user
                    return request.redirect(post.get('callback') or '/sales-rep/all-accounts')
        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or None
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        b2b_customer_type_fields = dict(request.env['res.partner'].fields_get(
                allfields=['b2b_customer_type'])['b2b_customer_type']['selection'])
        render_values = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'mode': mode,
            "partner_id": partner_id,
            'form_values': values,
            'error': errors,
            'country': country,
            'countries': countries,
            "states": states,
            "b2b_customer_type_fields": b2b_customer_type_fields,
        }
        return request.render('superasia_salesrep_app.sales_rep_add_account', render_values)

    @http.route(['/sales-rep/account/<int:partner_id>/update'], type='http', methods=['GET', 'POST'], auth="user", website=True, sitemap=False)
    def sales_agent_update_account(self, partner_id, **post):
        """
        Path/page for updating b2b user account by sales rep.
        """
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        partner_obj = Partner.browse(partner_id)
        values, errors = {}, {}
        if not partner_obj and not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        if not self.is_assigned(partner_id):
            raise Forbidden() 
        values = partner_obj
        def_country_id = partner_obj.country_id
        mode = 'edit'

        # IF POSTED
        if 'submitted' in post:
            pre_values = self.account_form_values_preprocess(post)
            errors, error_msg = self.add_account_form_validate(pre_values)
            post, errors, error_msg = self.account_form_values_postprocess(mode, pre_values, errors, error_msg)
            if errors:
                errors['error_message'] = error_msg
                values = post
            else:
                partner_obj.sudo().write(post)
                detail_page_url = f"/sales-rep/account/{partner_id}/details"
                return request.redirect(post.get('callback') or detail_page_url)
        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or def_country_id
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        b2b_customer_type_fields = dict(Partner.fields_get(
                allfields=['b2b_customer_type'])['b2b_customer_type']['selection'])
        render_values = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'mode': mode,
            "partner_id": partner_id,
            'form_values': values,
            'error': errors,
            'country': country,
            'countries': countries,
            "states": states,
            "b2b_customer_type_fields": b2b_customer_type_fields,
        }
        return request.render('superasia_salesrep_app.sales_rep_add_account', render_values)

    @http.route(['/sales-rep/account/<int:partner_id>/details'], type='http', methods=['GET'], auth="user", website=True, csrf=False)
    def sales_agent_b2b_details(self, partner_id, **kw):
        partner_obj = request.env['res.partner'].browse(partner_id)
        if not partner_obj or not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        if not self.is_assigned(partner_id):
            raise Forbidden()
        country = partner_obj.country_id
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        b2b_customer_type_fields = dict(request.env['res.partner'].fields_get(
                allfields=['b2b_customer_type'])['b2b_customer_type']['selection'])
        form_values = {
            'name': partner_obj.name,
            'street': partner_obj.street,
            'city': partner_obj.city,
            'zip': partner_obj.zip,
            'state_id': partner_obj.state_id,
            'phone': partner_obj.phone,
            'mobile': partner_obj.mobile,
            'email': partner_obj.email,
            'b2b_customer_type': partner_obj.b2b_customer_type,
        }
        render_values = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'partner_id': partner_obj,
            'error': {},
            'form_values': form_values,
            'country': country,
            'countries': countries,
            "states": states,
            'b2b_customer_type_fields': b2b_customer_type_fields,
        }
        return request.render('superasia_salesrep_app.sales_rep_account_detail', render_values)
    
    @http.route(['/selected-account/update'], type='json', auth="user", website=True)
    def update_selected_account(self, account_id):
        request.session['selected_partner_id'] = int(account_id)
        request.website.sale_reset()
        return {
            'redirect_url': '/sales-rep/sale/'
        }
    @http.route(['/sales-rep/account/<int:partner_id>/sales'], type='http', methods=['GET'], auth="user", website=True, csrf=False)
    def sales_agent_partner_sales(self, partner_id, **kw):
        """ All sale order record for given partner"""
        partner_obj = request.env['res.partner'].browse(partner_id)
        if not partner_obj or not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        sale_orders = []
        res_partner = request.env['res.partner']
        all_partners = res_partner.with_context(active_test=False).search([('id', 'child_of', partner_obj.ids)])
        all_partners.read(['parent_id'])

        sale_orders = request.env['sale.order'].search([('partner_id', 'in', all_partners.ids)])
        
        context = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'partner_id': partner_obj,
            'sale_orders': sale_orders
            
        }
        return request.render('superasia_salesrep_app.sales_rep_account_sale', context)
    

    @http.route(['/sales-rep/account/<int:partner_id>/dues'], type='http', methods=['GET'], auth="user", website=True, csrf=False)
    def sales_agent_partner_dues(self, partner_id, **kw):
        """ All Due invoice records for given partner"""
        partner_obj = request.env['res.partner'].browse(partner_id)
        if not partner_obj or not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()

        context = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'partner_id': partner_obj,
            'due_invoices': partner_obj.unpaid_invoices,
            
        }
        return request.render('superasia_salesrep_app.sales_rep_account_due', context)

    @http.route([
        '''/sales-rep/catalogue''',
        '''/sales-rep/catalogue/page/<int:page>''',
        '''/sales-rep/catalogue/category/<model("product.public.category"):category>''',
        '''/sales-rep/catalogue/category/<model("product.public.category"):category>/page/<int:page>'''
        ], type='http', auth="user", website=True)
    def sales_rep_catalogue_shop(self, page=0, category=None, search='', ppg=False, **post):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        request.session['selected_partner_id'] = False
        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']

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
            ppg = 30
        # ppr = request.env['website'].get_current_website().shop_ppr or 90
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        domain = self._get_search_domain(search, category, attrib_values)
        domain.append(('is_hide_b2b', '=', False))

        keep = QueryURL('/sales-rep/catalogue', category=category and int(category), search=search, attrib=attrib_list,
                        order=post.get('order'))
        pricelist_context, pricelist = self._get_pricelist_context()
        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/sales-rep/catalogue"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)
        search_product = Product.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain

        
        search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/sales-rep/catalogue/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        layout_mode = 'grid'
        ppr = 2

        domain_1 = self._get_search_domain_new(search, category)
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
            'bins': TableCompute().process(products, 30, ppr),
            'ppg': 30,
            'ppr': ppr,
            'categories': categs,
            'public_categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'selected_partner': False,
            
            'appied_filter_result': appied_filter_result,
            'applied_filter_values': applied_filter_values,
            'attrib_category': attrib_category,
            'variant_counts': variant_counts,

            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
        }
        if category:
            values['main_object'] = category

        return request.render('superasia_salesrep_app.sales_rep_catalogue_product', values)

    
    @http.route([
        '''/sales-rep/sale''',
        '''/sales-rep/sale/page/<int:page>''',
        '''/sales-rep/sale/category/<model("product.public.category"):category>''',
        '''/sales-rep/sale/category/<model("product.public.category"):category>/page/<int:page>'''
        ], type='http', auth="user", website=True)
    def sales_rep_sale_shop(self, page=0, category=None, search='', ppg=False, **post):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        partner_id = request.session.get('selected_partner_id')
        if partner_id:
            selected_partner = request.env['res.partner'].browse(partner_id)
        else:
            return werkzeug.utils.redirect('/sales-rep/home')

        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']

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
            ppg = 30
        # ppr = request.env['website'].get_current_website().shop_ppr or 90
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        domain = self._get_search_domain(search, category, attrib_values)
        domain.append(('is_hide_b2b', '=', False))

        keep = QueryURL('/sales-rep/sale', category=category and int(category), search=search, attrib=attrib_list,
                        order=post.get('order'))
        pricelist_context, pricelist = self._get_pricelist_context()
        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/sales-rep/sale"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)
        search_product = Product.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain

        # if search:
        #     search_categories = Category.search(
        #         [('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
        #     categs_domain.append(('id', 'in', search_categories.ids))
        # else:
        #     search_categories = Category
        
        search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/sales-rep/sale/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        # layout_mode = request.session.get('website_sale_shop_layout_mode')
        # if not layout_mode:
        #     if request.website.viewref('website_sale.products_list_view').active:
        #         layout_mode = 'list'
        #     else:
        #         layout_mode = 'grid'
        layout_mode = 'grid'
        ppr = 2

        domain_1 = self._get_search_domain_new(search, category)
        domain_1.append(('is_hide_b2b', '=', False))
        # if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
        #     domain_1.append(('is_hide_b2c', '=', False))
        # elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
        #     domain_1.append(('is_hide_b2b', '=', False))
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
            'bins': TableCompute().process(products, 30, ppr),
            'ppg': 30,
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
            'variant_counts': variant_counts,
            'selected_partner': selected_partner,

            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
        }
        if category:
            values['main_object'] = category

        return request.render('superasia_salesrep_app.sales_rep_product_listing', values)


    @http.route(['/sales-rep/sale/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product_info(self, product, category='', search='', **kwargs):
        if not product.can_access_from_current_website():
            raise NotFound()
        context = self._prepare_product_values(product, category, search, **kwargs)
        context.update({
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
        })
        return request.render("superasia_salesrep_app.sales_rep_product_info", context)

    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        response = super(SalesAgentDashboard, self).cart(**post)
        if request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            partner_id = request.session.get('selected_partner_id')
            if partner_id:
                selected_partner = request.env['res.partner'].browse(partner_id)
            else:
                return werkzeug.utils.redirect('/sales-rep/home')
            response.qcontext.update({
                'selected_partner': selected_partner,
                'footer_hide': True,
                'hide_install_pwa_btn': True,
                'hide_header': True,
            })
        return response

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        if not kw.get('country_id') and kw.get('shipping_country_id'):
            kw.update({
                'country_id': kw.get('shipping_country_id')
            })
        if not kw.get('state_id') and kw.get('shipping_state_id'):
            kw.update({
                'state_id': kw.get('shipping_state_id')
            })
        response = super(SalesAgentDashboard, self).address(**kw)
        if request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            response.qcontext.update({
                'footer_hide': True,
                'hide_install_pwa_btn': True,
                'hide_header': True,
            })
        return response

    @http.route(['/sales-rep/sale/sale-order'], type='http', auth="public", website=True, sitemap=False)
    def sale_order_details(self, **kw):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            raise NotFound()
        partner_id = request.session.get('selected_partner_id')
        if partner_id:
            selected_partner = request.env['res.partner'].browse(partner_id)
        else:
            return werkzeug.utils.redirect('/sales-rep/home')
        # TODO: check there have any product add in order, if none then return to cart page.
        order = request.website.sale_get_order()
        kw.update({'partner_id': order.partner_shipping_id.id})
        context = self.checkout_values(**kw)
        def_country_id = order.partner_id.country_id
        shipping_values, errors = {}, {}
        new_shipping_address, new_shipping_errors = {}, {}
        shipping_values = order.partner_shipping_id
        partner_id = int(kw.get('partner_id', -1))
        
        country = 'country_id' in shipping_values and shipping_values['country_id'] != '' and request.env['res.country'].browse(int(shipping_values['country_id']))
        country = country and country.exists() or def_country_id
        context.update({
            'date': fields.Date.today(),
            'selected_partner': selected_partner,
            'shipping_values': shipping_values,
            'new_shipping_address': new_shipping_address,
            'country': country,
            'countries': country.get_website_sale_countries(),
            "states": country.get_website_sale_states(),
            'error': errors,
            'new_shipping_error': new_shipping_errors,
            'callback': '/sales-rep/sale/sale-order',
            
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
        })
        return request.render("superasia_salesrep_app.sales_rep_order_detail", context)
    
    @http.route(['/sales-rep/cart/update_discount'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_discount(self, product_id, line_id=None, add_qty=None, set_discount=None, display=True):
        """This route is called when need to add discount from the cart"""
        order = request.website.sale_get_order()
        order_line = False
        if line_id is not False:
            order_line = request.env['sale.order.line'].sudo().browse(int(line_id))
            # order_line = order._cart_find_product_line(product_id, line_id)[:1]

        value = {}
        if order_line:
            order_line.write({
                'discount' : float(set_discount) if set_discount else 0.0,
                'discount_manual_update': True
            })
            value['done'] = True
        value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': order._cart_accessories()
        })
        value['website_sale.short_cart_summary'] = request.env['ir.ui.view'].render_template("website_sale.short_cart_summary", {
            'website_sale_order': order,
        })
        return value
    
    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        response = super(SalesAgentDashboard, self).payment_confirmation(**post)
        if request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            sale_order_id = request.session.get('sale_last_order_id')
            if sale_order_id:
                response.qcontext.update({
                    'footer_hide': True,
                    'hide_install_pwa_btn': True,
                    'hide_header': True,
                })
        return response

class BistaWebsiteSale(BistaWebsiteSale):
    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        res = super(BistaWebsiteSale, self).products_autocomplete(term, options, **kwargs)
        if request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep') and res.get('products'):
            for index, res_product in enumerate(res['products'], 0):
                app_website_url = res_product['website_url'].replace('/shop/','/sales-rep/sale/')
                res['products'][index].update({
                    'website_url': app_website_url,
                })
        return res
    
    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ """
        if request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            partner_id = request.session.get('selected_partner_id')
            if partner_id:
                selected_user = request.env['res.users'].search([('partner_id', '=', partner_id)], limit=1)
            else:
                return werkzeug.utils.redirect('/sales-rep/home')

            if sale_order_id is None:
                order = request.website.sale_get_order()
            else:
                order = request.env['sale.order'].sudo().browse(sale_order_id)
                assert order.id == request.session.get('sale_last_order_id')

            user_obj=request.env['res.users']

            b2bid = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
            group_list = [b2bid.id]

            user_data=user_obj.search([('id','=',selected_user.id),('groups_id','in',group_list)])
            if user_data:
                order.write({
                    'note': post.get('note', ''),
                    'purchase_order': post.get('purchase_order', ''),
                    'b2b_confirmed': True,
                })

                # order.onchange_partner_shipping_id()
                # order.order_line._compute_tax_id()
                request.session['sale_last_order_id'] = order.id
                # request.website.sale_get_order(update_pricelist=True)
                order.action_quotation_sent()
                mail_template = request.env.ref('superasiab2b_b2c.mail_template_b2b_sale_confirmation')
                if not mail_template:
                    mail_template = request.env.ref('sale.mail_template_sale_confirmation')
                mail_template.send_mail(order.id, force_send=True)
                request.website.sale_reset()
                return request.redirect('/shop/confirmation')
        
        res = super(BistaWebsiteSale, self).payment_validate(transaction_id, sale_order_id, **post)
        return res


    
