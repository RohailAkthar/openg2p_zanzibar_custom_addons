import time
import logging
from odoo import models, http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _auditlog_logout(self):
        """Helper to record logout in auditlog if available."""
        audit_session_id = request.session.get('auditlog_http_session_id')
        if audit_session_id:
            try:
                # We use a separate cursor or sudo to ensure it saves even if transaction fails
                request.env['auditlog.http.session'].sudo().browse(audit_session_id).write({
                    'logout_date': fields.Datetime.now()
                })
            except Exception:
                _logger.error("Failed to record auditlog logout")

    @classmethod
    def _authenticate(cls, endpoint):
        now = time.time()
        
        # 1. Check for Tab-Close Logout (Grace Period)
        tab_logout_at = request.session.get('tab_logout_at')
        if tab_logout_at:
            if now > tab_logout_at:
                _logger.info("G2P Session: Tab-close logout grace period expired. Logging out.")
                # RECORD TO AUDITLOG
                cls._auditlog_logout(cls)
                request.session.logout()
            else:
                if request.httprequest.path != '/web/session/tab_logout/cancel':
                    del request.session['tab_logout_at']

        # 2. Check for Inactivity Timeout (Server-Side)
        icp_sudo = request.env['ir.config_parameter'].sudo()
        max_inactivity = int(icp_sudo.get_param('sessions.max_inactivity_seconds', 0))
        
        if max_inactivity > 0 and request.session.uid:
            last_activity = request.session.get('last_activity')
            if last_activity and (now - last_activity) > max_inactivity:
                _logger.info("G2P Session: Inactivity timeout reached. Logging out.")
                # RECORD TO AUDITLOG
                cls._auditlog_logout(cls)
                request.session.logout()
            else:
                request.session['last_activity'] = now
        
        return super()._authenticate(endpoint)

    @classmethod
    def _post_dispatch(cls, response):
        super()._post_dispatch(response)
        if request.session.sid:
            # Full Security for Production (HTTPS)
            response.set_cookie(
                'session_id', 
                request.session.sid, 
                max_age=None, 
                expires=None, 
                httponly=True,
                secure=True,        # Enforce HTTPS
                samesite='Strict'   # Prevent CSRF and cross-site leaks
            )
