# -*- coding: utf-8 -*-

from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    app_category_1 = fields.Many2one('product.public.category', string='App Category 1')
    app_category_2 = fields.Many2one('product.public.category', string='App Category 2')

