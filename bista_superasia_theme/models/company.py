# -*- coding: utf-8 -*-

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    b2b_banner_image = fields.Binary(string='B2B Banner Image')
    b2c_banner_image = fields.Binary(string='B2C Banner Image')

