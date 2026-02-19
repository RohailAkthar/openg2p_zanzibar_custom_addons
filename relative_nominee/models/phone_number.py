from odoo import models, fields

class G2PPhoneNumber(models.Model):
    _inherit = "g2p.phone.number"

    phone_owner = fields.Selection(
        [("beneficiary", "Beneficiary"), ("nominee", "Nominee")],
        string="Phone Owner",
        default="beneficiary",
    )

    country_id = fields.Many2one(
        "res.country",
        "Country",
        default=lambda self: self.env.ref("base.tz", raise_if_not_found=False)
    )
