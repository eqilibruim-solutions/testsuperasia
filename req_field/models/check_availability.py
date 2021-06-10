# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CheckAvailability(models.Model):
    _inherit = 'stock.picking'

    def action_assign(self):
        # print(self.state)
        # print(self.user_id)
        # print(self.env.user.id)

        for rec in self:
            if rec.state == 'confirmed':
                print(rec.state)
                rec.user_id = self.env.user.id

        res = super(CheckAvailability, self).action_assign()
        return True
