from odoo import models, fields

class RealizedProductTemplate(models.Model):
    _inherit = 'product.template'

    location_bin = fields.Char('Bin Location', help='use this to identify bin location')
    # product_id = fields.Many2one('product.product')

class RealizedProductProduct(models.Model):
    _inherit = 'product.product'

    location_bin = fields.Char(related="product_tmpl_id.location_bin", string='Bin Location', help='use this to identify bin location')

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    location_bin = fields.Char(related="product_id.location_bin", string='Bin Location', help='use this to identify bin location')

