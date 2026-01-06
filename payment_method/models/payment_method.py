from odoo import models, fields, api

class ResPartnerRelatives(models.Model):
    _inherit = 'res.partner'

    payment_mode = fields.Selection(
    [
        ("bank", "Bank"),
        ("mobile_wallet", "Mobile Wallet"),
    ],
    string="Preferred Payment Method",
    )

    bank_name = fields.Char(string="Bank Name")
    account_num = fields.Char(string="Account Number")
    account_name = fields.Char(string="Account Name")

    mobile_wallet=fields.Char(string="Mobile Wallet")
