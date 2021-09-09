# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def write(self, vals):
        res =  super(PurchaseOrder, self).write(vals)
        if 'state' in vals and self.state =='purchase':
            self.order_line.write({}) # for updating vendor selling pricelist of product
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    def write(self, vals):
        res =  super(PurchaseOrderLine, self).write(vals)
        for line in self:
            if line.state == 'purchase':
                partner_id = line.partner_id.id
                product_id = line.product_id.id
                latest_pol_id = self.latest_pol_date_approve(partner_id, product_id)
                if line.id == latest_pol_id:
                    product_tmpl_obj = line.product_id.product_tmpl_id
                    pricelist_val = {
                            'min_qty': 1,
                            'price': line.price_unit,
                            'currency_id': line.currency_id.id
                        }
                    vendor_pricelist = product_tmpl_obj.seller_ids.filtered(lambda x: x.name.id==partner_id)
                    if vendor_pricelist:
                        product_tmpl_obj.write({
                            'seller_ids': [
                                (1, vendor_pricelist[0].id, pricelist_val)
                            ]
                        })
                    else:
                        pricelist_val.update({
                            'name': partner_id,
                        })
                        product_tmpl_obj.write({
                            'seller_ids': [
                                (0,0, pricelist_val),
                            ]
                        })

        return res
    
    def latest_pol_date_approve(self, partner_id, product_id):
        """Latest purchase order line based on confirmation date where partner_id and product_id same.

        Args:
            partner_id (int): id of vendor
            product_id (int): id of product.product
        """
        cr = self._cr
        latest_pol_id_list, latest_pol_id = [], False
        if product_id and partner_id:
            cr.execute("""
                SELECT pol.id FROM purchase_order po 
                INNER JOIN purchase_order_line pol 
                ON pol.order_id=po.id 
                and pol.product_id=%s and po.partner_id=%s 
                ORDER BY date_approve DESC LIMIT 1;""", (product_id,partner_id))
            latest_pol_id_list = list(map(lambda id: id[0], cr.fetchall()))
        if latest_pol_id_list:
            latest_pol_id = int(latest_pol_id_list[0])
        return latest_pol_id
