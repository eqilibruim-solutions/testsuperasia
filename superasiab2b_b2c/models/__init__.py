# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from . import portal_manager
# from . import ir_ui_menu_inherit
from . import website_config_settings, sale_order, crm_lead

# ****************

# smtp_user,smtp_pass , remove group access
# /base/models/ir_mail_server.py

# record rules
# Public product template --- remove websitepublished domain and give all access
# respartner-public in internal user
# rescompany -- add public  in admin
# res.partner.rule.private.employee -- add portal group
#Lots/Serial Numbers multi-company - False

# in public customer add email address in db

