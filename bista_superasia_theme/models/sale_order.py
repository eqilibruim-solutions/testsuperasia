from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    b2b_confirmed = fields.Boolean(string='', readonly=True)

    def dummy_action_btn(self):
        return True
