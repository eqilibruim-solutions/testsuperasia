# -*- coding: utf-8 -*-

from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    b2b_customer_type = fields.Selection([
        ('restaurant_owner', 'Restaurant'), ('grocery_owner', 'Grocery Store'), ('conv_owner', 'Convenience Store'),
        ('wholesale_dist', 'Wholesaler Distributor'), ('online_retailer', 'Online Retailer'), ('other', 'Other')
    ], string="Business Type")
