# -*- coding: utf-8 -*-

from . import controllers
from . import models

from odoo import api, SUPERUSER_ID


def tableau_post_init_hook(cr,registry):

    env = api.Environment(cr,SUPERUSER_ID,{})
    env['ir.config_parameter'].set_param('tableau_direct_connecter.access_token', '*'*40)
    

def tableau_uninstall_hook(cr,registry):

    env = api.Environment(cr,SUPERUSER_ID,{})
    env['ir.config_parameter'].set_param('tableau_direct_connecter.access_token', '*'*40)
    