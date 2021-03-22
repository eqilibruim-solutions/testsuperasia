from odoo import fields, models, api


class res_groups(models.Model):
    _inherit = 'res.groups'

    e_commerce = fields.Boolean(string="E-commerce")


class PricelistExtension(models.Model):
    _inherit = 'product.pricelist'

    group_id = fields.Many2many('res.groups', string="Account Type", domain="[('e_commerce', '=', True)]")
