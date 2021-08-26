# -*- coding: utf-8 -*-

from odoo import api, fields, models, registry, SUPERUSER_ID, _

class BistaDeliveryCarrier(models.Model):
    
    _inherit = 'delivery.carrier'
    is_gta_code = fields.Boolean("Gta Code Enabled", help="Is this shipping method used for shipping gta code based")