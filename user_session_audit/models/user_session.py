from odoo import models, fields, api
from datetime import datetime

class UserSession(models.Model):
    _name = 'user.session.audit'
    _description = 'User Session Audit'
    _order = 'login_date desc'

    user_id = fields.Many2one('res.users', string='User', required=True, index=True)
    login_date = fields.Datetime(string='Login Date', default=fields.Datetime.now)
    logout_date = fields.Datetime(string='Logout Date')
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string="User Agent")
    user_type = fields.Selection([
        ('registry', 'Pensioner Registry'),
        ('portal', 'Registration Portal')
    ], string="User Type")
    session_id = fields.Char(string='Session ID', index=True)

    @api.depends('login_date', 'logout_date')
    def _compute_duration(self):
        for record in self:
            if record.login_date and record.logout_date:
                diff = record.logout_date - record.login_date
                record.duration = diff.total_seconds() / 3600.0
            else:
                record.duration = 0.0

    @api.model
    def close_session(self, user_id, session_id):
        """ Close any open sessions for this user and session ID """
        # 1. Try exact match first
        open_sessions = self.sudo().search([
            ('user_id', '=', user_id),
            ('session_id', '=', session_id),
            ('logout_date', '=', False)
        ], limit=1)
        
        # 2. Fallback: Most recent open session for this user (handles SID rotation)
        if not open_sessions:
            open_sessions = self.sudo().search([
                ('user_id', '=', user_id),
                ('logout_date', '=', False)
            ], order='login_date desc', limit=1)
            
        if open_sessions:
            open_sessions.write({
                'logout_date': fields.Datetime.now(),
                'session_id': session_id, # Update with the latest session ID seen at logout
            })
            return True
        return False
