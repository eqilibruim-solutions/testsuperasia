# -*- coding: utf-8 -*-
from odoo import fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'
        
    priority_sequence = fields.Integer('Website View Sequence', default=500,
                         help="Determine the display order in the Website E-commerce Shop Page \n Lowest value(1,2,3,4...) will show in top")

    def _default_priority_sequence(self):
        self._cr.execute("SELECT MAX(priority_sequence) FROM %s" % self._table)
        max_sequence = self._cr.fetchone()[0]
        if max_sequence is None:
            return 500
        return max_sequence