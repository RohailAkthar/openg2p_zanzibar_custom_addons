from odoo import models


class RejectWizardInherit(models.TransientModel):
    _inherit = "reject.wizard"

    def confirm_rejection(self):
        """Override to also set rejected_by_user_id on the draft record."""
        active_ids = self._context.get("active_ids")
        self.ensure_one()
        record = self.env["draft.record"].browse(active_ids[0])

        record.with_context(mail_notrack=True).write(
            {
                "state": "rejected",
                "rejection_reason": self.rejection_reason,
                "rejected_by_user_id": self.env.user.id,
            }
        )

        record.message_post(body=f"Record rejected: {self.rejection_reason}")
        return {"type": "ir.actions.act_window_close"}
