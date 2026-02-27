from odoo import models, fields, api

class ResPartnerRelatives(models.Model):
    _inherit = 'res.partner'

    payment_mode = fields.Selection(
    [
        ("bank", "Bank"),
        ("mobile_wallet", "Mobile Wallet"),
    ],
    string="Preferred Payment Method",
    tracking=True,
    )

    bank_name = fields.Char(string="Bank Name", tracking=True)
    account_num = fields.Char(string="Account Number", tracking=True)
    account_name = fields.Char(string="Account Name", tracking=True)

    mobile_wallet=fields.Char(string="Mobile Wallet", tracking=True)
