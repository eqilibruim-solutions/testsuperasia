from odoo import models, fields


class SaleOrderSalesRep(models.Model):
    _inherit = 'sale.order'
    sales_rep_id = fields.Many2one(
        'res.users', string='Sales Representative', index=True, default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('superasia_salesrep_app.group_sales_rep').id)])
    
    def _website_product_id_change(self, order_id, product_id, qty=0):
        values = super(SaleOrderSalesRep, self)._website_product_id_change(order_id, product_id, qty=qty)
        if self.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            order = self.sudo().browse(order_id)
            order_line = order._cart_find_product_line(product_id)
            if order_line and order_line.discount_manual_update:
                values.update({
                    'discount': order_line.discount,
                })
        return values

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    discount_manual_update = fields.Boolean(default=False, readonly=True)