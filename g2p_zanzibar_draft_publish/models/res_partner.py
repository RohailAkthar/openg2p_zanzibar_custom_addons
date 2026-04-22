import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class G2PRespartnerIntegration(models.Model):
    _inherit = "res.partner"

    draft_record_id = fields.Many2one('draft.record', string='Original Draft Record', readonly=True, required=False)

    imported_record_state = fields.Selection(
        selection=[
            ("draft", "Not Verified"),
            ("submitted", "Submitted"),
            ("published", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        string="Status"
    )

    @api.model
    def cleanup_orphaned_published_partners(self):
        """Clean up published partners whose draft records were deleted"""
        # Find partners that reference draft records that no longer exist
        all_draft_ids = set(self.env['draft.record'].search([]).ids)
        orphaned_partners = self.search([
            ('is_registrant', '=', True),
            ('is_group', '=', False),
            ('db_import', '=', 'yes'),
            '|',
            ('draft_record_id', '=', False),
            ('draft_record_id', 'not in', list(all_draft_ids))
        ])
        
        # Mark orphaned partners as inactive so they don't appear in lists
        orphaned_partners.write({'active': False})
        return len(orphaned_partners)

    def action_save_to_draft(self, vals):
        # First call super to ensure standard fields are handled
        super().action_save_to_draft(vals)
        
        # Now handle Zanzibar specific fields
        context = self.env.context
        model_name = context.get("active_model")
        record_id = context.get("active_id")
        
        if model_name == "draft.record" and record_id:
            active_record = self.env[model_name].browse(record_id)
            
            try:
                partner_data = json.loads(active_record.partner_data or "{}")
            except (json.JSONDecodeError, TypeError):
                partner_data = {}
            
            # Sync Zanzibar fields from partner data to draft record fields
            sync_vals = {}
            if "benf_zan_id" in partner_data:
                sync_vals["zan_id"] = partner_data["benf_zan_id"]
            if "birthdate_date" in partner_data:
                sync_vals["birthdate_date"] = partner_data["birthdate_date"]
            if "registration_date" in partner_data:
                sync_vals["registration_date"] = partner_data["registration_date"]
            
            if sync_vals:
                active_record.write(sync_vals)

    def action_reject(self):
        """Open the reject wizard from the edit popup, targeting the active draft record."""
        context = self.env.context
        record_id = context.get("active_id")
        if not record_id:
            return
        return {
            "name": "Confirm Rejection",
            "type": "ir.actions.act_window",
            "res_model": "reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_ids": [record_id], "active_model": "draft.record"},
        }
