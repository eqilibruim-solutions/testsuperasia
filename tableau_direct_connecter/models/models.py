import hashlib  # line:2
import logging  # line:3
import os  # line:4
from odoo import models, fields, api  # line:5
from ast import literal_eval  # line:6


class WebConnecterSetting(models.TransientModel):  # line:8
    _inherit = 'res.config.settings'  # line:10

    def _gcurl(OO00OOOOOOO0O0O0O):  # line:12
        O00OO0OO00OOOO00O = OO00OOOOOOO0O0O0O.env['ir.config_parameter'].sudo().get_param('web.base.url')  # line:13
        OO00OOOOOOO0O0O0O.env['ir.config_parameter'].set_param('tableau_direct_connecter.url',
                                                               O00OO0OO00OOOO00O + '/tableau/connecter/')  # line:14
        return O00OO0OO00OOOO00O + '/tableau/connecter/'  # line:15

    url = fields.Char(string='Connecter Url', default=_gcurl)  # line:17
    access_token = fields.Char(string='Access Token' , default=(' '*40))  # line:18

    def set_values(O0O000O0OO0O0OO0O):  # line:20
        OOOOO00O0O0O00000 = super(WebConnecterSetting, O0O000O0OO0O0OO0O).set_values()  # line:21
        O0O000O0OO0O0OO0O.env['ir.config_parameter'].set_param('tableau_direct_connecter.url',
                                                               O0O000O0OO0O0OO0O.url)  # line:22
        O0O000O0OO0O0OO0O.env['ir.config_parameter'].set_param('tableau_direct_connecter.access_token',
                                                               O0O000O0OO0O0OO0O.access_token)  # line:23
        return OOOOO00O0O0O00000  # line:25

    @api.model  # line:27
    def get_values(OO00OO0O0O0O0OOOO):  # line:28
        O00OOO00000000O00 = super(WebConnecterSetting, OO00OO0O0O0O0OOOO).get_values()  # line:30
        OO00O000OO0OOOO00 = OO00OO0O0O0O0OOOO.env['ir.config_parameter'].sudo()  # line:31
        OO00OOOO0O0OO00O0 = OO00O000OO0OOOO00.get_param('tableau_direct_connecter.url')  # line:32
        OO00OOO0OO00O000O = OO00O000OO0OOOO00.get_param('tableau_direct_connecter.access_token')  # line:33
        O00OOO00000000O00.update(url=OO00OOOO0O0OO00O0, access_token=OO00OOO0OO00O000O)  # line:37
        return O00OOO00000000O00  # line:39

    def nonce(O0000OO00O0000O0O, length=40, prefix=""):  # line:41
        O0O000OOO00000000 = os.urandom(length)  # line:42
        return "{}_{}".format(prefix, str(hashlib.sha1(O0O000OOO00000000).hexdigest()))  # line:43

    def gtkn(O00O0O0O0000OO00O):  # line:45
        O00O0O0O0000OO00O.env['ir.config_parameter'].set_param('tableau_direct_connecter.access_token',
                                                               O00O0O0O0000OO00O.nonce())  # line:46
