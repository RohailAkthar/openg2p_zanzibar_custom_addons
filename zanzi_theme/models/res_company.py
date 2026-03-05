from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # ----------------------------------------------------------
    # Fields
    # ----------------------------------------------------------

    favicon = fields.Binary(string="Company Favicon", attachment=True)

    background_image = fields.Binary(string="Apps Menu Background Image", attachment=True)
    banner_background_image = fields.Binary(string="Banner Background Image", attachment=True)
