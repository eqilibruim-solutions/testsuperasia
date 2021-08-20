# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_margin = fields.Float(string='Margin', digits='Account',
                              store=True, readonly=True, compute='_calc_margin')
    # line_margin = fields.Float(string='Margin', digits='Account', readonly=True)
    line_margin_computed  = fields.Boolean(string='')


    @api.depends('price_unit', 'product_uom_qty', 'tax_id', 'product_id', 'order_id.partner_id', 'order_id.currency_id')
    def _calc_margin(self):
        for res in self:
            line_mrg_tot = 0
            cmp = 0.0
            cmp = ((res.purchase_price or res.product_id.standard_price) * res.product_uom_qty)
            margin = res.price_subtotal - cmp
            res.line_margin = margin
            res.line_margin_computed = True


    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res.update({'purchase_price':self.purchase_price})
        return res

    
class sale_order(models.Model):
    _inherit = "sale.order"

    def _calc_margin(self):
        for order in self:
            margin_per = 0.0
            margin = 0.0
            cmp = 0.0
            for line in order.order_line:
                if line.product_id:
                    cmp += (line.purchase_price * line.product_uom_qty)
                    margin =  order.amount_total - ((line.purchase_price or line.product_id.standard_price) * line.product_uom_qty)
                    # margin_per = (line.price_unit -line.purchase_price )/line.price_unit * 100
            if order.amount_total != 0:
                margin = order.amount_untaxed - cmp
                order.update({
                    'margin_cust' : (margin * 100) / order.amount_untaxed,
                    'margin_calc' : order.amount_untaxed - cmp
                })
            else:
                order.update({
                    'margin_cust' : 0.0,
                    'margin_calc' : 0.0
                })

    
    margin_cust = fields.Float('Margin %', compute='_calc_margin' , readonly=True)
    margin_calc = fields.Float('Margin', compute='_calc_margin' , readonly=True)
    
