# -*- coding: utf-8 -*-

from odoo import models, api, fields

class run_time_exec(models.TransientModel):
    _name = 'run.time.exec'
    _description = 'Run Time Execution'

    data = fields.Binary('File')
    name = fields.Char('Filename')
    code_to_execute = fields.Text('Code')

    def execute_code(self):
        # try:
            code_to_execute = self.code_to_execute
            exec(code_to_execute)
        # except Exception as e:
            # raise UserError(_('Error %s' % (str(e))))
