# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class GtaCode(models.Model):
    _name = 'gta.code'
    _description = 'Free delivery postal code GTA'
    _rec_name = 'postal_code'

    postal_code = fields.Char()
    region = fields.Char()

    _sql_constraints = [
        ('postal_code_uniq', 'UNIQUE(postal_code)', 'You can not have two region with same Postal Code!')
    ]

    