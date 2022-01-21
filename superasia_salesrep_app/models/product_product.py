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
