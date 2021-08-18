# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class account_invoice_line(models.Model):

    _inherit = "account.move.line"

    line_margin = fields.Float(string='Margin', digits='Account',store=True, readonly=True,compute='_calc_margin')
    # line_margin = fields.Float(string='Margin', digits='Account', readonly=True)
    purchase_price =  fields.Float('Cost', compute='_get_product_cost' ,digits=dp.get_precision('Product Price'))
    margin_subtotal_signed = fields.Float(string='Margin Signed', currency_field='always_set_currency_id',
        readonly=True,store=True, compute='_calc_margin')
    # margin_subtotal_signed = fields.Float(string='Margin Signed', currency_field='always_set_currency_id',
    #     readonly=True)
    line_margin_computed = fields.Boolean(string='')
    margin_subtotal_signed_computed = fields.Boolean(string='')

    @api.depends('product_id')
    def _get_product_cost(self):
        for n in self:
            frm_cur = self.env.company.currency_id
            to_cur = n.move_id.currency_id
            purchase_price = n.product_id.standard_price
            if n.product_uom_id != n.product_id.uom_id:
                purchase_price = n.product_id.uom_id._compute_price(purchase_price, n.product_uom_id)            
            price = frm_cur._convert(
                                    purchase_price, to_cur,
                                    n.move_id.company_id or self.env.company,
                                    fields.Date.today(), round=False)
            n.purchase_price =  price

    @api.depends('price_unit', 'discount', 'tax_ids', 'quantity',
                 'product_id', 'move_id.partner_id', 'move_id.currency_id')
    def _calc_margin(self):
        for res in self:
            if not len(res.product_id or []) is 0 and res.display_type is False:
                line_mrg_tot = 0
                cmp = 0.0
                cmp = ((res.purchase_price or res.product_id.standard_price) * res.quantity)
                margin = res.price_subtotal - cmp
                res.line_margin = margin
                margin_subtotal_signed = margin
                sign = res.move_id.type in ['in_refund', 'out_refund'] and -1 or 1
                res.margin_subtotal_signed = margin_subtotal_signed * sign
            else:
                res.margin_subtotal_signed = 0.0
            res.line_margin_computed = True
            res.margin_subtotal_signed_computed = True



    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(account_invoice_line, self)._onchange_product_id()
        if self.product_id:
            frm_cur = self.env.company.currency_id
            to_cur = self.move_id.currency_id
            purchase_price = self.product_id.standard_price
            if self.product_uom_id != self.product_id.uom_id:
                purchase_price = self.product_id.uom_id._compute_price(purchase_price, self.product_uom_id)
            price = frm_cur._convert(
                                    purchase_price, to_cur,
                                    self.move_id.company_id or self.env.company,
                                    fields.Date.today(), round=False)   
            self.purchase_price = price
            
        return res

    
class account_invoice(models.Model):
    _inherit = "account.move"

    margin_cust = fields.Float('Margin %', compute='_calc_margin')
    margin_calc = fields.Float('Margin', compute='_calc_margin')
    
    @api.depends('invoice_line_ids')
    def _calc_margin(self): 
        for order in self:
            line_mrg_tot = 0
            margin = 0.0
            cmp = 0.0
            for line in order.invoice_line_ids:
                cmp += (line.purchase_price * line.quantity)
                margin = line.price_subtotal - ((line.purchase_price or line.product_id.standard_price) * line.quantity)
                line_mrg_tot += margin 
            if order.amount_total != 0 and order.amount_untaxed != 0:
                order.update({
                    'margin_cust' : (line_mrg_tot * 100) / order.amount_untaxed,
                    'margin_calc' : line_mrg_tot
                })
            else:
                order.update({
                    'margin_cust' : 0.0,
                    'margin_calc' : 0.0
                })


