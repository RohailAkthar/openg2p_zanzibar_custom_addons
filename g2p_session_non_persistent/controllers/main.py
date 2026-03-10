# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import http
from odoo.http import request


class SessionTabLogout(http.Controller):

    @http.route('/web/session/tab_logout/request', type='http', auth="none", csrf=False)
    def request_logout(self):
        """
        Request a session logout with a 5-second grace period (High Security).
        This is called when an Odoo tab is closed.
        """
        if request.session.uid:
            # Set logout time to 5 seconds from now to allow for quick refreshes
            request.session['tab_logout_at'] = time.time() + 1
        return "OK"

    @http.route('/web/session/tab_logout/cancel', type='http', auth="none", csrf=False)
    def cancel_logout(self):
        """
        Cancel a pending session logout.
        This is called when an Odoo tab is loaded/refreshed.
        """
        if 'tab_logout_at' in request.session:
            del request.session['tab_logout_at']
        return "OK"
