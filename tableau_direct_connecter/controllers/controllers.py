from odoo import http #line:2
from odoo .http import request ,Response #line:3
from itertools import groupby #line:4
from odoo .tools import date_utils #line:5
import json #line:6
from odoo .addons .tableau_direct_connecter .controllers .validate_token import validate_token #line:7
from odoo .addons .tableau_direct_connecter .common import datefields_extracter #line:8
def calculate_rows (OOO0000OO0O0OOOO0 ,OO000OOO00O0O0O0O ):#line:10
    for O000OO0OO0OOOOOO0 ,O0000OOOOO00O000O in enumerate (OO000OOO00O0O0O0O ):#line:11
        OOO0000OO0O0OOOO0 .env .cr .execute (f''' SELECT COUNT(*) FROM {O0000OOOOO00O000O['table']}''')#line:12
        OOO0OO00OOO0O0OO0 =OOO0000OO0O0OOOO0 .env .cr .dictfetchall ()[0 ]['count']#line:13
        if OOO0OO00OOO0O0OO0 >20000 :#line:14
            O0000OOOOO00O000O ['size']=OOO0OO00OOO0O0OO0 #line:15
        else :#line:16
            del OO000OOO00O0O0O0O [O000OO0OO0OOOOOO0 ]#line:17
    return OO000OOO00O0O0O0O #line:18
class TableauConnecter (http .Controller ):#line:21
    @http .route ('/tableau/connecter/',type ='http',auth ="none",website =True ,csrf =False )#line:23
    def connecter_page (O0O0O00OO00OOOOOO ,**O000OOOO000O00OO0 ):#line:24
        return request .render ('tableau_direct_connecter.web_connecter_tableau',{})#line:26
    @validate_token #line:29
    @http .route ('/schemas/',type ='http',auth ="none",methods =['GET','OPTIONS'],csrf =False ,cors ='*')#line:30
    def get_schema (O0000OO0O000OO0O0 ,**OO0OO00OO0OO00000 ):#line:31
        O0O0OO0O0OOOO0000 =lambda OO0OOOO0O000O00O0 :OO0OOOO0O000O00O0 ['table_name']#line:33
        O000O0OO0O0O00OOO =dict ()#line:34
        try :#line:36
            with http .request .env .cr .savepoint ():#line:37
                OO0OOO00OOO00OOOO =request .env .cr .execute (f'''
                                                    SELECT 
                                                    column_name,data_type AS column_type,table_name 
                                                    FROM 
                                                    information_schema.columns 
                                                    WHERE 
                                                    table_schema = 'public' 
                                                    ORDER BY table_name
                                                    ''')#line:46
                OO0OOO00OOO00OOOO =request .env .cr .dictfetchall ()#line:47
                OOOOOO00O0O0OOOOO =request .env .cr .execute ('''
                                                    SELECT 
                                                    relname AS table ,n_live_tup AS size 
                                                    FROM 
                                                    pg_stat_user_tables 
                                                    WHERE n_live_tup > 15000 
                                                    ORDER BY relname
                                                    ''')#line:55
                OOOOOO00O0O0OOOOO =request .env .cr .dictfetchall ()#line:56
                OOOOOO00O0O0OOOOO =calculate_rows (request ,OOOOOO00O0O0OOOOO )#line:57
                for O0000OOOOO00OO0OO ,O0000O00O00OO0OOO in groupby (OO0OOO00OOO00OOOO ,O0O0OO0O0OOOO0000 ):#line:58
                    O0000O00O00OO0OOO =list (O0000O00O00OO0OOO )#line:59
                    O000O0OO0O0O00OOO [O0000OOOOO00OO0OO ]=O0000O00O00OO0OOO #line:60
        except Exception as OO000OO0O00000OO0 :#line:61
            return Response (json .dumps ({'error':f'{OO000OO0O00000OO0}'},default =date_utils .json_default ),content_type ='application/json',status =500 )#line:66
        return Response (json .dumps ({'schema':O000O0OO0O0O00OOO ,'metadata':OOOOOO00O0O0OOOOO ,'dbname':request .env .cr .dbname },default =date_utils .json_default ),content_type ='application/json',status =200 )#line:74
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





