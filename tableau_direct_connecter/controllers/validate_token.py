import re  # line:1
import ast  # line:2
import functools  # line:3
import logging  # line:4
from odoo.exceptions import AccessError  # line:5
from odoo import http  # line:7
from odoo.addons.tableau_direct_connecter.common import (invalid_response, valid_response, )  # line:11
from odoo.http import request  # line:12


def validate_token(OO0000OOO00OOOOOO):  # line:14
    ""  # line:15

    @functools.wraps(OO0000OOO00OOOOOO)  # line:17
    def O0OO00000000O0OOO(O00000000O00OO0OO, *OOO0O00O00OOO0OOO, **O0000O0O0000O0O00):  # line:18
        ""  # line:19
        O0OOO0O0OOOO00O00 = request.env['ir.config_parameter'].sudo()  # line:20
        O000OOO0000O000OO = request.httprequest.headers.get("Authorization")  # line:21
        if not O000OOO0000O000OO:  # line:22
            return invalid_response("access_token_not_found", "missing access token in request header", 401,
                                    check_json=request.__dict__.get('jsonrequest', None))  # line:23
        O0O0OO00OO0OO00OO = (O0OOO0O0OOOO00O00.get_param('tableau_direct_connecter.access_token'))  # line:26
        if O0O0OO00OO0OO00OO != O000OOO0000O000OO:  # line:27
            return invalid_response("access_token", "token seems to have expired or invalid", 401,
                                    check_json=request.__dict__.get('jsonrequest', None))  # line:28
        return OO0000OOO00OOOOOO(O00000000O00OO0OO, *OOO0O00O00OOO0OOO, **O0000O0O0000O0O00)  # line:30

    return O0OO00000000O0OOO
