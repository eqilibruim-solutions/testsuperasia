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
    'depends': ['base', 'stock', ],
    # always loaded
    'data': [
        'views/lot_management.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}