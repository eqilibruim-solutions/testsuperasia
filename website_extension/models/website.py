from odoo import models, api, _
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def get_pricelist_available(self, show_visible=False):
        print("get_pricelist")
        dep = super(Website, self).get_pricelist_available(show_visible)

        req = request
        # print(request)

        # print(type(dep))
        # sel_groups_1_8_9
        # for pl in dep.read(['group_id']):
        #     print(pl)
        # if self.env.user.customer_type is not False:
        #     if self.env.user.customer_type == 'person':
        #         print('B2C Customer')
        #     elif self.env.user.customer_type == 'company':
        #         print('B2B Customer')
        # else:
        #     print(self.env.user.customer_type)

        # if self.env.user.user_has_groups('base.group_portal'):
        #     group_id = request.env['ir.model.data'].get_object('base', 'group_portal')
        # else:
        #     group_id = request.env['ir.model.data'].get_object('base', 'group_public')
        if self.env.user.user_has_groups('superasiab2b_b2c.group_b2baccount'):
            group_id = request.env['ir.model.data'].get_object('superasiab2b_b2c', 'group_b2baccount')
        else:
            group_id = request.env['ir.model.data'].get_object('superasiab2b_b2c', 'group_b2c')

        group_list = [group_id.id]
        print(group_list)

        print(dep.search([('group_id', 'in', group_list)]))

        return dep.search([('group_id', 'in', group_list)])
