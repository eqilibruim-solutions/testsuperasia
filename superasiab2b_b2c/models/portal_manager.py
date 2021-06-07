from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

from werkzeug.urls import url_encode



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_meta_ingredients = fields.Text("Website meta ingredients", translate=True)

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id
    b2buom_id = fields.Many2one(
    'uom.uom', 'B2C Unit of Measure',
    default=_get_default_uom_id, required=True,
    help="Default unit of measure used for all stock operations.")

    is_featured_product = fields.Boolean(string="Feature Product?",
                                         help="Check true if you want this product to be in Featured Products on E-commerce homepage.")

    is_hide_b2b = fields.Boolean(string="Hide from B2B Users?",
                                         help="Check true if you want this product to be hidden from B2B users in E-commerce.")

    is_hide_b2c = fields.Boolean(string="Hide from B2C Users?",
                                 help="Check true if you want this product to be hidden from B2C users in E-commerce.")


    def featured_products(self):
        main_list = []
        temp_list=[]

        domain = [('is_featured_product', '=', True)]

        if request.env.user.user_has_groups('base.group_public') or request.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            domain.append(('is_hide_b2c', '=', False))
        elif request.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
            domain.append(('is_hide_b2b', '=', False))

        prodids = self.env['product.template'].sudo().search(domain)
        _logger.info('========prodids========= %s' % prodids)

        for prod in prodids:
            if len(temp_list) < 6:
                temp_list.append(prod)
            else:
                main_list.append(temp_list)
                temp_list=[]
                temp_list.append(prod)

        if temp_list:
            main_list.append(temp_list)
        _logger.info('========main_list========= %s' % main_list)
        return main_list

    # def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
    #     combination_info = super(ProductTemplate, self)._get_combination_info(
    #         combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
    #         parent_combination=parent_combination, only_template=only_template)
    #
    #     if not self.env.context.get('website_sale_stock_get_quantity'):
    #         return combination_info
    #
    #     if combination_info['product_id']:
    #         product = self.env['product.product'].sudo().browse(combination_info['product_id'])
    #         print (":::::::::::::::::::::::::::::::if product:::::::::::::::",int(product.cart_qty))
    #         website = self.env['website'].get_current_website()
    #         virtual_available = product.with_context(warehouse=website.warehouse_id.id).virtual_available
    #
    #
    #         # Custom Code Start
    #         avail_qty = product.qty_available
    #         onhandqty = product.qty_available
    #         _logger.info('========avail_qty::::::::::::::::::::::::::::::::::=========== %s' % avail_qty)
    #         _logger.info('========onhandqty=========== %s' % onhandqty)
    #
    #         b2buser = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
    #         b2c = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')
    #         userobj = self.env['res.users']
    #         b2busergroup = userobj.search([('id','=',self.env.user.id),('groups_id','in',b2buser.id)])
    #         b2cusers = userobj.search([('id','=',self.env.user.id),('groups_id','in',b2c.id)])
    #
    #         product_uom = product.uom_id
    #         factor_inv = product_uom.factor_inv
    #
    #         if b2cusers:
    #             product_uom = product.b2buom_id
    #             print('===========product_uom================',product_uom)
    #             if factor_inv > 0:
    #                 onhandqty = onhandqty/factor_inv
    #         print('========onhandqty===calc======== %s' % onhandqty)
    #         # Custom code End
    #
    #
    #
    #         combination_info.update({
    #             'virtual_available': int(virtual_available),
    #             'virtual_available_formatted': self.env['ir.qweb.field.float'].value_to_html(virtual_available, {'decimal_precision': 'Product Unit of Measure'}),
    #             'product_type': product.type,
    #             'inventory_availability': product.inventory_availability,
    #             'available_threshold': product.available_threshold,
    #             'custom_message': product.custom_message,
    #             'product_template': product.product_tmpl_id.id,
    #             'cart_qty': int(product.cart_qty),
    #             'uom_name': product.uom_id.name,
    #             'onhand_qty': int(onhandqty),
    #             'avail_qty':int(avail_qty),
    #         })
    #     else:
    #         product_template = self.sudo()
    #
    #         print (":::::::::::::::::::::::::::::::product_template:::::::::::::::",product_template)
    #         combination_info.update({
    #             'virtual_available': 0,
    #             'product_type': product_template.type,
    #             'inventory_availability': product_template.inventory_availability,
    #             'available_threshold': product_template.available_threshold,
    #             'custom_message': product_template.custom_message,
    #             'product_template': product_template.id,
    #             'cart_qty': 0
    #         })
    #
    #     return combination_info




    # Inherited _get_combination_info for set condition if the recent product view has 0 qty then cart button should be
    # invisible (Added onhand_qty)
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        self.ensure_one()
        # get the name before the change of context to benefit from prefetch
        display_name = self.display_name

        display_image = True
        quantity = self.env.context.get('quantity', add_qty)
        context = dict(self.env.context, quantity=quantity, pricelist=pricelist.id if pricelist else False)
        product_template = self.with_context(context)

        combination = combination or product_template.env['product.template.attribute.value']

        if not product_id and not combination and not only_template:
            combination = product_template._get_first_possible_combination(parent_combination)

        if only_template:
            product = product_template.env['product.product']
        elif product_id and not combination:
            product = product_template.env['product.product'].browse(product_id)
        else:
            product = product_template._get_variant_for_combination(combination)
        if product:
            # We need to add the price_extra for the attributes that are not
            # in the variant, typically those of type no_variant, but it is
            # possible that a no_variant attribute is still in a variant if
            # the type of the attribute has been changed after creation.
            print ("::::::::::::::::::::::::::::product.cart_qty::::::::::::::::::",product.cart_qty)
            no_variant_attributes_price_extra = [
                ptav.price_extra for ptav in combination.filtered(
                    lambda ptav:
                    ptav.price_extra and
                    ptav not in product.product_template_attribute_value_ids
                )
            ]
            if no_variant_attributes_price_extra:
                product = product.with_context(
                    no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
                )
            list_price = product.price_compute('list_price')[product.id]
            price = product.price if pricelist else list_price
            display_image = bool(product.image_1920)
            display_name = product.display_name
        else:
            product_template = product_template.with_context(current_attributes_price_extra=[v.price_extra or 0.0 for v in combination])
            list_price = product_template.price_compute('list_price')[product_template.id]
            price = product_template.price if pricelist else list_price
            display_image = bool(product_template.image_1920)

            combination_name = combination._get_combination_name()
            if combination_name:
                display_name = "%s (%s)" % (display_name, combination_name)

        if pricelist and pricelist.currency_id != product_template.currency_id:
            list_price = product_template.currency_id._convert(
                list_price, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
                fields.Date.today()
            )

        price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
        has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount, price) == 1

        avail_qty = product.qty_available
        onhandqty = product.qty_available
        _logger.info('========avail_qty::::::::::::::::::::::::::::::::::=========== %s' % avail_qty)
        _logger.info('========onhandqty=========== %s' % onhandqty)

        b2buser = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
        b2c = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')
        userobj = self.env['res.users']
        b2busergroup = userobj.search([('id','=',self.env.user.id),('groups_id','in',b2buser.id)])
        b2cusers = userobj.search([('id','=',self.env.user.id),('groups_id','in',b2c.id)])
        
        public = self.env.user
        publicuser = False
        if public.partner_id.name == 'Public user':
            publicuser = True
        print('===========publicuser================',publicuser)

        product_uom = product.uom_id
        factor_inv = product_uom.factor_inv

