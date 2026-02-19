from odoo import models, fields, api

class ResPartnerRelatives(models.Model):
    _inherit = 'res.partner'

    def _get_nominee_gender_dynamic_selection(self):
        options = self.env["gender.type"].search([])
        return [(option.value, option.code) for option in options]

    # Your existing fields...
    nominee_first_name = fields.Char("First Name")
    nominee_middle_name = fields.Char("Middle Name")
    nominee_last_name = fields.Char("Surname")
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
    
    beneficiary_phone_number_ids = fields.One2many(
        "g2p.phone.number",
        "partner_id",
        string="Beneficiary Phone Numbers",
        domain=['|', ("phone_owner", "=", "beneficiary"), ("phone_owner", "=", False)]
    )

    nominee_phone_number_ids = fields.One2many(
        "g2p.phone.number",
        "partner_id",
        string="Nominee Phone Numbers",
        domain=[("phone_owner", "=", "nominee")]
    )

    @api.onchange("nominee_mobile")
    def _onchange_nominee_mobile(self):
        if self.nominee_mobile:
            # Check if number already exists to avoid duplicates
            existing = self.nominee_phone_number_ids.filtered(lambda p: p.phone_no == self.nominee_mobile)
            if not existing:
                self.nominee_phone_number_ids = [fields.Command.create({
                    'phone_no': self.nominee_mobile,
                    'phone_owner': 'nominee',
                })]

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            if partner.nominee_mobile:
                partner._sync_nominee_phone(partner.nominee_mobile)
        return partners

    def write(self, vals):
        res = super().write(vals)
        if 'nominee_mobile' in vals:
            for partner in self:
                partner._sync_nominee_phone(partner.nominee_mobile)
        return res

    def _sync_nominee_phone(self, mobile):
        if not mobile:
            return
            
        # Get active nominee numbers
        active_phones = self.phone_number_ids.filtered(
            lambda p: p.phone_owner == 'nominee' and not p.disabled
        )
        
        exists_active = False
        for phone in active_phones:
            if phone.phone_no == mobile:
                exists_active = True
            else:
                # Disable old active number
                phone.write({
                    'disabled': fields.Datetime.now(),
                    'disabled_by': self.env.user.id
                })
        
        if not exists_active:
             self.env['g2p.phone.number'].create({
                 'partner_id': self.id,
                 'phone_no': mobile,
                 'phone_owner': 'nominee',
                 'country_id': self.env.ref('base.tz').id
             })

    @api.depends("reg_ids.value", "reg_ids.id_type")
    def _compute_nominee_zanid(self):
        for record in self:
            val = False
            # Check if reg_ids exists
            if record.reg_ids:
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
   