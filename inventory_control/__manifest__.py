# -*- coding: utf-8 -*-
{
    'name': "Inventory Control",

    'summary': """Module to exercise control on inventory - validations & restrictions""",

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': 'Product',
    'version': '1.1',
    'depends': ['base','product','stock','stock_barcode'],
    # always loaded
    'data': [
        'views/views.xml',
        'views/stock_picking.xml',
    ],
    'qweb': [
        "static/src/xml/barcode_extended.xml",
    ],
}