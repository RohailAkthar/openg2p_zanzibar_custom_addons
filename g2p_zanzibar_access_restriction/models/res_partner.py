from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    def toggle_active(self):
        """Restrict archiving/unarchiving to Super Admins only and sync disabled status."""
        if not self.env.user.has_group("g2p_zanzibar_access_restriction.group_g2p_super_admin"):
            raise UserError(_("Only Super Admins can archive or unarchive records."))

        for record in self:
            if record.active:  # About to archive
                if not record.disabled:
                    record.write({
                        "disabled": fields.Datetime.now(),
                        "disabled_reason": _("Manually Archived"),
                        "disabled_by": self.env.user.id,
                    })
            else:  # About to unarchive
                if record.disabled:
                    record.write({
                        "disabled": None,
                        "disabled_reason": None,
                        "disabled_by": None,
                    })
        return super().toggle_active()

    def enable_registrant(self):
        """Automatically unarchive the record when enabled."""
        res = super().enable_registrant()
        self.write({"active": True})
        return res
