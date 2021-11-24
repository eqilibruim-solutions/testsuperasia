from werkzeug import Response
import werkzeug.utils
import logging
_logger = logging.getLogger(__name__)

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.bista_superasia_theme.controllers.main import TableCompute
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
            return request.not_found()
        b2b_user_group = request.env['ir.model.data'].sudo().get_object(
                                'superasiab2b_b2c','group_b2baccount')
        userobj = request.env['res.users'].sudo()
        b2b_users = userobj.search([('groups_id','in',b2b_user_group.id)])
        b2b_partner_ids = []
        if b2b_users:
            b2b_partner_ids = b2b_users.mapped('partner_id')
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
            return request.not_found()
        b2b_user_group = request.env['ir.model.data'].sudo().get_object(
                                'superasiab2b_b2c','group_b2baccount')
        # if b2b_user_group:
        #     b2b_partner_ids = b2b_user_group.users.mapped('partner_id')
        userobj = request.env['res.users'].sudo()
        b2b_users = userobj.search([('groups_id','in',b2b_user_group.id)])
        b2b_partner_ids = []
        if b2b_users:
            b2b_partner_ids = b2b_users.mapped('partner_id')
        # Filter
        if post.get('city'):
            filter_city_list = request.httprequest.args.getlist('city')
            b2b_partner_ids = b2b_partner_ids.filtered(lambda x: x.city in filter_city_list)
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
            return request.not_found()
        
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        values, errors = {}, {}
        partner_id = int(post.get('partner_id', -1))
        mode = 'edit' if partner_id > 0 else 'new'

        if mode == 'edit':
            values = Partner.browse(partner_id)

        # IF POSTED
        if 'submitted' in post:
            pre_values = self.account_form_values_preprocess(post)
            errors, error_msg = self.add_account_form_validate(pre_values)
            post, errors, error_msg = self.account_form_values_postprocess(mode, pre_values, errors, error_msg)
            if errors:
                errors['error_message'] = error_msg
                values = post
            else:
                if mode == 'edit' and partner_id:
                    Partner.browse(partner_id).sudo().write(post)
                else:
                    user_obj = request.env['res.users'].sudo()
                    exists_user = user_obj.search([('login','=',post.get('email'))])
                    if exists_user:
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

                    profile_obj = request.env['res.partner']
                    # profile_ids=profile_obj.search([('user_id','=',user_data.id)])
                    # if profile_ids:
                    #     return request.redirect('/accountexist')


                    partner_id = user_data.partner_id
                    login = user_data.login

                    # b2b_customer_type_key = post.get('b2b_customer_type')
                    # # Get b2b_customer_type selection field's label in res.partner model
                    # b2b_customer_type = dict(request.env['res.partner'].fields_get(
                    #     allfields=['b2b_customer_type'])['b2b_customer_type']['selection'])[b2b_customer_type_key]
                    post['company_type'] = 'company'
                    profile_vals = post
                    partner_id.write(profile_vals)

                
                    if partner_id:
                        ir_mail_server = request.env['ir.mail_server']
                        mail_server_id = ir_mail_server.search([('name','=','Superasia')])
                        smtp_user = str(mail_server_id.smtp_user)
                        temp_obj = request.env['mail.template']
                        template_data = temp_obj.search([('name','=','Account Activation')])
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

                if not errors:
                    return request.redirect(post.get('callback') or '/sales-rep/all-accounts')
        country = None
        if mode == 'edit' and not errors:
            country = values.country_id

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

    @http.route(['/sales-rep/account/<int:partner_id>/details'], type='http', methods=['GET'], auth="user", website=True, csrf=False)
    def sales_agent_b2b_details(self, partner_id, **kw):
        partner_obj = request.env['res.partner'].browse(partner_id)
        if not partner_obj or not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            return request.not_found()
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
            'partner_id': partner_id,
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
    
    @http.route([
        '''/sales-rep/sale''',
        '''/sales-rep/sale/page/<int:page>''',
        '''/sales-rep/sale/category/<model("product.public.category"):category>''',
        '''/sales-rep/sale/category/<model("product.public.category"):category>/page/<int:page>'''
        ], type='http', auth="user", website=True)
    def sales_rep_sale_shop(self, page=0, category=None, search='', ppg=False, **post):
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
            ppg = 90
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
        print(":::::::::::self._get_search_order(post):::::::::::::::",self._get_search_order(post))
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
            'variant_counts': variant_counts,
            'selected_partner': selected_partner,

            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
        }
        if category:
            values['main_object'] = category

        return request.render('superasia_salesrep_app.sales_rep_product_listing', values)


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
