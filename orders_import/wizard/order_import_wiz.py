# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api, _
import base64
import io
from odoo.exceptions import Warning
from odoo.tools import pycompat
from datetime import datetime


class OrdersImport(models.TransientModel):
    _name = 'orders.import'
    _description = "Import Orders from files"

    import_file = fields.Binary('File', help="Select file for import orders.")
    import_file_name = fields.Char('File Name')

    def import_orders(self):
        """
        Upload xlsx file data into multiple objects.
        :return:
        """
        payment_term_obj = self.env['account.payment.term']
        product_obj = self.env['product.product']
        partner_obj = self.env['res.partner']
        sale_obj = self.env['sale.order']
        user_obj = self.env['res.users']
        if not self.import_file:
            raise Warning(_("Please attach file then Upload"))
        if not self.import_file_name.endswith('.csv'):
            raise Warning(_("Please upload file only of '.csv' format!"))
        header_seq = ['customer', 'order_date', 'orderID', 'customer_po', 'start_ship_date', 'bill_street',
                      'bill_street2', 'bill_city', 'bill_state', 'bill_postcode', 'bill_country', 'ship_street',
                      'ship_street2', 'ship_city', 'ship_state', 'ship_postcode', 'ship_country', 'phone', 'fax',
                      'email', 'contact', 'rep', 'cancel_date', 'ship_method', 'notes', 'sku', 'qty', 'description',
                      'unit_price', 'unit_discount', 'customer_id', 'payment_terms', 'source', 'externalOrderID',
                      'original_unit_price']
        try:
            csv_data = self.import_file or b''
            csv_data = base64.b64decode(csv_data)
            file_data = pycompat.csv_reader(io.BytesIO(csv_data), delimiter=',')
            i = 1
            data_lst = []
            order_lst = []
            for row in file_data:
                if i > 1:
                    if row[2] not in order_lst:
                        order_lst.append(row[2])
                    data_lst.append({'customer': row[0], 'order_date': row[1], 'orderID': row[2], 'customer_po': row[3],
                                     'start_ship_date': row[4], 'bill_street': row[5], 'bill_street2': row[6],
                                     'bill_city': row[7], 'bill_state': row[8], 'bill_postcode': row[9],
                                     'bill_country': row[10], 'ship_street': row[11], 'ship_street2': row[12],
                                     'ship_city': row[13], 'ship_state': row[14], 'ship_postcode': row[15],
                                     'ship_country': row[16], 'phone': row[17], 'fax': row[18], 'email': row[19],
                                     'contact': row[20], 'rep': row[21], 'cancel_date': row[22], 'ship_method': row[23],
                                     'notes': row[24], 'sku': row[25], 'qty': float(row[26]), 'description': row[27],
                                     'unit_price': float(row[28]), 'unit_discount': float(row[29]),
                                     'customer_id': row[30],
                                     'payment_terms': row[31], 'source': row[32], 'externalOrderID': row[33],
                                     'original_unit_price': float(row[34])
                                     })
                if i == 1:
                    header = [cell.strip() for cell in row]
                    if header != header_seq:
                        raise Warning(_("Please upload same header sequence as below\n%s" % header_seq))
                i += 1
            existing_order = sale_obj.search([('import_order_id', 'in', order_lst)])
            if existing_order:
                raise Warning(_("Order already exists:\n%s" % existing_order.mapped('import_order_id')))
        except Exception as e:
            raise Warning(_(e))

        sale_order_dict = {}
        for val in data_lst:
            partner_id = False
            try:
                if val.get('customer'):
                    partner_id = partner_obj.search([('email', '=', val.get('email'))])
                    if not partner_id:
                        country_id = self.env['res.country'].search([('name', '=', val.get('bill_country'))])
                        state_id = self.env['res.country.state'].search([('code', '=', val.get('bill_state')),
                                                                         ('country_id', '=', country_id.id)])
                        partner_id = partner_obj.create({'name': val.get('customer'),
                                                         'street': val.get('bill_street'),
                                                         'street2': val.get('bill_street2'),
                                                         'city': val.get('bill_city'),
                                                         'state_id': state_id and state_id.id or False,
                                                         'country_id': country_id and country_id.id or False,
                                                         'zip': val.get('bill_postcode'),
                                                         'type': 'contact',
                                                         'phone': val.get('phone'),
                                                         # 'fax': val.get('fax'),
                                                         'email': val.get('email')})
                if val.get('orderID'):
                    if val.get('sku'):
                        product_code = val.get('sku').strip()
                        product_data = product_obj.search_read([('default_code', '=', product_code)],
                                                               ['id', 'uom_id'])
                        qty = float(val.get('qty'))
                        uom_id = product_data[0].get('uom_id')[0] if product_data \
                            else False
                        unit_price = float(val.get('unit_price', 0.0))
                        product_id = product_data[0].get('id')
                        display_name = val.get('description')
                        order_lines = (0, 0, {'product_id': product_id,
                                              'name': display_name,
                                              'product_uom_qty': qty,
                                              'tax_id': [],
                                              'price_unit': unit_price,
                                              'product_uom': uom_id,
                                              'discount': float(val.get('unit_discount', 0.0))})

                    if val.get('orderID') in sale_order_dict.keys():
                        sale_order_dict.get(val.get('orderID')).get('order_line').append(order_lines)
                    else:
                        payment_term_id = payment_term_obj.search([('name', '=', val.get('payment_terms'))])
                        user_id = user_obj.search([('name', '=', val.get('rep'))])
                        date_order = datetime.strptime(val.get('order_date'), '%d/%m/%Y')
                        sale_order_dict.update(
                            {val.get('orderID'): {'partner_id': partner_id and partner_id.id or False,
                                                  'date_order': date_order,
                                                  'note': val.get('notes'),
                                                  'payment_term_id': payment_term_id and payment_term_id.id or False,
                                                  'order_line': [order_lines],
                                                  'import_order_id': val.get('orderID'),
                                                  'client_order_ref': val.get('customer_po'),
                                                  'user_id': user_id and user_id.id or False
                                                  }
                             })
            except Exception as e:
                raise Warning(_(e))

        for order in sale_order_dict.values():
            sale_obj.create(order)
        return True
