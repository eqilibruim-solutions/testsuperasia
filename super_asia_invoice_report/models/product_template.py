from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = 'product.template'

    def _get_default_length_uom(self):
        return self._get_length_uom_name_from_ir_config_parameter()

    logistic_length = fields.Float(string="Length", help="Logistic length")
    logistic_width = fields.Float(string="Width", help="Logistic width")
    logistic_height = fields.Float(string="Height", help="Logistic height")
    length_uom_name = fields.Char(string='Length unit of measure label', compute='_compute_length_uom_name',
                                  default=_get_default_length_uom)

    def _compute_length_uom_name(self):
        for template in self:
            template.length_uom_name = self._get_length_uom_name_from_ir_config_parameter()

    @api.model
    def _get_length_uom_name_from_ir_config_parameter(self):
        """ Get the unit of measure to interpret the `length` field. By default, we consider
        that lengths are expressed in cubic meters. Users can configure to express them in cubic feet
        by adding an ir.config_parameter record with "product.volume_in_cubic_feet" as key
        and "1" as value.
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        return "ft" if get_param('product.volume_in_cubic_feet') == '1' else "m"

    # Pallet Configuration
    pallet_no_of_cases = fields.Integer(string="Total no. of Cases", help="Total no. of Cases in a Pallet")
    pallet_no_of_layers = fields.Integer(string="Total no. of Layers", help="Total no. of Layers in a Pallet")
    pallet_boxes_per_layer = fields.Integer(string="Boxes Per Layer", help="Boxes Per Layer")