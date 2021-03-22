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


class product_template(models.Model):
    _inherit = 'product.template'

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id
    b2buom_id = fields.Many2one(
    'uom.uom', 'B2C Unit of Measure',
    default=_get_default_uom_id, required=True,
    help="Default unit of measure used for all stock operations.")


class SaleOrdersuperaisa(models.Model):
    _inherit = 'sale.order'


    def _website_product_id_change(self, order_id, product_id, qty=0):

        userobj = self.env['res.users']
        superasiaid = self.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')

        b2buser = userobj.search([('id','=',self.env.uid),('groups_id','in',superasiaid.id)])

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

        _logger.info('========product_uom========= %s' % product_uom)



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


class res_users(models.Model):
	_inherit = 'res.users'

	def approveuser(self):
		self.active = True
		self.action_reset_password()


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

        partner_id = self.order_id.partner_id


        b2buser = userobj.search([('partner_id','=',partner_id.id),('groups_id','in',superasiaid.id)])

        if b2buser:
            product_uom = self.product_id.uom_id
            # vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        else:
            product_uom = self.product_id.b2buom_id
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


        priceitemid = self.env['product.pricelist.item'].search([('pricelist_id','=',self.order_id.pricelist_id.id),('product_id','=',self.product_id.id)])
        _logger.info('========priceitemid========= %s' % priceitemid)
        if priceitemid:
            vals['price_unit'] = priceitemid.fixed_price
        else:
            if self.order_id.pricelist_id and self.order_id.partner_id:
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

    # @api.onchange('product_uom', 'product_uom_qty')
    # def product_uom_change(self):
    #     if not self.product_uom or not self.product_id:
    #         self.price_unit = 0.0
    #         return
    #     if self.order_id.pricelist_id and self.order_id.partner_id:
    #         product = self.product_id.with_context(
    #             lang=self.order_id.partner_id.lang,
    #             partner=self.order_id.partner_id,
    #             quantity=self.product_uom_qty,
    #             date=self.order_id.date_order,
    #             pricelist=self.order_id.pricelist_id.id,
    #             uom=self.product_uom.id,
    #             fiscal_position=self.env.context.get('fiscal_position')
    #         )
    #         self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)


# class IrMailServer(models.Model):
#     _inherit = "ir.mail_server"


#     smtp_user = fields.Char(string='Username', help="Optional username for SMTP authentication")
#     smtp_pass = fields.Char(string='Password', help="Optional password for SMTP authentication")


# class ResPartner(models.Model):
#     _inherit = 'res.partner'

#     signup_token = fields.Char(copy=False)
#     signup_type = fields.Char(string='Signup Token Type', copy=False)
#     signup_expiration = fields.Datetime(copy=False)