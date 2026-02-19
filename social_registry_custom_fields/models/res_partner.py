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
    @api.depends("reg_ids.value", "reg_ids.id_type")
    def _compute_benf_zan_id(self):
        for record in self:
            val = False
            # Check for Zanzibar ID in reg_ids
            if record.reg_ids:
                zan_id_record = record.reg_ids.filtered(lambda r: r.id_type.name == "Zanzibar ID")
                if zan_id_record:
                    val = zan_id_record[0].value
            record.benf_zan_id = val

    x_region_code=fields.Char("X_Reg")
    
    x_district_code=fields.Char("X_dist")

    pensioner_id=fields.Char(string="Pensioner ID")
    middle_name = fields.Char(string="Middle Name", translate=False)

    @api.onchange("is_group", "family_name", "given_name", "middle_name", "addl_name")
    def name_change(self):
        vals = {}
        if not self.is_group:
            parts = [self.given_name, self.middle_name, self.family_name]
            # Filter None, False or empty strings
            parts = [p.strip() for p in parts if p and p.strip()]
            name = " ".join(parts)
            vals.update({"name": name.upper()})
            self.update(vals)
