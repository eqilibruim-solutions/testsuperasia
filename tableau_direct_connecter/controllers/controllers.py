from odoo import http  # line:2
from odoo.http import request, Response  # line:3
from itertools import groupby  # line:4
from odoo.tools import date_utils  # line:5
import json  # line:6
from odoo.addons.tableau_direct_connecter.controllers.validate_token import validate_token  # line:7
from odoo.addons.tableau_direct_connecter.common import datefields_extracter  # line:8

class TableauConnecter(http.Controller):  # line:11
    @http.route('/tableau/connecter/', type='http', auth="none", website=True, csrf=False)  # line:13
    def cp(OO0O00OO000O0OOOO, **OOO0O00OOOOO0OO00):  # line:14
        return request.render('tableau_direct_connecter.web_connecter_tableau', {})  # line:16

    @validate_token  # line:19
    @http.route('/schemas/', type='http', auth="none", methods=['GET', 'OPTIONS'], csrf=False, cors='*')  # line:20
    def gs(OO00OO00O00O00O0O, **OO0O0OOO0OO0000OO):  # line:21
        OOO0O00O000OO0OOO = lambda O00OOOOO0O000O0OO: O00OOOOO0O000O0OO['table_name']  # line:23
        O0O000OO0O0OOO0O0 = dict()  # line:24
        try:  # line:26
            with http.request.env.cr.savepoint():  # line:27
                O0O0O00000OO0O0OO = request.env.cr.execute(f'''
                                                    SELECT 
                                                    column_name,data_type AS column_type,table_name 
                                                    FROM 
                                                    information_schema.columns 
                                                    WHERE 
                                                    table_schema = 'public' 
                                                    ORDER BY table_name
                                                    ''')  # line:36
                O0O0O00000OO0O0OO = request.env.cr.dictfetchall()  # line:37
                OOO0000O00O000000 = request.env.cr.execute('''SELECT 
                                                    relname AS table ,n_live_tup AS size 
                                                    FROM 
                                                    pg_stat_user_tables 
                                                    WHERE n_live_tup > 20000 
                                                    ORDER BY relname
                                                    ''')  # line:44
                OOO0000O00O000000 = request.env.cr.dictfetchall()  # line:45
                for OOOO000000OO0OO00, OOO0O0OOOOO0OO0OO in groupby(O0O0O00000OO0O0OO, OOO0O00O000OO0OOO):  # line:46
                    OOO0O0OOOOO0OO0OO = list(OOO0O0OOOOO0OO0OO)  # line:47
                    O0O000OO0O0OOO0O0[OOOO000000OO0OO00] = OOO0O0OOOOO0OO0OO  # line:48
        except Exception as O0O0000000000OOOO:  # line:49
            return Response(json.dumps({'error': f'{O0O0000000000OOOO}'}, default=date_utils.json_default),
                            content_type='application/json', status=500)  # line:54
        return Response(
            json.dumps({'schema': O0O000OO0O0OOO0O0, 'metadata': OOO0000O00O000000, 'dbname': request.env.cr.dbname},
                       default=date_utils.json_default), content_type='application/json', status=200)  # line:62

    @validate_token
    @http.route('/model/<string:model>/', type='http', auth="none", methods=['GET', 'OPTIONS'], website=True,
                csrf=False, cors='*')
    def get_model(self, model, **kwargs):
        status = 200
        if kwargs.get('from', None) and kwargs.get('to', None):
            frm, to = int(kwargs.get('from')), int(kwargs.get('to'))
            try:
                with http.request.env.cr.savepoint():
                    values = request.env.cr.execute(f'''SELECT * 
                                                        FROM 
                                                        {model} 
                                                        WHERE id >={frm} AND id <= {to} 
                                                        ORDER BY id '''
                                                    )
                    values = request.env.cr.dictfetchall()
            except Exception as e:
                values = {'error': f"{model} not found in your Database"}
                status = 404
            return Response(json.dumps(values, default=date_utils.json_default), content_type='application/json',
                            status=status)

        limit = kwargs.get('limit') if kwargs.get('limit', None) else 20000
        try:
            with http.request.env.cr.savepoint():
                values = request.env.cr.execute(f'''SELECT * 
                                                    FROM 
                                                    {model}
                                                    LIMIT 
                                                    {int(limit)}
                                                    ''')
                values = request.env.cr.dictfetchall()
        except Exception as e:
            values = {'error': f"{model} not found in your Database"}
            status = 404
        return Response(json.dumps(values, default=date_utils.json_default), content_type='application/json',
                        status=status)