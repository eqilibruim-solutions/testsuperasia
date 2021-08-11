# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class User(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        if vals.get('company_id'):
            action = self.env.ref('aged_receivable_report.action_account_receivable_aging', False)
            action.sudo().context = {'search_default_company_id': vals['company_id']}
        return super(User, self).write(vals)
