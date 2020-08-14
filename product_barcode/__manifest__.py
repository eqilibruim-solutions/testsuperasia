# -*- coding: utf-8 -*-
{
    'name': "Product Barcode",

    'summary': """Product Barcode""",

    'description': """
                Product Barcode customization.
            """,

    'author': "Shawaz Jahangiri",
    'website': "http://www.bistasolutions.com",
    'category': 'Product',
    'version': '1.0',
    'depends': ['base', 'product'],
    # always loaded
    'data': [
        'views/product_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
