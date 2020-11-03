# -*- coding: utf-8 -*-
from odoo import models, fields, api, _



class AccountMove(models.Model):
    _inherit= 'account.move'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        print('============================================')
        if self.env.user.has_group('bista_account.group_own_customer'):
            print('============dddddddddddd================================')
            args += [('partner_id.user_id','=', self.env.user.id)]
        return super(AccountMove, self).search(args,offset,limit,order,count)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('bista_account.group_own_customer'):
            args += [('partner_id.user_id', '=', self.env.user.id)]
        return super(AccountMove, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)