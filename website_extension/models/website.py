from odoo import models, api, _
# from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def _get_pricelist_available(self, req, show_visible=False):
        dep = super(Website, self)._get_pricelist_available(req, show_visible)

        print(dep)

        return dep
