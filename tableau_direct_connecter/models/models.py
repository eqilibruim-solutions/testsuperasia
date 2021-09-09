import hashlib #line:2
import logging #line:3
import os #line:4
from odoo import models ,fields ,api #line:5
from ast import literal_eval #line:6
class WebConnecterSetting (models .TransientModel ):#line:9
    _inherit ='res.config.settings'#line:10
    def _get_connecter_url (OO0OO0O00OOOO00O0 ):#line:12
        OO00000O000OOO0O0 =OO0OO0O00OOOO00O0 .env ['ir.config_parameter'].sudo ().get_param ('web.base.url')#line:13
        OO0OO0O00OOOO00O0 .env ['ir.config_parameter'].set_param ('tableau_direct_connecter.url',OO00000O000OOO0O0 +'/tableau/connecter/')#line:14
        return OO00000O000OOO0O0 +'/tableau/connecter/'#line:15
    url =fields .Char (string ='Connecter Url',default =_get_connecter_url )#line:17
    access_token =fields .Char (string ='Access Token',default ="*******************************************" )#line:18
    def set_values (O0OO0OO000OO000O0 ):#line:20
        O0O00OO00O0OOO00O =super (WebConnecterSetting ,O0OO0OO000OO000O0 ).set_values ()#line:21
        O0OO0OO000OO000O0 .env ['ir.config_parameter'].set_param ('tableau_direct_connecter.url',O0OO0OO000OO000O0 .url )#line:22
        O0OO0OO000OO000O0 .env ['ir.config_parameter'].set_param ('tableau_direct_connecter.access_token',O0OO0OO000OO000O0 .access_token )#line:23
        return O0O00OO00O0OOO00O #line:25
    @api .model #line:27
    def get_values (O0OOOOOOO0O00OO0O ):#line:28
        OO0O0O0OOOOOOOOOO =super (WebConnecterSetting ,O0OOOOOOO0O00OO0O ).get_values ()#line:29
        OOOO0O0O0O0O0OO0O =O0OOOOOOO0O00OO0O .env ['ir.config_parameter'].sudo ()#line:30
        OO0O0O000O0O00O00 =OOOO0O0O0O0O0OO0O .get_param ('tableau_direct_connecter.url')#line:31
        O0000O00OO000O00O =OOOO0O0O0O0O0OO0O .get_param ('tableau_direct_connecter.access_token')#line:32
        OO0O0O0OOOOOOOOOO .update (url =OO0O0O000O0O00O00 ,access_token =O0000O00OO000O00O )#line:36
        return OO0O0O0OOOOOOOOOO #line:38
    def nonce (O00OOO0OO00OOO0O0 ,length =40 ,prefix =""):#line:40
        OOOOO00O0O00OO0O0 =os .urandom (length )#line:41
        return "{}_{}".format (prefix ,str (hashlib .sha1 (OOOOO00O0O00OO0O0 ).hexdigest ()))#line:42
    def generate_token (O00000O00OOO0O000 ):#line:44
        O00000O00OOO0O000 .env ['ir.config_parameter'].set_param ('tableau_direct_connecter.access_token',O00000O00OOO0O000 .nonce ())#line:45
