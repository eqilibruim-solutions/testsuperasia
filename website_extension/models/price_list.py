from odoo import fields, models, api


class res_groups(models.Model):
    _inherit = 'res.groups'

    e_commerce = fields.Boolean(string="E-commerce")


class PricelistExtension(models.Model):
    _inherit = 'product.pricelist'

    customer_type = fields.Selection([
        ('person', 'Individual'),
        ('company', 'Company')
    ], string="Customer Type")
    group_id = fields.Many2one('res.groups', string="User Type", domain="[('e_commerce', '=', True)]") # ToDo: domain set 'e_commerce' as true
