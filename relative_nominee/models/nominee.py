from odoo import models, fields, api

class ResPartnerRelatives(models.Model):
    _inherit = 'res.partner'

    def _get_nominee_gender_dynamic_selection(self):
        options = self.env["gender.type"].search([])
        return [(option.value, option.code) for option in options]

    # Your existing fields...
    nominee_first_name = fields.Char("First Name")
    nominee_last_name = fields.Char("Last Name")
    nominee_gender = fields.Selection(selection=_get_nominee_gender_dynamic_selection)
    nominee_mobile = fields.Char("Mobile")
    nominee_zanid = fields.Char("ZanID", compute="_compute_nominee_zanid", readonly=True, store=True)
    nominee_rel_benf = fields.Selection(
    [
        ("wife", "Wife"),
        ("husband", "Husband"),
        ("son", "Son"),
        ("daughter", "Daughter"),
        ("grandchild", "Grandchild"),
        ("other", "Other"),
    ],
    string="Relationship with beneficiary",
    )

    nominee_house_street = fields.Char(string="House & Street")
    nominee_shehia = fields.Char(string="Shehia (Ward)")
    
        # REMOVED: nominee_region_code, nominee_district_code
    # NEW: Direct Selection fields
    nominee_region = fields.Selection(
        selection='_get_nominee_region_selection',
        string="Region"
    )
    nominee_district = fields.Selection(
        selection='_get_nominee_district_selection', 
        string="District"
    )

    nominee_post_code=fields.Char("PO BOX / Post code")

    @api.depends("reg_ids")
    def _compute_nominee_zanid(self):
        for record in self:
            val = False
            # Check if reg_ids exists
            if hasattr(record, "reg_ids"):
                 # Look for Nominee Zanzibar ID
                 reg_id = record.reg_ids.filtered(lambda r: r.id_type.name == "Nominee Zanzibar ID")
                 if reg_id:
                     val = reg_id[0].value
            record.nominee_zanid = val

    @api.model
    def _get_nominee_region_selection(self):
        """Dynamic region selection from g2p.region"""
        regions = self.env["g2p.region"].sudo().search([])
        return [(region.code, region.name) for region in regions]

    @api.model
    def _get_nominee_district_selection(self):
        """Dynamic district selection from g2p.district"""
        districts = self.env["g2p.district"].sudo().search([])
        return [(district.code, district.name) for district in districts]
   
