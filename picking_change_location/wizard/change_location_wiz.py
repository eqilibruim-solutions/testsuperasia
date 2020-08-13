# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ChangeLocationWizard(models.TransientModel):
    _name = "change.location.wizard"
    _description = "Change Location"

    location_dest_id = fields.Many2one("stock.location", string='Destination Location')
    location_id = fields.Many2one("stock.location", string='Source Location')

    def change_location(self):
        """ Changes the Destination Location and reserve with updated location. """
        self.ensure_one()
        pick_obj = self.env[self._context['active_model']].browse(self._context['active_id'])
        pick_obj.do_unreserve()
        vals = {}
        if self.location_id:
            vals.update({'location_id': self.location_id.id})
        if self.location_dest_id:
            vals.update({'location_dest_id': self.location_dest_id.id})
        pick_obj.write(vals)
        pick_obj.action_assign()
        return {'type': 'ir.actions.act_window_close'}
