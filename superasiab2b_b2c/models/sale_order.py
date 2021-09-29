from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _latest_quotation_sent_order(self, partner, **kwargs):
        self.ensure_one()
        quotations = self.env['sale.order']
        if partner:
            domain = [
                ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
                ('state', 'in',['sent'])
            ]
            quotations = self.search(domain, order='date_order desc', limit=1)
        return quotations