from odoo import fields, models, api


class PricelistExtension(models.Model):
    _inherit = 'product.pricelist'

    customer_type = fields.Selection([
        ('individual', 'Individual'),
        ('company', 'Company')
    ], string="Customer Type")
