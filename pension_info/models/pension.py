from odoo import models, fields, api

class ResPartnerRelatives(models.Model):
    _inherit = 'res.partner'

    other_pension = fields.Selection(
    [
        ("yes", "Yes"),
        ("no", "No"),
    ],
    string="Are you receiving any other pension?",
    )

    scheme_name = fields.Char(string="If Yes, which scheme")
    # account_num = fields.Char(string="Account Number")
    # account_name = fields.Char(string="Account Name")

    # mobile_wallet=fields.Char(string="Mobile Wallet")
