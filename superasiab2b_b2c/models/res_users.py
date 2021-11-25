from odoo import fields, models


class User(models.Model):
    _inherit = "res.users"

    source_id = fields.Many2one('utm.source', 'Source',
                                help="This is the source of the link, e.g. Search Engine, another domain, or name of email list")