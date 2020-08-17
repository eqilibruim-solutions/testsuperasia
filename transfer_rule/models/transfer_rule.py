# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (https://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.osv import expression
from datetime import datetime


class InternalStockOrderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _name = "internal.stock.orderpoint"
    _description = "Minimum Inventory Rule"

    @api.model
    def default_get(self, fields):
        res = super(InternalStockOrderpoint, self).default_get(fields)
        warehouse = None
        if 'warehouse_id' not in res and res.get('company_id'):
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', res['company_id'])], limit=1)
        if warehouse:
            res['warehouse_id'] = warehouse.id
            res['location_id'] = warehouse.lot_stock_id.id
        return res

    # def _get_source_location(self):
    #     self.env['ir.config_parameter'].sudo().get_param('source_location')
    #     return self.env['ir.config_parameter'].sudo().get_param('source_location')

    name = fields.Char(
        'Name', copy=False, required=True, readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('internal.stock.orderpoint'))
    active = fields.Boolean(
        'Active', default=True,
        help="If the active field is set to False, it will allow you to hide the orderpoint without removing it.")
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse',
        check_company=True, ondelete="cascade", required=True)
    location_id = fields.Many2one(
        'stock.location', 'Location',
        ondelete="cascade", required=True, check_company=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        ondelete='cascade', required=True, check_company=True)
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure', related='product_id.uom_id',
        readonly=True, required=True,
        default=lambda self: self._context.get('product_uom', False))
    product_uom_name = fields.Char(string='Product unit of measure label', related='product_uom.display_name',
                                   readonly=True)
    product_min_qty = fields.Float(
        'Minimum Quantity', digits='Product Unit of Measure', required=True,
        help="When the virtual stock equals to or goes below the Min Quantity specified for this field, Odoo generates "
             "a procurement to bring the forecasted quantity to the Max Quantity.")
    product_max_qty = fields.Float(
        'Maximum Quantity', digits='Product Unit of Measure', required=True,
        help="When the virtual stock goes below the Min Quantity, Odoo generates "
             "a procurement to bring the forecasted quantity to the Quantity specified as Max Quantity.")
    qty_multiple = fields.Float(
        'Qty Multiple', digits='Product Unit of Measure',
        default=1, required=True,
        help="The procurement quantity will be rounded up to this multiple."
             "If it is 0, the exact quantity will be used.")
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, index=True,
        default=lambda self: self.env.company)
    allowed_location_ids = fields.One2many(comodel_name='stock.location', compute='_compute_allowed_location_ids')

    @api.depends('warehouse_id')
    def _compute_allowed_location_ids(self):
        loc_domain = [('usage', 'in', ('internal', 'view'))]
        # We want to keep only the locations
        #  - strictly belonging to our warehouse
        #  - not belonging to any warehouses
        for orderpoint in self:
            other_warehouses = self.env['stock.warehouse'].search([('id', '!=', orderpoint.warehouse_id.id)])
            for view_location_id in other_warehouses.mapped('view_location_id'):
                loc_domain = expression.AND([loc_domain, ['!', ('id', 'child_of', view_location_id.id)]])
                loc_domain = expression.AND(
                    [loc_domain, ['|', ('company_id', '=', False), ('company_id', '=', orderpoint.company_id.id)]])
            orderpoint.allowed_location_ids = self.env['stock.location'].search(loc_domain)

    def run_rule(self):
        move_vals = []
        pick_vals = {}
        source_location_id = self.env.company.internal_location_id.id
        for rule in self:
            product_dict = rule.product_id.with_context(
                {'location': rule.location_id.id})._compute_quantities_dict(None, None, None, from_date=False,
                                                                            to_date=datetime.now())
            internal_product_dict = rule.product_id.with_context(
                {'location': source_location_id})._compute_quantities_dict(None, None, None, from_date=False,
                                                                           to_date=datetime.now())
            if rule.product_min_qty > product_dict.get(rule.product_id.id)['virtual_available'] and \
                    internal_product_dict.get(rule.product_id.id)['free_qty']:
                move_vals.append((0, 0, {
                    'product_id': rule.product_id.id,
                    'name': rule.product_id.name,
                    'product_uom': rule.product_id.uom_po_id.id,
                    'product_uom_qty': internal_product_dict.get(rule.product_id.id)[
                        'free_qty'] if rule.product_max_qty > internal_product_dict.get(rule.product_id.id)[
                        'free_qty'] else rule.product_max_qty,
                    'location_id': source_location_id,
                    'location_dest_id': rule.location_id.id,
                }))
                if rule.location_id.id not in pick_vals.keys():
                    pick_vals.update({rule.location_id.id: {
                        'location_id': source_location_id,
                        'location_dest_id': rule.location_id.id,
                        'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                        'immediate_transfer': False,
                        'move_ids_without_package': move_vals if move_vals else [],
                        'origin': rule.name,
                    }})
                else:
                    picking_dict = pick_vals.get(rule.location_id.id)
                    picking_dict.get('move_ids_without_package').append(move_vals)
                    picking_dict['origin'] += rule.name

        picking_obj = self.env['stock.picking']
        for picking in pick_vals.values():
            picking_id = picking_obj.create(picking)
            picking_id.action_confirm()
            picking_id.action_assign()
        return True
