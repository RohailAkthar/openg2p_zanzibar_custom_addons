from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type="form", **options):
        """Include G2P Super Admin group membership in view cache key so views are cached separately."""
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + (self.env.user.has_group("g2p_zanzibar_access_restriction.group_g2p_super_admin"),)

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        """Enforce read-only mode on Individual Registrant views for users who are not G2P Super Admins."""
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        if view_type in ("form", "tree"):
            indiv_form = self.env.ref("g2p_registry_individual.view_individuals_form", raise_if_not_found=False)
            indiv_tree = self.env.ref("g2p_registry_individual.view_individuals_list_tree", raise_if_not_found=False)
            is_indiv = (
                (indiv_form and view and view.id == indiv_form.id)
                or (indiv_tree and view and view.id == indiv_tree.id)
                or arch.attrib.get("string") == "Individual Registrant"
                or self._context.get("registrant_form")
            )
            if is_indiv and not self.env.user.has_group("g2p_zanzibar_access_restriction.group_g2p_super_admin"):
                arch.attrib["edit"] = "0"
                arch.attrib["create"] = "0"
        return arch, view

    def write(self, vals):
        """Restrict modifying individual registrant records in backend to G2P Super Admins only."""
        if not self.env.su and not self.env.user.has_group("g2p_zanzibar_access_restriction.group_g2p_super_admin"):
            if any(rec.is_registrant for rec in self):
                # Allow chatter, tracking, activities, and internal mail operations
                allowed_fields = {
                    "message_follower_ids",
                    "activity_ids",
                    "message_ids",
                    "message_main_attachment_id",
                }
                if any(field not in allowed_fields for field in vals):
                    raise UserError(_("Only users with the G2P Super Admin role can edit records in the Individual Registry."))
        return super().write(vals)

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
