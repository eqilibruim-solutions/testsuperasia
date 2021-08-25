# -*- coding: utf-8 -*-
{
    'name': "Tableau Odoo Direct Connector",

    'summary': """
        This connector allows you to connect Odoo data with Tableau and shows ALL your Odoo data onto Tableau.""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Techneith",
    'website': "https://www.techneith.com",
    'price':1150,
    'currency':'USD',
    'category': 'Business Tool',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],
    'images': ['static/description/icon.png'],

    # always loaded
    'data': [
        'views/settings.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "application": True,
    "installable": True,
}
