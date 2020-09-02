# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def _default_lot_sequence(self):
        if self.env.user.company_id.auto_generate_lot_serial:
            return self.env['ir.sequence'].next_by_code(
                    'bista.auto.lot.serial')
        else:
            return self.env['ir.sequence'].next_by_code(
                    'stock.lot.serial')

    name = fields.Char(
        'Lot/Serial Number', default=_default_lot_sequence,
        required=True, help="Unique Lot/Serial Number")
    partner_id = fields.Many2one(
        'res.partner', 'Vendor',
        help="show vendor in stock production lot form view.")
    barcode = fields.Char('Barcode', related='product_id.barcode')
    country_id = fields.Many2one('res.country', string="Country",
        related='partner_id.country_id')
    company_id = fields.Many2one('res.company', string='Company',
        required=True, default=lambda self: self.env.user.company_id,
        help="Company related to this Lot/Serial Number")


class StockMove(models.Model):
    _inherit = 'stock.move'

    expiry_date = fields.Datetime(string='Expiry Date')
    lot_no = fields.Many2one('stock.production.lot', string='Lot/Serial Number')


    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        result = super(StockMove, self) \
            ._prepare_move_line_vals(quantity, reserved_quant)
        ''' This method create auto generate lot/serial number
            when picking type is incoming, product track by lot/serial number
            and auto generate lot/serial number configation set true.
        '''
        if self.env.user.company_id.auto_generate_lot_serial:
            if self.picking_type_id.code == 'incoming' and \
                    self.product_id.tracking != 'none':
                seq = self.env.ref(
                    'auto_generate_lot_serial_number.sequence_auto_generate_lot_serial')
                seq.write({'prefix': self.env.user.company_id.prefix,
                           'padding': self.env.user.company_id.digits})
                lot_vals = {
                    'name': self.env['ir.sequence'].next_by_code(
                        'bista.auto.lot.serial'),
                    'product_id': self.product_id.id,
                    'product_uom_id': self.product_uom.id,
                    'partner_id': self.picking_partner_id.id,
                    'company_id': self.env.user.company_id.id
                    }
                if self.picking_type_id.use_create_lots and \
                        not self.picking_type_id.use_existing_lots:
                        lot_id = self.env['stock.production.lot'] \
                           .sudo().create(lot_vals)
                        if lot_id:
                            result.update({'lot_id': lot_id.id,
                                           'lot_name': lot_id.name})
                else:
                    lot_id_exist = self.env['stock.production.lot'].search([
                        ('product_id', '=', self.product_id.id)])
                    if lot_id_exist and \
                            not self.product_id.tracking == 'lot':
                        result.update({'lot_id': lot_id_exist[-1].id})
                    else:
                        if self.product_id.tracking == 'lot':
                            lot_id = self.env['stock.production.lot'] \
                                .sudo().create(lot_vals)
                            if lot_id:
                                result.update({'lot_id': lot_id.id})
                        else:
                            if not lot_id_exist:
                                lot_id = self.env['stock.production.lot'] \
                                    .sudo().create(lot_vals)
                                if lot_id:
                                    result.update({'lot_id': lot_id.id})

                    self.lot_no = lot_id.id
        return result

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for rec in self:
            picking_id = self.env['stock.picking'].search([('name', '=', rec.reference)])
            for ml in picking_id.move_ids_without_package:
                if ml.lot_no:
                    lot_id = ml.lot_no
                    if ml.expiry_date:
                        lot_id.removal_date = ml.expiry_date
        return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        for rec in self.move_ids_without_package:
            stock_production_id = self.env['stock.production.lot'].search([('id', '=', rec.lot_no.id)])
            stock_production_id.unlink()

