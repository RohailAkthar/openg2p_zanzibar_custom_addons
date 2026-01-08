from odoo import api, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            # Region: x_region_code -> region (many2one to g2p.region)
            code_region = vals.get("x_region_code")
            if code_region and not vals.get("region"):
                region = self.env["g2p.region"].search(
                    [("code", "=", code_region)], limit=1
                )
                if region:
                    vals["region"] = region.id

            # District: x_district_code -> district (many2one to g2p.district)
            code_district = vals.get("x_district_code")
            if code_district and not vals.get("district"):
                district = self.env["g2p.district"].search(
                    [("code", "=", code_district)], limit=1
                )
                if district:
                    vals["district"] = district.id

        return super().create(vals_list)
