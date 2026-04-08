import logging
from odoo import http, fields
from odoo.http import request
from odoo.addons.web.controllers.session import Session

_logger = logging.getLogger(__name__)

class UserSessionAuditController(Session):

    def _close_audit_session(self):
        """ Helper to close the audit session record """
        if request.session and request.session.uid:
            user_id = request.session.uid
            session_id = request.session.sid
            _logger.info("User Session Audit: Attempting to close session for user %s (SID: %s)", user_id, session_id)
            try:
                # Use the helper method we added to the model
                # We use sudo() and a new environment if necessary, but request.env is usually fine
                closed = request.env['user.session.audit'].sudo().close_session(user_id, session_id)
                if closed:
                    _logger.info("User Session Audit: Successfully recorded logout for user %s", user_id)
                else:
                    _logger.warning("User Session Audit: Could not find any open record to close for user %s", user_id)
            except Exception as e:
                _logger.error("User Session Audit: Error closing session: %s", str(e))

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        self._close_audit_session()
        return super(UserSessionAuditController, self).logout(redirect=redirect)

    @http.route('/web/session/destroy', type='json', auth="user")
    def destroy(self):
        self._close_audit_session()
        return super(UserSessionAuditController, self).destroy()
