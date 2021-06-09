from odoo import fields, models, api
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class InheritProductionLot(models.Model):
    _inherit = "stock.production.lot"

    active = fields.Boolean(string="Active",
                            help="Check to make the lot active.",
                            default=True)

    def archive_production_lot(self):
        today_date = datetime.today()
        today_100_days = today_date - timedelta(days=100)
        # Get the Production Lots older than 100 days from current date
        prod_lots = self.env['stock.production.lot'].search([('create_date', '<=', today_100_days.strftime("%Y-%m-%d"))])
        for prod_lot in prod_lots:
            # Set current Production Lot active to False if qty is 0
            if prod_lot.product_qty <= 0:
                prod_lot.active = False

        # stock_quants = self.env['stock.quant'].search(['&', ('lot_id', 'in', prod_lots.ids), ('quantity', '>=', 0)])
        # print(stock_quants)

        _logger.info("Production Lot Archiving Conditionally")
