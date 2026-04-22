from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        # Detect if the current user is a Dashboard Viewer
        is_dashboard_viewer = self.env.user.has_group('openg2p_zanzibar_map.group_dashboard_viewer')
        
        # Admin Exception: If they are a System Admin, we MUST NOT hide the navbar
        # otherwise they get locked out of Odoo settings.
        is_system_admin = self.env.user.has_group('base.group_system')
        
        result['is_dashboard_viewer'] = is_dashboard_viewer
        # We only force 'standalone' mode for non-admin viewers
        result['is_dashboard_standalone'] = is_dashboard_viewer and not is_system_admin
        
        return result
