from odoo import models, api, fields

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    responsible_user = fields.Many2one(
        'res.users', 'Responsible',
        domain=lambda self: [('groups_id', 'in', self.env.ref('stock.group_stock_user').id)])

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    user_id = fields.Many2one(default=False) # over ride default attribute
        
    @api.model
    def create(self, vals):
        picking_type_id = vals.get("picking_type_id")
        user_id = vals.get("user_id", False)
        if picking_type_id and not user_id:
            picking_type_obj = self.env['stock.picking.type'].browse(int(picking_type_id))
            if picking_type_obj.code == 'internal' and picking_type_obj.responsible_user:
                vals.update({
                    'user_id': picking_type_obj.responsible_user.id
                })
                
        res = super(StockPicking, self).create(vals)
        return res