# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class AccountReceivableReport(models.Model):
    _name = 'account.receivable.report'
    _rec_name = 'partner_id'
    _description = 'Account Receivable Report'

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True)
    salesperson = fields.Many2one('res.users',string='Salesperson', readonly=True)
    source_document = fields.Char(string='Source Document', readonly=True)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Term', readonly=True)
    account_move_id = fields.Many2one(
        'account.move', string='Journal Entry', readonly=True)
    accounting_date = fields.Date(string='Accounting Date', readonly=True)
    bill_date = fields.Date(string='Invoice Date', readonly=True)
    date_maturity = fields.Date(string='Due Date', readonly=True)
    bucket_current = fields.Monetary(string='Current', readonly=True)
    bucket_postdate = fields.Monetary(string='Post Date', readonly=True)
    bucket_30 = fields.Monetary(string='1-30 Days', readonly=True)
    bucket_60 = fields.Monetary(string='31-60 Days', readonly=True)
    bucket_90 = fields.Monetary(string='61-90 Days', readonly=True)
    bucket_120 = fields.Monetary(string='91-120 Days', readonly=True)
    bucket_150 = fields.Monetary(string='121-150 Days', readonly=True)
    bucket_180 = fields.Monetary(string='151-180 Days', readonly=True)
    bucket_180_plus = fields.Monetary(string='Plus 180 Days', readonly=True)
    balance = fields.Monetary(string='Total', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)
    currency_id = fields.Many2one(
        related="company_id.currency_id", string="Currency", readonly=True)

    @api.model
    def create_update_customer_aging(self):
        self._cr.execute("delete from account_receivable_report")
        customer_query = """
            insert into account_receivable_report (
                        create_date, create_uid, write_date, write_uid,
                        partner_id, salesperson, account_move_id,
                        source_document, payment_term_id,
                        accounting_date, bill_date, date_maturity,
                        bucket_postdate,bucket_current, bucket_30, bucket_60, bucket_90, bucket_120, bucket_150, bucket_180, bucket_180_plus,
                        balance, company_id)
            select now(), 1, now(), 1, partner_id, salesperson, account_move_id,
            source_document, payment_term_id, accounting_date, bill_date, date_maturity,
            bucket_postdate,bucket_current, bucket_30, bucket_60, bucket_90, bucket_120, bucket_150, bucket_180, bucket_180_plus, balance, company_id
            from (
                  WITH aged AS (
                        select
                        partner_id, salesperson, account_move_id,
                        source_document, payment_term_id,
                        accounting_date, bill_date, date_maturity, company_id,
                        bucket_postdate,bucket_current, bucket_30, bucket_60, bucket_90, bucket_120, bucket_150, bucket_180, bucket_180_plus, amt as balance
                              from (
                                    select
                                    partner_id, salesperson, account_move_id,
                                    source_document, payment_term_id,
                                    accounting_date, bill_date, date_maturity,
                                    amt as amt,
                                    company_id,
                                    case when
                                    bill_date > aged_date
                                    then amt else 0 end bucket_postdate,
                                    case when
                                    date_maturity >= aged_date
                                    then amt else 0 end bucket_current,
                                    case when
                                    (date_maturity < aged_date) and
                                    (date_maturity >= (aged_date - interval '30 days'))
                                    then amt else 0 end bucket_30,
                                    case when
                                    (date_maturity < (aged_date - interval '30 days')) and
                                    (date_maturity >= (aged_date - interval '60 days'))
                                    then amt else 0 end bucket_60,
                                    case when
                                    (date_maturity < (aged_date - interval '60 days')) and
                                    (date_maturity >= (aged_date - interval '90 days'))
                                    then amt else 0 end bucket_90,
                                    case when
                                    (date_maturity < (aged_date - interval '90 days')) and
                                    (date_maturity >= (aged_date - interval '120 days'))
                                    then amt else 0 end bucket_120,
                                    case when
                                    (date_maturity < (aged_date - interval '120 days')) and
                                    (date_maturity >= (aged_date - interval '150 days'))
                                    then amt else 0 end bucket_150,
                                    case when
                                    (date_maturity < (aged_date - interval '150 days')) and
                                    (date_maturity >= (aged_date - interval '180 days'))
                                    then amt else 0 end bucket_180,
                                    case when
                                    (date_maturity < (aged_date - interval '180 days'))
                                    then amt else 0 end bucket_180_plus
                                          from (
                                                select
                                                coalesce(aml_res.id) as partner_id,
                                                coalesce(user_id.id) as salesperson,
                                                coalesce(am.id) as account_move_id,
                                                coalesce(am.ref) as source_document,
                                                apt.id as payment_term_id,
                                                (aml.balance - COALESCE((select sum(amount) from account_partial_reconcile where debit_move_id=aml.id and max_date <= (now() at time zone 'UTC')::date),0)
                                                + COALESCE((select sum(amount) from account_partial_reconcile where credit_move_id=aml.id and max_date <= (now() at time zone 'UTC')::date),0)) as amt,
                                                (now() at time zone 'UTC')::date as aged_date,
                                                (now() at time zone 'UTC')::date - aml.date_maturity::date as diff_date,
                                                am.invoice_date::date as bill_date, aml.date_maturity::date as date_maturity,
                                                coalesce(am.date, aml.date) as accounting_date,
                                                am.company_id as company_id
                                                from account_move_line aml
                                                left join account_move am on aml.move_id = am.id
                                                left join account_payment ap on aml.payment_id = ap.id
                                                left join res_partner aml_res on aml.partner_id = aml_res.id
                                                left join res_users user_id on am.invoice_user_id = user_id.id
                                                left join account_account acc on aml.account_id = acc.id
                                                left join account_account_type acctype on acc.user_type_id = acctype.id
                                                left join account_payment_term apt on am.invoice_payment_term_id = apt.id
                                                where acc.internal_type in ('receivable')
                                                and aml.partner_id is not null
                                                and aml.balance <> 0
                                                and am.state = 'posted'
                                                ) as record
                                          where record.amt <> 0
                                          order by record.partner_id
            ) as result order by partner_id
            )
            select
            aged.partner_id,
            aged.salesperson,
            aged.account_move_id,
            aged.source_document,
            aged.payment_term_id,
            aged.accounting_date,
            aged.bill_date,
            aged.date_maturity,
            aged.company_id,
            aged.bucket_postdate,aged.bucket_current, aged.bucket_30, aged.bucket_60,
            aged.bucket_90, aged.bucket_120, aged.bucket_150, aged.bucket_180, aged.bucket_180_plus, aged.balance
            from aged
            order by aged.partner_id ) as output
    """
        self._cr.execute(customer_query)
        action = self.env.ref('aged_receivable_report.action_account_receivable_aging', False)
        action.sudo().context = {'search_default_company_id': self.env.user.company_id.id}
        action_data = None
        if action:
            action_data = action.read()[0]
        return action_data
