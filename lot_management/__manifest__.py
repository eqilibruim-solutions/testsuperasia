# -*- coding: utf-8 -*-
{
    'name': "Lot Management",

    'summary': """Lot Management""",

    'description': """
                changes pertaining to lot management.
            """,

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",
    'category': 'Product',
    'version': '1.1',
    'depends': ['base', 'stock', 'product_expiry'],
    # always loaded
    'data': [
        'views/lot_management.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}