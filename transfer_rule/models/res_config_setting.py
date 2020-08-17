# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_location_id = fields.Many2one("stock.location", related="company_id.internal_location_id",
                                           string="Internal Source Location", readonly=False)
