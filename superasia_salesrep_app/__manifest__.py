
{
    'name': "SuperAsia Sales Representative App",
    'version': '13.0.1.0.0',
    'category': 'Website',
    'summary': 'SuperAsia Sales Representative App',
    'description': """Responsive dashboard for sales representative.""",
    'author': "Bista Solutions Pvt. Ltd.-Saidul Tuhin",
    'website': 'www.bistasolutions.com',
    'license': 'AGPL-3',
    "depends": ['base','web','website','portal','sale','website_sale','bista_superasia_theme','superasiab2b_b2c'],
    "data": [
        'security/ir.model.access.csv',
        'security/access_rights.xml',
        'views/assets.xml',
        'views/sales_agent_home.xml',
        'views/accounts.xml',
        'views/add-account.xml',
        'views/account-detail.xml',
        'views/product-listing.xml',
        'views/website_navbar_inh.xml',
        'views/cart_page_inherit.xml',
    ],

    "installable": True,
    "application":True
}
