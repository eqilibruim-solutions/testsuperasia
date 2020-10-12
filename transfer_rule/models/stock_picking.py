# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (https://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        rules_ids = self.env['internal.stock.orderpoint'].search([])
        rules_ids.run_rule()
        return res
