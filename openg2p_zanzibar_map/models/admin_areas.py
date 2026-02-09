from odoo import models, fields

class ZanzibbarProvince(models.Model):
    _inherit = 'g2p.region'
    _description = 'Province'

    name = fields.Char(string="Province Name", required=True)
    code = fields.Char(string="Capitol")


class ZanzibbarDistrict(models.Model):
    _inherit = 'g2p.district'
    _description = 'Zanzibar District'
    
    name = fields.Char(string="District Name", required=True)
    # Linking to the existing Region/Province table
    province_id = fields.Many2one('g2p.region', string="Province/Region", required=True)
    code = fields.Char(string="District Code")
