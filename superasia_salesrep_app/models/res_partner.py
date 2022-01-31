# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.website.models import ir_http

class ResPartner(models.Model):
    _inherit = 'res.partner'
    # FIXME: When we install this module first time
    # "External ID not find" error show because of domain
    # Initial solution, remove domain from field before installing app then add domain after installed
    # assigned_sale_rep = fields.Many2one(
    #     'res.users', string='Assigned Sales Rep',
    #     domain=lambda self: [('groups_id', 'in', self.env.ref('superasia_salesrep_app.group_sales_rep').id)])
    
    assigned_sale_rep = fields.Many2one(
        'res.users', string='Assigned Sales Rep')
        # domain=lambda self: [('groups_id', 'in', self.env.ref('superasia_salesrep_app.group_sales_rep').id)])
 
    sale_rep_create = fields.Boolean(string='', help="Create by Sales Rep or not")
    last_website_so_id = fields.Many2one('sale.order', compute='_compute_last_website_so_id', string='Last Online Sales Order')

    def _compute_last_website_so_id(self):
        """Override base code
        Return last_website_so_id which are created/assigned by sales rep person
        """
        SaleOrder = self.env['sale.order']
        for partner in self:
            is_public = any(u._is_public() for u in partner.with_context(active_test=False).user_ids)
            website = ir_http.get_request_website()
            if website and not is_public:
                if self.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
                    partner.last_website_so_id = SaleOrder.search([
                        ('partner_id', '=', partner.id),
                        ('website_id', '=', website.id),
                        ('state', '=', 'draft'),
                        ('sales_rep_id', '=', self.env.user.id)
                    ], order='write_date desc', limit=1)
                else:
                    partner.last_website_so_id = SaleOrder.search([
                        ('partner_id', '=', partner.id),
                        ('website_id', '=', website.id),
                        ('state', '=', 'draft'),
                        ('sales_rep_id', '=', False)
                    ], order='write_date desc', limit=1)
            else:
                partner.last_website_so_id = SaleOrder  # Not in a website context or public User

    @api.model
    def create(self, vals):
        if self.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            vals.update({
                'assigned_sale_rep': self.env.user.id,
                'sale_rep_create': True
            })
        partner = super(ResPartner, self).create(vals)
        return partner

