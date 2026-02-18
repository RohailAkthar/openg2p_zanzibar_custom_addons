from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    benf_post_code = fields.Char(string="Post Code")
    benf_zan_id = fields.Char(string="Zan ID", compute="_compute_benf_zan_id", readonly=True, store=True)
    disability = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Do you have any disability?"
    )
    is_receiving_allowance = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="Are you receiving 5000 allowance from district council? (Below 70 years)",
    )
    has_health_insurance = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="Are you covered with any health insurance scheme?",
    )
    @api.depends("reg_ids")
    def _compute_benf_zan_id(self):
        for record in self:
            val = False
            # Check if reg_ids exists (it should if module deps are correct)
            if hasattr(record, "reg_ids"):
                 # Look for Zanzibar ID
                 reg_id = record.reg_ids.filtered(lambda r: r.id_type.name == "Zanzibar ID")
                 if reg_id:
                     # Take the first one if multiple (though unique constraint usually prevents this)
                     val = reg_id[0].value
            record.benf_zan_id = val

    x_region_code=fields.Char("X_Reg")
    
    x_district_code=fields.Char("X_dist")
