# -*- coding: utf-8 -*-
{
    'name': "Change Location",

    'summary': """Change Location on Shipments""",

    'description': """
                Change Location in receipt and delivery order if user need to send/received the qty
                in different location.
            """,

    'author': "Shawaz Jahangiri",
    'website': "http://www.bistasolutions.com",
    'category': 'Inventory',
    'version': '1.0',
    'depends': ['base', 'stock'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/change_location_wiz_view.xml',
        'views/stock_picking_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
