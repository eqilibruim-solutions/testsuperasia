import werkzeug.utils
import logging
_logger = logging.getLogger(__name__)

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.web.controllers.main import Home


class Extension_Home(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        response = super(Extension_Home, self).web_login()             

        user_obj=request.env['res.users']

        sales_rep = request.env['ir.model.data'].get_object('superasia_salesrep_app','group_sales_rep')

        group_list = [sales_rep.id]

        user_data=user_obj.search([('id','=',request.uid),('groups_id','in',group_list)])

        if user_data:
            return werkzeug.utils.redirect('/sales-rep/home')
        return response


class SalesAgentDashboard(WebsiteSale):

    @http.route(['/sales-rep/home'], type='http', auth="user", website=True, csrf=False)
    def sales_agent_home(self, **post):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            return request.not_found()
        return request.render('superasia_salesrep_app.sales_agent_home',{
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True
        })
    
    @http.route(['/sales-rep/all-accounts'], type='http', auth="user", website=True, csrf=False)
    def sales_agent_accounts(self, **post):
        if not request.env.user.user_has_groups('superasia_salesrep_app.group_sales_rep'):
            return request.not_found()
        b2b_user_group = request.env['ir.model.data'].sudo().get_object(
                                'superasiab2b_b2c','group_b2baccount')
        b2b_partner_ids = []
        if b2b_user_group:
            b2b_partner_ids = b2b_user_group.users.mapped('partner_id')
        
        context = {
            'footer_hide': True,
            'hide_install_pwa_btn': True,
            'hide_header': True,
            'b2b_partner_ids': b2b_partner_ids,
        }
        return request.render('superasia_salesrep_app.sales_rep_accounts', context)