import base64
import io
from datetime import datetime
from dateutil import relativedelta
from datetime import datetime,timedelta
import datetime
import time
import json
import os
import logging
import requests
import werkzeug.utils
import werkzeug.wrappers
import psycopg2
from random import randint
import random

from itertools import islice
from xml.etree import ElementTree as ET
import unicodedata

import odoo
import re
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_stock.controllers.main import WebsiteSaleStock


from odoo import http, models, fields, _
from odoo import SUPERUSER_ID
from odoo.http import request
from odoo.tools import pycompat, OrderedSet
from odoo.addons.http_routing.models.ir_http import slug, _guess_mimetype
from odoo.addons.web.controllers.main import Binary
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import ValidationError


import urllib.request
_logger = logging.getLogger(__name__)


def redirect_with_hash(*args, **kw):
    """
        .. deprecated:: 8.0

        Use the ``http.redirect_with_hash()`` function instead.
    """
    return http.redirect_with_hash(*args, **kw)


class Extension_Home(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        _logger.info('========kw=========== %s' % kw)   
        response = super(Extension_Home, self).web_login()             
        _logger.info('========kw=========== %s' % kw)                
        _logger.info('========request.uid=========== %s' % request.uid)                

        user_obj=request.env['res.users']

        b2bid = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
        b2c = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')

        group_list = [b2bid.id,b2c.id]

        user_data=user_obj.search([('id','=',request.uid),('groups_id','in',group_list)])


        if user_data:
            return werkzeug.utils.redirect('/shop')

        return response

class superasiab2b_b2c(http.Controller):
    

    @http.route(['/b2b_activation'], type='http', auth="public", website=True,csrf=False)
    def b2b_activation(self, **post):
        error = {}
        default = {}
        env = request.env(user=SUPERUSER_ID)
        # country_obj=request.env['res.country']
        # country_data=country_obj.search([])
        # state_obj=request.env['res.country.state']
        # state_data=state_obj.search([])
        # countries = request.env['res.country'].sudo().search([])

        # states = request.env['res.country.state'].sudo().search([])

        return request.render('superasiab2b_b2c.b2b_activation',{
            'error':error,
            'default':default,
            # 'countries': countries,
            # 'states': states,
            })
        

  
    @http.route(['/b2baccountactivation'], Method=['POST'], type='http', auth="public", website=True,csrf=False)
    def b2baccountactivation(self, **post):
            error = {}
            default = {}
            current_date = time.strftime("%Y-%m-%d")
            env = request.env(user=SUPERUSER_ID)

            company_name = post.get('company_name')
            contact_name = post.get('contact_name')
            street = post.get('street')
            # city = post.get('city')
            # zipcode = post.get('zipcode')
            # country_id = post.get('country_id')
            # state_id = post.get('state_id')
            email = post.get('email')
            regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
            if not (re.search(regex,email)):  
                return request.render('superasiab2b_b2c.invalidemail',{
                    })         
            website = post.get('website')
            mobile = post.get('mobile')
            if mobile:
                mobile = '+1' + mobile


            orm_user = request.env['res.users']
            
            activeuser = orm_user.search([('login','=',email),('active','=',True)])
            if activeuser:
                return request.redirect('/repeat_user')


            superasiaid = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
            internalid = request.env['ir.model.data'].get_object('base','group_portal')

            group_list = [superasiaid.id,internalid.id]

            _logger.info('========group_list=========== %s' % group_list)                


            
            vals = {
            'name':company_name,
            'login' : email,
            'password':'Admin@123',
            'groups_id':[(6,0,group_list)],
            'active':False
            # 'odoobot_state':'disabled'

            }


            
            user_data = orm_user.create(vals)
            user_id = user_data.id

            profile_obj = request.env['res.partner']
            profile_ids=profile_obj.search([('user_id','=',user_data.id)])
            if profile_ids:
                return request.redirect('/accountexist')

            lead = self.env["crm.lead"].with_context(mail_create_nosubscribe=True).sudo().create({
                "contact_name": contact_name,
                # "description": ,
                "email_from": email,
                "name": company_name,
                "partner_name": company_name,
                "phone": mobile
            })


            # state_data = ''
            # _logger.info('========state_id======== %s' % state_id)
            # if state_id:

            #         state_obj=request.env['res.country.state']
            #         state_data=state_obj.search([('id','=',int(state_id))])
            #         _logger.info('========state_data======== %s' % state_data)
            #         state_data = state_data.id


            # country_data = ''
            # if country_id:
            #     country_obj=request.env['res.country']
            #     country_data=country_obj.search([('id','=',int(country_id))])
            #     country_data = country_data.id
            

            partner_id = user_data.partner_id
            login = user_data.login

            b2b_customer_type_key = post.get('b2b_customer_type')
            # Get b2b_customer_type selection field's label in res.partner model
            b2b_customer_type = dict(request.env['res.partner'].fields_get(
                allfields=['b2b_customer_type'])['b2b_customer_type']['selection'])[b2b_customer_type_key]

            profile_vals={
            'street': street,
            # 'city': city,
            # 'zip': zipcode,
            # 'country_id':country_data,
            # 'state_id':state_data,
            'email':login,
            'mobile':mobile,
            'website':website,
            'company_type':'company',
            'b2b_customer_type': b2b_customer_type_key
            }
            
            partner_id.write(profile_vals)

            
            if partner_id:
                ir_mail_server = request.env['ir.mail_server']
                mail_server_id = ir_mail_server.search([('name','=','Superasia')])
                smtp_user = str(mail_server_id.smtp_user)
                temp_obj = request.env['mail.template']
                template_data = temp_obj.search([('name','=','Account Activation')])
                if template_data:
                    replaced_data= template_data.body_html.replace('${object.company_name}',company_name)
                    replaced_dataone= replaced_data.replace('${object.email}',email)
                    # replaced_datatwo= replaced_dataone.replace('${object.company_name}',company_name)
                    msg = ir_mail_server.build_email(
                    email_from=smtp_user,     
                    email_to=[email],
                    subject="Account Activation",
                    body=replaced_dataone,
                    body_alternative="",
                    object_id=1,
                    subtype='html'
                    )
                    res = mail_server_id.send_email(msg)
                    admin_mail_template = "B2B Account Activation Request"
                    self.send_admin_activation_mail(admin_mail_template, company_name, email, user_id, contact_name, company_name, b2b_customer_type, mobile, street)

            return request.render('superasiab2b_b2c.reset_password_email', {
                'user_data': user_data
            })



    @http.route(['/b2cactivation'], type='http', auth="public", website=True,csrf=False)
    def b2cactivation(self, **post):
        error = {}
        default = {}
        env = request.env(user=SUPERUSER_ID)

        return request.render('superasiab2b_b2c.b2cactivation',{
            'error':error,
            'default':default,
            })
        

  
    @http.route(['/b2caccountactivation'], Method=['POST'], type='http', auth="public", website=True,csrf=False)
    def b2caccountactivation(self, **post):
            error = {}
            default = {}
            current_date = time.strftime("%Y-%m-%d")
            env = request.env(user=SUPERUSER_ID)

            company_name = post.get('company_name')
            b2b_customer_type = ""
            email = post.get('email')
            regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
            if not (re.search(regex,email)):  
                return request.render('superasiab2b_b2c.invalidemail',{
                    })         

            mobile = post.get('mobile')
            if mobile:
                mobile = '+1' + mobile
            password = post.get('password')
            confirmpassword = post.get('confirmpassword')
            _logger.info('========password=========== %s' % password)                
            _logger.info('========confirmpassword=========== %s' % confirmpassword)                
            if password != confirmpassword:
                return request.render('superasiab2b_b2c.confirmpassword',{
                    })



            orm_user = request.env['res.users']
            
            activeuser = orm_user.search([('login','=',email),('active','=',True)])
            if activeuser:
                return request.redirect('/repeat_user')




            internalid = request.env['ir.model.data'].get_object('base','group_portal')
            b2c = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')

            group_list = [internalid.id,b2c.id]
            _logger.info('========group_list=========== %s' % group_list)                

            pricelistid = request.env['product.pricelist'].search([('group_id','in',internalid.id)])
            _logger.info('========pricelistid=========== %s' % pricelistid) 
            
            vals = {
            'name':company_name,
            'login' : email,
            'password':confirmpassword,
            'groups_id':[(6,0,group_list)],
            # 'odoobot_state':'disabled'

            }


            
            user_data = orm_user.create(vals)
            user_id = user_data.id

            profile_obj = request.env['res.partner']
            profile_ids=profile_obj.search([('user_id','=',user_data.id)])
            if profile_ids:
                return request.redirect('/accountexist')

            

            partner_id = user_data.partner_id
            login = user_data.login

            profile_vals={
            'email':login,
            'company_type':'company',
            'property_product_pricelist':pricelistid.id
            }
            
            partner_id.write(profile_vals)

            
            if partner_id:
                ir_mail_server = request.env['ir.mail_server']
                mail_server_id = ir_mail_server.search([('name','=','Superasia')])
                smtp_user = str(mail_server_id.smtp_user)
                temp_obj = request.env['mail.template']
                template_data = temp_obj.search([('name','=','Account Activation')])
                if template_data:
                    replaced_data= template_data.body_html.replace('${object.company_name}',company_name)
                    replaced_dataone= replaced_data.replace('${object.email}',email)
                    msg = ir_mail_server.build_email(
                    email_from=smtp_user,     
                    email_to=[email],
                    subject="Account Activation",
                    body=replaced_dataone,
                    body_alternative="",
                    object_id=1,
                    subtype='html'
                    )
                    res = mail_server_id.send_email(msg)
                    admin_mail_template = "New B2C User"
                    self.send_admin_activation_mail(admin_mail_template, company_name, email, user_id, company_name, b2b_customer_type, company_name, mobile, "")

            return request.render('superasiab2b_b2c.reset_password_emailb2c',{
                'user_data': user_data
            })

    @staticmethod
    def send_admin_activation_mail(template_name, company, user_email, partner_id, user_name, business_name="", b2b_customer_type="", contact_no="", address=""):
        sa_email = "hello@superasia.ca"
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        usr_url = "{}/web?#id={}&action=74&model=res.users&view_type=form&cids=1&menu_id=4".format(base_url, partner_id)

        ir_mail_server = request.env['ir.mail_server']
        mail_server_id = ir_mail_server.search([('name', '=', 'Superasia')])
        smtp_user = str(mail_server_id.smtp_user)
        temp_obj = request.env['mail.template']
        template_data = temp_obj.search([('name', '=', template_name)])
        if template_data:
            replaced_data = template_data.body_html.replace('${object.company_name}', company)
            replaced_dataone = replaced_data.replace('${object.signup_url}', usr_url).replace('${object.email}', user_email).replace('${website_url}', base_url).replace('${full_name}', user_name).replace('${business_name}', business_name).replace('${business_type}', b2b_customer_type).replace('${contact_no}', contact_no).replace('${address}', address)
            mail_subject = "{} for {}".format(template_name, user_email)
            msg = ir_mail_server.build_email(
                email_from=smtp_user,
                email_to=[sa_email],
                subject=mail_subject,
                body=replaced_dataone,
                body_alternative="",
                object_id=1,
                subtype='html'
            )
            res = mail_server_id.send_email(msg)
    
    @http.route(['/acceptconditions'], Method=['POST'], type='http', auth="public", website=True)
    def acceptconditions(self, **post):
        return request.render('superasiab2b_b2c.acceptconditions',{

                })

        

    @http.route(['/repeat_user'], Method=['POST'], type='http', auth="public", website=True)
    def repeat_user(self, **post):

        return request.render('superasiab2b_b2c.repeat_user',{
                })

    @http.route(['/accountexist'], Method=['POST'], type='http', auth="public", website=True)
    def accountexist(self, **post):

        return request.render('superasiab2b_b2c.portaluserexist',{
                })



class WebsiteSaleStocksuperasia(WebsiteSaleStock):
    @http.route()
    def payment_transaction(self, *args, **kwargs):
        """ Payment transaction override to double check cart quantities before
        placing the order
        """
        order = request.website.sale_get_order()
        values = []
        for line in order.order_line:
            if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
                cart_qty = sum(order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                # avl_qty = line.product_id.with_context(warehouse=order.warehouse_id.id).virtual_available

                avl_qty = line.product_id.qty_available
                _logger.info('========avl_qty=========== %s' % avl_qty)

                b2buser = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2baccount')
                b2c = request.env['ir.model.data'].get_object('superasiab2b_b2c','group_b2cuser')
                userobj = request.env['res.users']
                b2busergroup = userobj.search([('id','=',request.uid),('groups_id','in',b2buser.id)])
                b2cusers = userobj.search([('id','=',request.uid),('groups_id','in',b2c.id)])

                public=userobj.search([('id','=',request.uid)])

                publicuser = False
                if public.partner_id.name == 'Public user':
                    publicuser =public
                    _logger.info('===========publicuser======== %s' % publicuser)

                product_uom = line.product_id.uom_id
                _logger.info('===========product_uom======== %s' % product_uom)
                factor_inv = 0
                if product_uom.factor_inv:
                    factor_inv = product_uom.factor_inv
                _logger.info('===========factor_inv======== %s' % factor_inv)


                if b2cusers:

                    product_uom = line.product_id.b2buom_id
                    if factor_inv > 0:
                        avl_qty = avl_qty*factor_inv
                    _logger.info('========avl_qty===b2cusers======== %s' % avl_qty)

                if publicuser:

                    product_uom = line.product_id.b2buom_id
                    if factor_inv > 0:
                        avl_qty = avl_qty*factor_inv
                    _logger.info('========avl_qty===publicuser======== %s' % avl_qty)
                _logger.info('========cart_qty=========== %s' % cart_qty)

                if cart_qty > avl_qty:
                    values.append(_('You ask for %s products but only %s is available') % (cart_qty, avl_qty if avl_qty > 0 else 0))

        if values:
            raise ValidationError('. '.join(values) + '.')
        return super(WebsiteSaleStock, self).payment_transaction(*args, **kwargs)
