from odoo import models, fields, api, _
from odoo.http import request

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _update_last_login(self):
        super(ResUsers, self)._update_last_login()
        for user in self:
            # Skip public user noise
            if user.id == self.env.ref('base.public_user').id:
                continue
                
            # Detect user type
            user_type = 'registry'
            if user.has_group('base.group_portal') and not user.has_group('base.group_user'):
                user_type = 'portal'
            elif request and request.httprequest and ('/my/' in request.httprequest.path or '/portal' in request.httprequest.path):
                user_type = 'portal'

            # Create session audit record
            self.env['user.session.audit'].sudo().create({
                'user_id': user.id,
                'login_date': fields.Datetime.now(),
                'ip_address': request.httprequest.remote_addr if request else False,
                'user_agent': request.httprequest.user_agent.string if request else False,
                'session_id': request.session.sid if request else False,
                'user_type': user_type,
            })
        return True
