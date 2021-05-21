from odoo import models, api, _
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def get_pricelist_available(self, show_visible=False):
        dep = super(Website, self).get_pricelist_available(show_visible)

        req = request
        group_list = []
        grouppub_id = request.env['ir.model.data'].get_object('base', 'group_public')
        # groupport_id = request.env['ir.model.data'].get_object('base', 'group_portal')
        b2c = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')
        group_list = [grouppub_id.id,b2c.id]

        if self.env.user.user_has_groups('base.group_public') or self.env.user.user_has_groups('superasiab2b_b2c.group_b2cuser'):
            print(dep.search([('group_id', 'in', group_list)]))
            return dep.search([('group_id', 'in', group_list)])
        else:
            print('fafs', dep.search(['&', ('group_id', 'not in', group_list), ('selectable', '=', True)]))
            return dep.search(['&', ('group_id', 'not in', group_list), ('selectable', '=', True)])


