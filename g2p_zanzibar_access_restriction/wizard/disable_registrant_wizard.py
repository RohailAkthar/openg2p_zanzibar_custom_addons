from odoo import models, fields, api

class G2PDisableRegistryWiz(models.TransientModel):
    _inherit = "g2p.disable.registrant.wizard"

    def disable_registrant(self):
        """Automatically archive the record when disabled."""
        res = super().disable_registrant()
        for rec in self:
            if rec.partner_id:
                rec.partner_id.write({"active": False})
        return res
