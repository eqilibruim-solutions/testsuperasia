# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista Web One2many Kanban',
    'version': '13.0.001',
    'license': 'AGPL-3',
    'category': 'Web',
    'summary': 'Display one2many widget as kanban',
    'description': """
       We need to define one2many field in kanban view definition and use
        for loop to display fields like:
        <t t-foreach="record.one2manyfield.raw_value" t-as='o'>
            <t t-esc="o.name">
            <t t-esc="o.many2onefield[1]">
        </t>
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['base', 'web', 'stock'],
    'data': [
        'views/templates.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
