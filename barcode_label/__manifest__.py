# -*- coding: utf-8 -*-
{
    'name': "Lot Barcode Label",

    'summary': """Lot Barcode""",

    'description': """
                Lot barcode report customization.
            """,

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': 'Product',
    'version': '1.1',
    'depends': ['base', 'stock', 'product', 'barcodes'],
    # always loaded
    'data': [
        'data/lot_report_paperformat.xml',
        # 'report/report_lot_barcode.xml',
        'report/report_lot_barcode_full.xml',
        'report/report_barcode_custom.xml',
        # 'report/report_barcode_custom_full.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