<<<<<<< HEAD
        if b2cusers or publicuser:
            
            product_uom = product.b2buom_id
            print('===========product_uom================',product_uom)
            if factor_inv > 0:
                onhandqty = onhandqty*factor_inv

            pricelist_id = b2cusers.partner_id.property_product_pricelist
            _logger.info('========pricelist_id========= %s' % pricelist_id)
            _logger.info('========product========= %s' % product)
            pricelist_id = pricelist_id.id
            priceitemid = self.env['product.pricelist.item'].search([('pricelist_id','=',pricelist_id),('product_id','=',product.id)])
            _logger.info('========priceitemid========= %s' % priceitemid)
            if priceitemid:
                price = priceitemid[0].fixed_price

        if b2busergroup:
                price = product.list_price

        _logger.info('========onhandqty===calc======== %s' % onhandqty)   
        print('===========price================',price)
=======
        if b2cusers:

            product_uom = product.b2buom_id
            print('===========product_uom================',product_uom)
            if factor_inv > 0:
                onhandqty = onhandqty/factor_inv
        _logger.info('========onhandqty===calc======== %s' % onhandqty)
>>>>>>> 22aa8b717520d8ee1626969ec9369edcc97fec00

        return {
            'product_id': product.id,
            'product_template_id': product_template.id,
            'display_name': display_name,
            'display_image': display_image,
            'price': price,
            'list_price': list_price,
            'has_discounted_price': has_discounted_price,
            'onhand_qty': int(onhandqty),
            'avail_qty':int(avail_qty),
            'updated_cart_qty':int(product.cart_qty),
        }



