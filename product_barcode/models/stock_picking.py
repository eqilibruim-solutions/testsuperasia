# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # def get_barcode_view_state(self):
    #     pickings = super(StockPicking, self).get_barcode_view_state()
    #
    #         picking['move_line_ids'] = sorted(picking['move_line_ids'],
    #                                           key=lambda i: i['sequence'],
    #                                           reverse=True)
    #     return pickings
    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        fields_to_read = self._get_picking_fields_to_read()
        pickings = self.read(fields_to_read)
        for picking in pickings:
            picking['move_line_ids'] = self.env['stock.move.line'].browse(picking.pop('move_line_ids')).read([
                'product_id',
                'location_id',
                'location_dest_id',
                'location_bin',
                'qty_done',
                'display_name',
                'product_uom_qty',
                'product_uom_id',
                'product_barcode',
                'owner_id',
                'lot_id',
                'lot_name',
                'package_id',
                'result_package_id',
                'dummy_id',
                'sequence',
            ])
            picking['move_line_ids'] = sorted(picking['move_line_ids'],
                                              key=lambda i: i['sequence'])
            product_ids = tuple(set([move_line_id['product_id'][0] for move_line_id in picking['move_line_ids']]))
            print('-----------------product_ids----------------', product_ids)
            tracking_and_barcode_per_product_id = {}
            for res in self.env['product.product'].search_read([('id', 'in', product_ids)], ['tracking', 'barcode']):
                tracking_and_barcode_per_product_id[res.pop("id")] = res

            archive_products = self.move_line_ids.filtered(
                lambda p: p.product_id.active == False)
            if archive_products:
                raise UserError(
                    _("The following products are Archived. Please Unarchive to process. \n %s") % (
                        archive_products.mapped('display_name')))
            for move_line_id in picking['move_line_ids']:

                id = move_line_id.pop('product_id')[0]
                move_line_id['product_id'] = {"id": id, **tracking_and_barcode_per_product_id[id]}
                id, name = move_line_id.pop('location_id')
                move_line_id['location_id'] = {"id": id, "display_name": name}
                id, name = move_line_id.pop('location_dest_id')
                move_line_id['location_dest_id'] = {"id": id, "display_name": name}
            id, name = picking.pop('location_id')
            picking['location_id'] = self.env['stock.location'].search_read([("id", "=", id)], [
                'parent_path'
            ])[0]
            picking['location_id'].update({"id": id, "display_name": name})
            id, name = picking.pop('location_dest_id')
            picking['location_dest_id'] = self.env['stock.location'].search_read([("id", "=", id)], [
                'parent_path'
            ])[0]
            picking['location_dest_id'].update({"id": id, "display_name": name})
            picking['group_stock_multi_locations'] = self.env.user.has_group('stock.group_stock_multi_locations')
            picking['group_tracking_owner'] = self.env.user.has_group('stock.group_tracking_owner')
            picking['group_tracking_lot'] = self.env.user.has_group('stock.group_tracking_lot')
            picking['group_production_lot'] = self.env.user.has_group('stock.group_production_lot')
            picking['group_uom'] = self.env.user.has_group('uom.group_uom')
            picking['use_create_lots'] = self.env['stock.picking.type'].browse(picking['picking_type_id'][0]).use_create_lots
            picking['use_existing_lots'] = self.env['stock.picking.type'].browse(picking['picking_type_id'][0]).use_existing_lots
            picking['show_entire_packs'] = self.env['stock.picking.type'].browse(picking['picking_type_id'][0]).show_entire_packs
            picking['actionReportDeliverySlipId'] = self.env.ref('stock.action_report_delivery').id
            picking['actionReportBarcodesZplId'] = self.env.ref('stock.action_label_transfer_template_zpl').id
            picking['actionReportBarcodesPdfId'] = self.env.ref('stock.action_label_transfer_template_pdf').id
            picking['stock_group_manager'] = self.env.user.has_group('stock.group_stock_manager')

            if self.env.company.nomenclature_id:
                picking['nomenclature_id'] = [self.env.company.nomenclature_id.id]
        return pickings
    def check_product_on_barcode_scanned(self, product=None):
        '''This method used to check product is part of order or not.'''

        move_line_id = self.move_line_ids_without_package.filtered(
            lambda
                rec: rec.move_id and rec.product_id.id == product)
        if self.picking_type_code in ('outgoing', 'internal', 'incoming'):
            if move_line_id:
                return (True, 'existing_line')
            else:
                if self.env.user.has_group('stock.group_stock_manager'):
                    return (True, 'existing_line')
                else:
                    return (True, 'extra_line')

        else:
            return (True, 'incoming_transfer')

    def check_lot_on_barcode_scanned(self, barcode=None, qty=None):
        '''This methodu used to check the lot/serial number is part of order or not.'''
        ml_id = self.move_line_ids_without_package.filtered(
            lambda
                rec: rec.move_id and rec.lot_id.name == barcode)
        if self.picking_type_code in ('outgoing', 'internal', 'incoming'):
            if ml_id:
                return (True, 'existing_lot')
            else:
                if self.env.user.has_group('stock.group_stock_manager'):
                    return (True, 'existing_lot')
                else:
                    return (True, 'extra_lot')

    def action_generate_backorder_wizard(self):
        view = self.env.ref('stock.view_backorder_confirmation')
        backorder_ml_ids = self.move_line_ids.filtered(lambda m: m.qty_done < m.product_uom_qty)
        product_name = ''
        for rec in backorder_ml_ids:
            product_name += rec.product_id.display_name + ' %s\n' % str(rec.product_uom_qty - rec.qty_done)
        wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in self],
                                                               'product_name': product_name})
        return {
            'name': _('Create Backorder?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

class StockMove(models.Model):
    _inherit = 'stock.move.line'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence', related='location_id.sequence')
