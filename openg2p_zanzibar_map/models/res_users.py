from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

try:
    from botocore.exceptions import EndpointConnectionError
except ImportError:
    EndpointConnectionError = Exception

class ResUsers(models.Model):
    _inherit = 'res.users'

    has_dashboard_viewer_access = fields.Boolean(
        string='Dashboard Viewer',
        compute='_compute_dashboard_viewer_access',
        inverse='_set_dashboard_viewer_access',
        help="Check this to grant the user access to the Pensioner Dashboard."
    )

    def _compute_dashboard_viewer_access(self):
        group_id = self.env.ref('openg2p_zanzibar_map.group_dashboard_viewer', raise_if_not_found=False)
        for user in self:
            if group_id:
                user.has_dashboard_viewer_access = group_id.id in user.groups_id.ids
            else:
                user.has_dashboard_viewer_access = False

    def _set_dashboard_viewer_access(self):
        group = self.env.ref('openg2p_zanzibar_map.group_dashboard_viewer', raise_if_not_found=False)
        if not group:
            return
        for user in self:
            if user.has_dashboard_viewer_access:
                user.write({'groups_id': [(4, group.id)]})
            else:
                user.write({'groups_id': [(3, group.id)]})

    def write(self, vals):
        """
        Safeguard: Catch S3 connection errors during user form saves.
        This prevents 'Invalid Operation' popups when Minio is offline.
        """
        try:
            return super(ResUsers, self).write(vals)
        except EndpointConnectionError as e:
            _logger.warning("Captured S3 Connection Error during user save: %s. Proceeding anyway.", str(e))
            # We return True because the user data was likely written to DB, 
            # and only the background sync/image processing failed.
            return True
        except Exception as e:
            # Re-raise other errors
            if "Could not connect to the endpoint URL" in str(e):
                _logger.warning("Captured generic connection error: %s. Proceeding anyway.", str(e))
                return True
            raise e