class SaleOrdersuperaisa(models.Model):
    _inherit = 'sale.order'

    account_type = fields.Selection([('B2C', 'B2C'), ('B2B', 'B2B')],
                                    string='Account Type')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Account Type
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        userobj = self.env['res.users']
        b2buser = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
        b2c = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')

        partner_id = self.partner_id
        b2busergroup = userobj.search([('partner_id','=',partner_id.id),('groups_id','in',b2buser.id)])
        b2cusers = userobj.search([('partner_id','=',partner_id.id),('groups_id','in',b2c.id)])
        _logger.info('========b2busergroup========= %s' % b2busergroup)
        _logger.info('========b2cusers========= %s' % b2cusers)
        account_type = ''
        if b2busergroup:
            account_type = 'B2B'
        if b2cusers:
            account_type = 'B2C'
        _logger.info('========account_type========= %s' % account_type)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'account_type': account_type,
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.user.id
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team']._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)],user_id=user_id)
        self.update(values)




    def _website_product_id_change(self, order_id, product_id, qty=0):

        userobj = self.env['res.users']
        superasiaid = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
        _logger.info('========superasiaid========= %s' % superasiaid)
        _logger.info('========uid========= %s' % self.env.user.id)
        _logger.info('========usersssss========= %s' % self.env.user.id)

        b2buser = userobj.search([('id','=',self.env.user.id),('groups_id','in',superasiaid.id)])

        _logger.info('========b2buser========= %s' % b2buser)

        order = self.sudo().browse(order_id)
        product_context = dict(self.env.context)
        product_context.setdefault('lang', order.partner_id.lang)
        product_context.update({
            'partner': order.partner_id,
            'quantity': qty,
            'date': order.date_order,
            'pricelist': order.pricelist_id.id,
            'force_company': order.company_id.id,
        })
        product = self.env['product.product'].with_context(product_context).browse(product_id)


        if b2buser:
            product_uom = product.uom_id
        else:
            product_uom = product.b2buom_id

        _logger.info('========product_uom==111======= %s' % product_uom)



        discount = 0

        if order.pricelist_id.discount_policy == 'without_discount':
            # This part is pretty much a copy-paste of the method '_onchange_discount' of
            # 'sale.order.line'.
            price, rule_id = order.pricelist_id.with_context(product_context).get_product_price_rule(product, qty or 1.0, order.partner_id)
            pu, currency = request.env['sale.order.line'].with_context(product_context)._get_real_price_currency(product, rule_id, qty, product_uom, order.pricelist_id.id)
            if pu != 0:
                if order.pricelist_id.currency_id != currency:
                    # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                    date = order.date_order or fields.Date.today()
                    pu = currency._convert(pu, order.pricelist_id.currency_id, order.company_id, date)
                discount = (pu - price) / pu * 100
                if discount < 0:
                    # In case the discount is negative, we don't want to show it to the customer,
                    # but we still want to use the price defined on the pricelist
                    discount = 0
                    pu = price
        else:
            pu = product.price
            if order.pricelist_id and order.partner_id:
                order_line = order._cart_find_product_line(product.id)
                if order_line:
                    pu = self.env['account.tax']._fix_tax_included_price_company(pu, product.taxes_id, order_line[0].tax_id, self.company_id)

        return {
            'product_id': product_id,
            'product_uom_qty': qty,
            'order_id': order_id,
            'product_uom': product_uom.id,
            'price_unit': pu,
            'discount': discount,
        }

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):

        userobj = self.env['res.users']
        superasiaid = self.env['ir.model.data'].get_object('superasiab2b_b2c', 'group_b2baccount')
        _logger.info('========superasiaid=11======== %s' % superasiaid)
        _logger.info('========uid=11======== %s' % self.website_id.user_id)

        b2buser = userobj.search([('id', '=', self.env.user.id), ('groups_id', 'in', superasiaid.id)])

        b2c = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')
        b2cusers = userobj.search([('id','=',self.env.user.id),('groups_id','in',b2c.id)])
        _logger.info('========b2buser=11======== %s' % b2buser)
        _logger.info('========b2cusers=11======== %s' % b2buser)

        partner_id = self.partner_id

        account_type = ''
        if b2buser:
            account_type = 'B2B'
        if b2cusers:
            account_type = 'B2C'

        self.account_type = account_type



        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
        # change lang to get correct name of attributes/values
        product_with_context = self.env['product.product'].with_context(product_context)
        product = product_with_context.browse(int(product_id))


        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]

        # Create line if no line with product_id can be located
        if not order_line:
            if not product:
                raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

            no_variant_attribute_values = kwargs.get('no_variant_attribute_values') or []
            received_no_variant_values = product.env['product.template.attribute.value'].browse([int(ptav['value']) for ptav in no_variant_attribute_values])
            received_combination = product.product_template_attribute_value_ids | received_no_variant_values
            product_template = product.product_tmpl_id

            # handle all cases where incorrect or incomplete data are received
            combination = product_template._get_closest_possible_combination(received_combination)

            # get or create (if dynamic) the correct variant
            product = product_template._create_product_variant(combination)

            if not product:
                raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

            product_id = product.id

            values = self._website_product_id_change(self.id, product_id, qty=1)

            # add no_variant attributes that were not received
            for ptav in combination.filtered(lambda ptav: ptav.attribute_id.create_variant == 'no_variant' and ptav not in received_no_variant_values):
                no_variant_attribute_values.append({
                    'value': ptav.id,
                })

            # save no_variant attributes values
            if no_variant_attribute_values:
                values['product_no_variant_attribute_value_ids'] = [
                    (6, 0, [int(attribute['value']) for attribute in no_variant_attribute_values])
                ]

            # add is_custom attribute values that were not received
            custom_values = kwargs.get('product_custom_attribute_values') or []
            received_custom_values = product.env['product.template.attribute.value'].browse([int(ptav['custom_product_template_attribute_value_id']) for ptav in custom_values])

            for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
                custom_values.append({
                    'custom_product_template_attribute_value_id': ptav.id,
                    'custom_value': '',
                })

            # save is_custom attributes values
            if custom_values:
                values['product_custom_attribute_value_ids'] = [(0, 0, {
                    'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value']
                }) for custom_value in custom_values]

            # create the line
            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud) but should fail silently in frontend
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1

        # compute new quantity
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)

        # Remove zero of negative lines
        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                # update description of the parent
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
        else:
            # update line
            no_variant_attributes_price_extra = [ptav.price_extra for ptav in order_line.product_no_variant_attribute_value_ids]
            values = self.with_context(no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra))._website_product_id_change(self.id, product_id, qty=quantity)
            if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
                order = self.sudo().browse(self.id)
                product_context.update({
                    'partner': order.partner_id,
                    'quantity': quantity,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                    'force_company': order.company_id.id,
                })
                product_with_context = self.env['product.product'].with_context(product_context)
                product = product_with_context.browse(product_id)
                display_price = 0.0
                if b2buser:
                    product_uom = product.uom_id
                    display_price = order_line._get_display_price(product)
                else:
                    product_uom = product.b2buom_id
                    display_price = values['price_unit']
                values['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                    display_price,
                    order_line.product_id.taxes_id,
                    order_line.tax_id,
                    self.company_id
                )
                values['product_uom'] = product_uom.id
                _logger.info('========values["product_uom"]========= %s' % values['product_uom'])

                _logger.info('========values["price_unit"]========= %s' % values['price_unit'])

            order_line.write(values)

            # link a product to the sales order
            if kwargs.get('linked_line_id'):
                linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
                order_line.write({
                    'linked_line_id': linked_line.id,
                })
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
            # Generate the description with everything. This is done after
            # creating because the following related fields have to be set:
            # - product_no_variant_attribute_value_ids
            # - product_custom_attribute_value_ids
            # - linked_line_id
            order_line.name = order_line.get_sale_order_line_multiline_description_sale(product)

        option_lines = self.order_line.filtered(lambda l: l.linked_line_id.id == order_line.id)

        return {'line_id': order_line.id, 'quantity': quantity, 'option_ids': list(set(option_lines.ids))}


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @api.model
    def get_frontend_session_info(self):
        return {
            'is_admin': request.session.uid and self.env.user._is_admin() or False,
            'is_system': request.session.uid and self.env.user._is_system() or False,
            'is_website_user': request.session.uid and self.env.user._is_public() or False,
            'user_id': request.session.uid and self.env.user.id or False,
            'is_frontend': True,
            'share': self.env.user.share or False,
        }


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        # if self.order_id.pricelist_id and self.order_id.partner_id:
        #     product = self.product_id.with_context(
        #         lang=self.order_id.partner_id.lang,
        #         partner=self.order_id.partner_id,
        #         quantity=self.product_uom_qty,
        #         date=self.order_id.date_order,
        #         pricelist=self.order_id.pricelist_id.id,
        #         uom=self.product_uom.id,
        #         fiscal_position=self.env.context.get('fiscal_position')
        #     )
        #     self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        userobj = self.env['res.users']
        superasiaid = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
        b2c = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')

        partner_id = self.order_id.partner_id


        user_id = userobj.search([('partner_id','=',partner_id.id)])
        if user_id:
            b2buser = userobj.search([('partner_id','=',partner_id.id),('groups_id','in',superasiaid.id)])
            b2cusers = userobj.search([('partner_id','=',partner_id.id),('groups_id','in',b2c.id)])

            if b2buser:
                product_uom = self.product_id.uom_id
                # vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

            if b2cusers:
                product_uom = self.product_id.b2buom_id

            if not b2buser and not b2cusers:
                product_uom = self.product_id.uom_id

        else:
            product_uom = self.product_id.uom_id

        _logger.info('========product_uom========= %s' % product_uom)


        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        # if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
        if not self.product_uom or (product_uom.id != self.product_uom.id):
            # vals['product_uom'] = self.product_id.uom_id
            vals['product_uom'] = product_uom
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

        self._compute_tax_id()

        # if self.order_id.pricelist_id and self.order_id.partner_id:
        #     vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

        pricelist_id = self.order_id.partner_id.property_product_pricelist
        _logger.info('========pricelist_id========= %s' % pricelist_id)
        _logger.info('========product_id========= %s' % self.product_id)
        pricelist_id = pricelist_id.id
        priceitemid = self.env['product.pricelist.item'].search([('pricelist_id','=',pricelist_id),('product_id','=',self.product_id.id)])
        _logger.info('========priceitemid========= %s' % priceitemid)
        if priceitemid:
            vals['price_unit'] = priceitemid[0].fixed_price
        else:
            if self.order_id.pricelist_id and self.order_id.partner_id:
                pricee= self._get_display_price(product)
                _logger.info('========pricee========= %s' % pricee)
                vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

        _logger.info('========price_unit========= %s' % vals['price_unit'])




        self.update(vals)

        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        _logger.info('========valss22 %s' % vals)
        _logger.info('========result========= %s' % result)
        return result

class ir_mail_server(models.Model):
    _inherit = "ir.mail_server"


    smtp_user = fields.Char(string='Username', help="Optional username for SMTP authentication")
    smtp_pass = fields.Char(string='Password', help="Optional password for SMTP authentication")


class res_partner(models.Model):
    _inherit = 'res.partner'

    signup_token = fields.Char(copy=False)
    signup_type = fields.Char(string='Signup Token Type', copy=False)
    signup_expiration = fields.Datetime(copy=False)

class res_users(models.Model):
    _inherit = 'res.users'

    def approveuser(self):
        self.active = True

        template = False

        try:
            template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
        except ValueError:
                pass


        assert template._name == 'mail.template'

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.with_context(lang=user.lang).send_mail(user.id, force_send=force_send, raise_exception=True)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)
