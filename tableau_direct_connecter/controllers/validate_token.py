import re
import ast
import functools
import logging
import json
from odoo.exceptions import AccessError
import requests
from odoo import http
from odoo.addons.tableau_direct_connecter.common import (
    invalid_response,
    valid_response,
)
from odoo.addons.tableau_direct_connecter.url import (
   url,
)
from odoo.http import request

def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        ICPSudo = request.env['ir.config_parameter'].sudo()
        access_token = request.httprequest.headers.get("Authorization")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401,check_json = request.__dict__.get('jsonrequest',None))
        access_token_data = (
            ICPSudo.get_param('tableau_direct_connecter.access_token')
        )
        if access_token_data != access_token or access_token == '*'*40:
            return invalid_response("access_token", "token seems to have expired or invalid", 401,check_json = request.__dict__.get('jsonrequest',None))

        return func(self, *args, **kwargs)

    return wrap


def validate_license(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        
        ICPSudo = request.env['ir.config_parameter'].sudo()
        (host_name,license_key) = (ICPSudo.get_param('web.base.url'),ICPSudo.get_param('tableau_direct_connecter.tableau_license_key'))
        response = requests.post(url,data={"host_name":host_name,"license_key":license_key})
        
        if response.status_code == 401:
            return invalid_response("License", "Please enter a valid license key !", 401,check_json = request.__dict__.get('jsonrequest',None))
        if response.status_code == 408:
            return invalid_response("License", "Your trial is expired !", 408,check_json = request.__dict__.get('jsonrequest',None))
        if response.status_code != 200:
            return invalid_response("error","Something went wrong !" , response.status_code,check_json = request.__dict__.get('jsonrequest',None))
        
        return func(self, *args, **kwargs)

    return wrap