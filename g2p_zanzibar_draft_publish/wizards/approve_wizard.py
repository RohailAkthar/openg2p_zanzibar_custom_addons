from odoo import models, fields, api

class ApproveWizard(models.TransientModel):
    _name = "approve.wizard"
    _description = "Confirm Approval Wizard"

    def confirm_approval(self):
        self.ensure_one()
        active_ids = self._context.get("active_ids")
        records = self.env["draft.record"].browse(active_ids)
        for record in records:
            record.action_publish()
        return {"type": "ir.actions.act_window_close"}
