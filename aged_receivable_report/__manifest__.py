# -*- coding: utf-8 -*-

{
    'name': "Aged Receivable Report",
    'category': 'Account',
    'summary': "Aged Receivable Report",
    'description': """,
===================================================================
    This module is show Aged Receivable report with all details in list view.
    """,
    'version': '13.0.1.0.0',
    'author': 'Bista solutions Pvt Ltd',
    'website': 'https://www.bistasolutions.com',
    'depends': ['base', 'account', 'sale_management', 'account_reports'],
    'data': [
        'security/receivable_report_data_security.xml',
        'security/ir.model.access.csv',
        'views/account_receivable_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True
}
