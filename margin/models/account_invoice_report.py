# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import tools
from odoo import models, fields, api

class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    margin_subtotal_signed = fields.Float('Margin')


    @api.model
    def _select(self):
        return '''
            SELECT
                line.id,
                line.move_id,
                line.product_id,
                line.account_id,
                line.analytic_account_id,
                line.journal_id,
                line.company_id,
                SUM(line.margin_subtotal_signed) AS margin_subtotal_signed,
                COALESCE(line.currency_id, line.company_currency_id)        AS currency_id,
                line.partner_id AS commercial_partner_id,
                move.name,
                move.state,
                move.type,
                move.partner_id,
                move.invoice_user_id,
                move.fiscal_position_id,
                move.invoice_payment_state,
                move.invoice_date,
                move.invoice_date_due,
                move.invoice_payment_term_id,
                move.invoice_partner_bank_id,
                move.amount_residual_signed                                 AS residual,
                move.amount_total_signed                                    AS amount_total,
                uom_template.id                                             AS product_uom_id,
                template.categ_id                                           AS product_categ_id,
                SUM(line.quantity / NULLIF(COALESCE(uom_line.factor, 1) * COALESCE(uom_template.factor, 1), 0.0))
                                                                            AS quantity,
                -SUM(line.balance)                                          AS price_subtotal,
                -SUM(line.balance / NULLIF(COALESCE(uom_line.factor, 1) * COALESCE(uom_template.factor, 1), 0.0))
                                                                            AS price_average,
                COALESCE(partner.country_id, commercial_partner.country_id) AS country_id,
                1                                                           AS nbr_lines
        '''

    
