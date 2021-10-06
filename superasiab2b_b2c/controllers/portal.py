from odoo import http, _
from odoo.addons.portal.controllers.portal import (CustomerPortal,
                                                   get_records_pager)
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self):
        values = super(CustomerPortal, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        current_cart_order = request.website.sale_get_order()
        if current_cart_order.order_line:
            quotations = current_cart_order
        else:
            quotations = SaleOrder.search([
                ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
                ('state', 'in', ['draft', 'sent'])
            ])
        values['last_quotation_sent_count'] = 1 if quotations else 0
        return values
    
    def last_quotation_order(self):
        """
        latest/last quotation(sent/draft) id based on partner
        """
        SaleOrder = request.env['sale.order']
        partner = request.env.user.partner_id
        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['draft','sent'])
        ]
        current_cart_order = request.website.sale_get_order()
        if current_cart_order.order_line:
            latest_order = current_cart_order
        else:
            domain += [('id', '!=', current_cart_order.id)]
            latest_order = SaleOrder.search(domain, order='date_order desc', limit=1)
        return latest_order

    @http.route(['/my/last-confirm-order', '/my/last-confirm-order/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_last_confirm_order(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['draft','sent'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        # default sortby order
        sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('sale.order', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        # quotation_count = SaleOrder.search(domain)
        quotation_count = 1
        # make pager
        pager = portal_pager(
            url="/my/last-confirm-order",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=1
        )
        request.session['last_quotation_sent'] = False
        current_cart_order = request.website.sale_get_order()
        if current_cart_order.order_line:
            quotations = current_cart_order
        else:
            domain += [('id', '!=', current_cart_order.id)]
            quotations = SaleOrder.search(domain, order=sort_order, limit=1, offset=pager['offset'])
            if quotations[0].state == 'sent':
                request.session['last_quotation_sent'] = quotations[0].id

        values.update({
            'date': date_begin,
            'quotations': quotations.sudo(),
            'page_name': 'quote',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/last-confirm-order',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("sale.portal_my_quotations", values)
    
    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        response = super(CustomerPortal, self).portal_order_page(
            order_id, report_type, access_token, message, download, **kw)
        SaleOrder = request.env['sale.order']
        visible_cart_btn = False
        latest_order = self.last_quotation_order()
        if latest_order.state == 'sent':
            order_obj = SaleOrder.browse(int(order_id))
            if order_obj.state == 'sent' and order_obj.id == latest_order.id:
                visible_cart_btn = True
        response.qcontext['visible_cart_btn'] = visible_cart_btn
        return response
    

    @http.route(['/order-change-state'], type='json', auth="user")
    def order_state_change(self, order_id=None, **kw):
        error = ''
        partner = request.env.user.partner_id
        # TODO: check the partner id, is the partner owner/partner fo that order
        SaleOrder = request.env['sale.order'].sudo()
        sudo_order = SaleOrder.browse(int(order_id))
        if sudo_order:
            sudo_order.write({
                'b2b_confirmed': False
            })
            sudo_order.action_draft()
            request.session['sale_order_id'] = sudo_order.id
            # partner.write({
            #     'last_website_so_id': sudo_order.id
            # })
        return {
            'error': error,
            'done': ''
        }

