import logging
_logger = logging.getLogger(__name__)

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale



class SalesAgentDashboard(WebsiteSale):

    @http.route(['/sales-rep/home'], type='http', auth="user", website=True, csrf=False)
    def sales_agent_home(self, **post):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            return request.not_found()
        return request.render('superasia_salesrep_app.sales_agent_home',{
            'footer_hide': True,
            'hide_install_pwa_btn': True
        })