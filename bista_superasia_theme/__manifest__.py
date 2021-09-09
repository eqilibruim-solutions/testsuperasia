
{
    'name': "SuperAsia Website Theme",
    'version': '13.0.1.0.0',
    'category': 'Website',
    'summary': 'SuperAsia Website Theme.',
    'description': """SuperAsia Website Theme.""",
    'author': "Bista Solutions Pvt. Ltd.",
    'website': 'www.bistasolutions.com',
    'license': 'AGPL-3',
    "depends": ['base','web','website','portal','bista_web_pwa','superasiab2b_b2c','sale','payment','website_sale','website_form','auth_signup','website_sale_delivery','website_sale_stock','sale_stock'],
    "data": [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/homepage_template.xml',
        'views/header_footer_inherit.xml',
        'views/shop_page_inherit.xml',
        'views/cart_page_inherit.xml',
        'views/contact_us_template_inherit.xml',
        'views/portal_template.xml',
        'views/company.xml',
        'views/gta_code.xml',
        'views/delivery_carrier.xml',
        'views/check_postal_code.xml',
        'views/product_template.xml',
    ],

    "installable": True,
    "application":True
}
