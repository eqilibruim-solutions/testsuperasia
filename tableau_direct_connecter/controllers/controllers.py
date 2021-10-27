# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request,Response
from itertools import groupby
from odoo.tools import date_utils
import json
from odoo.addons.tableau_direct_connecter.controllers.validate_token import validate_token,validate_license
from odoo.addons.tableau_direct_connecter.common import datefields_extracter





class TableauConnecter(http.Controller):

    @http.route('/tableau/connecter/', type='http', auth="none", website=True, csrf=False)
    def connecter_page(self, **kw):

        return request.render('tableau_direct_connecter.web_connecter_tableau', {})

    @validate_license
    @validate_token
    @http.route('/schemas/', type='http', auth="none",methods=['GET','OPTIONS'],csrf=False,cors='*')
    def get_schema(self, **kwargs):

        key_func = lambda v: v['table_name']
        res = dict()
        big_tables = []
        try:
            with http.request.env.cr.savepoint():
                schemas = request.env.cr.execute(f'''
                                                    SELECT 
                                                    column_name,data_type AS column_type,table_name 
                                                    FROM 
                                                    information_schema.columns 
                                                    WHERE 
                                                    table_schema = 'public' 
                                                    ORDER BY table_name
                                                    ''')
                schemas = request.env.cr.dictfetchall()
               
                for key, value in groupby(schemas, key_func):
                    value = list(value)
                    res[key] = value
                    request.env.cr.execute(f''' SELECT COUNT(*) FROM {key}''')
                    count = request.env.cr.dictfetchall()[0]['count']
                    if count > 20000:
                        big_tables.append({'table':key,'size':count})
        except Exception as e:
            return Response(
                        json.dumps({'error':f'{e}'},default=date_utils.json_default),
                        content_type='application/json',
                        status= 500
                        )



        return Response(
                        json.dumps({'schema':res,'metadata':big_tables,'dbname':request.env.cr.dbname},default=date_utils.json_default),
                        content_type='application/json',
                        status=200
                        )
    @validate_license
    @validate_token
    @http.route('/model/<string:model>/', type='http', auth="none",methods=['GET','OPTIONS'],website=True, csrf=False,cors='*')
    def get_model(self,model,**kwargs):

        status = 200
        last_id = kwargs.get('last_id',0)
        limit = kwargs.get('limit',20000)
        try:
            with http.request.env.cr.savepoint():
                values = request.env.cr.execute(f'''SELECT * 
                                                    FROM 
                                                    {model} 
                                                    WHERE id > {int(last_id)} 
                                                    ORDER BY id
                                                    LIMIT {int(limit)}
                                                ''')
                values = request.env.cr.dictfetchall()
        except Exception as e:
            values = {'error':str(e)}
            status = 404
        return Response(json.dumps(values,default=date_utils.json_default),content_type='application/json',status=status)



    @http.route('/get/count/<string:model>/', type='http', auth="none",methods=['GET','OPTIONS'],website=True, csrf=False,cors='*')
    def get_count(self,model,**kwargs):
        values = {}
        try:
            with http.request.env.cr.savepoint():
                request.env.cr.execute(f''' SELECT COUNT(*) FROM {model}''')
                by_select_query = request.env.cr.dictfetchall()[0]['count']
                request.env.cr.execute(f'''
                                                            SELECT 
                                                            n_live_tup AS count 
                                                            FROM 
                                                            pg_stat_user_tables 
                                                            WHERE 
                                                            relname = '{model}'
                                                            ''')
                by_meta_query = request.env.cr.dictfetchall()[0]['count']
                values = {'by_count(*)':by_select_query,'by_meta_table':by_meta_query}
        except Exception as e:
            values = {'error':str(e)}
            status = 500
        return Response(json.dumps(values),content_type='application/json',status=200)




