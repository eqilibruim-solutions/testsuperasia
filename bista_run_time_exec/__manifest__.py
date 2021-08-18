# -*- coding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    RTL Code
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
{
    'name': 'Run Time Execution',
    'version': '1.0.1',
    'category': 'Generic Modules',
    'description': """Run Time Execution""",
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': "https://www.bistasolutions.com",
    'summary': """Using this module, 
        We can execute any script from the wizard.
        We can execute query, existing functions and can able to execute custom code also.""",
    'depends': ['base'],
    'init_xml': [],
    'data': ['wizard/run_time_exec_view.xml',
    'security/ir.model.access.csv'],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
