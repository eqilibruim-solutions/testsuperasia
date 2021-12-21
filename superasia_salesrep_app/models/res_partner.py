# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_rep_user = fields.Many2one('res.users', string='Responsible Sales Rep')
    sale_rep_create = fields.Boolean(string='', help="Create by Sales Rep or not")

    @api.model
    def create(self, vals):
        if self.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            vals.update({
                'sale_rep_user': self.env.user.id,
                'sale_rep_create': True
            })
        partner = super(ResPartner, self).create(vals)
        return partner

