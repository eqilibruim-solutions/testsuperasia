from datetime import timedelta
from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def lot_close_to_removal(self, duration_day=30):
        """Find the lot obj which are close to removal_date
        based on duration_day of product

        Args:
            duration_day (int, optional): Defaults to 30.

        Returns:
            [obj]: return stock.production.lot object
        """
        current_date = fields.Datetime.now()
        date_with_duration = current_date + timedelta(days=duration_day)
        closest_lot_obj = self.env['stock.production.lot'].search([
            ('product_id', '=', self.id),
            ('removal_date', '>=', current_date),
            ('removal_date', '<=', date_with_duration)
            ], order='removal_date', limit=1)
        
        return closest_lot_obj


class ProductTemplate(models.Model):
    _inherit = "product.template"
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)
        product = self.env['product.product'].browse(combination_info['product_id']) or self
        factor_inv = 0
        if product.uom_id.factor_inv:
            factor_inv = product.uom_id.factor_inv
        if factor_inv > 0:
            combination_info.update({
                'unit_price': round(float(combination_info['price'])/factor_inv)
            })
        return combination_info