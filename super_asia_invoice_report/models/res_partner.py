from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ethnicity = fields.Char(string="Ethnicity", help="Ethnicity of the Customer.")
