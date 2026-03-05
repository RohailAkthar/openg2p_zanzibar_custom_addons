from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # ----------------------------------------------------------
    # Fields
    # ----------------------------------------------------------

    appbar_image = fields.Binary(string="Apps Menu Footer Image", attachment=True)
