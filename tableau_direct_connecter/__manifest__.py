# -*- coding: utf-8 -*-
{
    'name': "tableau_direct_connecter",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Techneith",
    'website': "https://www.techneith.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],
    'images': ['static/description/icon.png'],

    # always loaded
    'data': [
        'views/settings.xml',
        # 'views/resources.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "application": True,
    "installable": True,
    "post_init_hook":"tableau_post_init_hook",
    "uninstall_hook":"tableau_uninstall_hook"
}
