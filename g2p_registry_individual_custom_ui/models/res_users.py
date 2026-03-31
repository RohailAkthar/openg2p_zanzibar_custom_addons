from odoo import models, fields, api

class ChangePasswordWizard(models.TransientModel):
    _inherit = 'change.password.wizard'

    user_id_display = fields.Many2one('res.users', string='User', readonly=True)
    user_login_display = fields.Char(string='User Login', readonly=True)
    new_passwd_display = fields.Char(string='New Password')

    @api.model
    def default_get(self, fields):
        res = super(ChangePasswordWizard, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        if active_ids and len(active_ids) == 1:
            user = self.env['res.users'].browse(active_ids[0])
            res.update({
                'user_id_display': user.id,
                'user_login_display': user.login,
            })
        return res

    def change_password_button(self):
        # Sync the display password back to the lines before calling original method
        if self.new_passwd_display:
            for line in self.user_ids:
                line.new_passwd = self.new_passwd_display
        return super(ChangePasswordWizard, self).change_password_button()
