# -*- coding: utf-8 -*-
import hashlib
import logging
import os
import requests
import json
from odoo import models, fields, api,_
from ast import literal_eval
from odoo.exceptions import ValidationError
from odoo.addons.tableau_direct_connecter.url import (
   url,
)


class WebConnecterSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_connecter_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.env['ir.config_parameter'].set_param('tableau_direct_connecter.url', base_url + '/tableau/connecter/')
        return base_url + '/tableau/connecter/'

    url = fields.Char(string='Connecter Url', default=_get_connecter_url)
    access_token = fields.Char(string='Access Token', default=" " * 40)
    tableau_license_key = fields.Char(string='License Key')
    
    def set_values(self):
        res = super(WebConnecterSetting, self).set_values()
        self.env['ir.config_parameter'].set_param('tableau_direct_connecter.url', self.url)
        self.env['ir.config_parameter'].set_param('tableau_direct_connecter.access_token', self.access_token)
        if self.tableau_license_key:
            response = requests.post(url,data={"host_name":self.env['ir.config_parameter'].sudo().get_param('web.base.url'),"license_key":self.tableau_license_key},headers={'Accept':'application/json'})
            
            if response.status_code == 401:
                raise ValidationError('Please enter a valid license key !')
            if response.status_code == 408:
                raise ValidationError('Your trial is expired !')
            if response.status_code != 200:
                raise ValidationError('something went wrong on server side !')
            self.env['ir.config_parameter'].set_param('tableau_direct_connecter.tableau_license_key', self.tableau_license_key)
        else:
            self.env['ir.config_parameter'].set_param('tableau_direct_connecter.tableau_license_key', self.tableau_license_key)
        return res

    @api.model
    def get_values(self):
        res = super(WebConnecterSetting, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        url = ICPSudo.get_param('tableau_direct_connecter.url')
        access_token = ICPSudo.get_param('tableau_direct_connecter.access_token')
        tableau_license_key = ICPSudo.get_param('tableau_direct_connecter.tableau_license_key')
        res.update(
            url=url,
            access_token=access_token,
            tableau_license_key=tableau_license_key
        )

        return res

    def nonce(self, length=40, prefix=""):
        rbytes = os.urandom(length)
        return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))

    def generate_token(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        license_key = ICPSudo.get_param('tableau_direct_connecter.tableau_license_key')  
        if not license_key:
            raise ValidationError('Please enter valid license key then generate token') 
        self.env['ir.config_parameter'].set_param('tableau_direct_connecter.access_token', self.nonce())
