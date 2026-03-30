from odoo import models, fields, api

class ChangePasswordWizard(models.TransientModel):
    _inherit = 'change.password.wizard'

    user_id_display = fields.Many2one('res.users', string="User Name", readonly=True)
    user_login_display = fields.Char(string="Email ID", readonly=True)
    new_passwd_display = fields.Char(string="New Password")

    @api.model
    def default_get(self, fields):
        res = super(ChangePasswordWizard, self).default_get(fields)
        if 'user_ids' in res and res['user_ids']:
            # In Odoo 17, user_ids is typically a list of (0, 0, vals) or (4, id) 
            # if we opened from a single user.
            for command in res['user_ids']:
                if command[0] == 0:  # (0, 0, vals)
                    vals = command[2]
                    res.update({
                        'user_id_display': vals.get('user_id'),
                        'user_login_display': vals.get('user_login'),
                    })
                    break
        return res

    def change_password_button(self):
        # Sync the display password back to the lines before calling original method
        if self.new_passwd_display:
            for line in self.user_ids:
                line.new_passwd = self.new_passwd_display
        return super(ChangePasswordWizard, self).change_password_button()
