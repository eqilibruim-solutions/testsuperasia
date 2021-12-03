from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            res_partner = self.env['res.partner'].browse(int(vals.get('partner_id')))
            vals['source_id'] = res_partner.user_ids.source_id.id

        result = super(SaleOrder, self).create(vals)
        return result

    @api.onchange('partner_id')
    def onchange_partner_id_source_id(self):
        if not self.partner_id:
            return
        self.source_id = self.partner_id.user_ids.source_id.id

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