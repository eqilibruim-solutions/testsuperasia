from odoo import fields, models, api


class PricelistExtension(models.Model):
    _inherit = 'product.pricelist'

    customer_type = fields.Selection([
        ('person', 'Individual'),
        ('company', 'Company')
    ], string="Customer Type")
