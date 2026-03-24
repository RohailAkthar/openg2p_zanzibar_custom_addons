import logging

from werkzeug.exceptions import Forbidden

from odoo import http, _
from odoo.http import request

from odoo.addons.g2p_registration_portal_base.controllers.main import (
    G2PregistrationPortalBase,
)

_logger = logging.getLogger(__name__)


class G2PPortalUpdateRestriction(G2PregistrationPortalBase):
    """Override individual portal routes to enforce group-based access control.

    - Admin group: can Create and Update individuals
    - User group: can only Update individuals
    - No group: no access to Create or Update
    """

    def _check_portal_admin(self):
        """Check if the current user belongs to the Portal Admin group."""
        if not request.env.user.has_group(
            "g2p_portal_update_restriction.group_portal_registrant_admin"
        ):
            raise Forbidden(_("You do not have permission to create new registrants."))

    def _check_portal_user(self):
        """Check if the current user belongs to the Portal User group (or Admin, which implies User)."""
        if not request.env.user.has_group(
            "g2p_portal_update_restriction.group_portal_registrant_user"
        ):
            raise Forbidden(_("You do not have permission to update registrants."))

    # ---- List view: User (and Admin) ----

    def individual_list(self, **kw):
        self._check_portal_user()
        return super().individual_list(**kw)

    @http.route("/portal/registration/zan_id_lookup", type="json", auth="user", csrf=False)
    def zan_id_lookup(self, zan_id):
        if not zan_id:
            return super().zan_id_lookup(zan_id)

        ZanID = zan_id.strip()

        # 1. Check for Draft (Active)
        draft_active = request.env['draft.record'].sudo().search([
            ('zan_id', '=', ZanID),
            ('state', '=', 'draft')
        ], limit=1)
        if draft_active:
            return {
                "status": "ALREADY_EXISTS_IN_DRAFT",
                "message": "Zan id is already exist in the system and it is in the draft state"
            }

        # 2. Check for Rejected
        draft_rejected = request.env['draft.record'].sudo().search([
            ('zan_id', '=', ZanID),
            ('state', '=', 'rejected')
        ], limit=1)
        if draft_rejected:
            return {
                "status": "ALREADY_EXISTS",
                "message": "zan id is already exist so pls update the record."
            }

        # 3. Check for Approved (Published)
        draft_published = request.env['draft.record'].sudo().search([
            ('zan_id', '=', ZanID),
            ('state', '=', 'published')
        ], limit=1)

        id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
        reg_id = request.env["g2p.reg.id"].sudo().search([
            ("id_type", "=", id_type.id),
            ("value", "=", ZanID)
        ], limit=1)

        if draft_published or (reg_id and reg_id.partner_id):
            return {
                "status": "ALREADY_EXISTS",
                "message": "Zan id is already exist in the system"
            }

        return super().zan_id_lookup(zan_id)

    # ---- Create routes: Admin only ----

    def individual_registrar_create(self, **kw):
        self._check_portal_admin()
        return super().individual_registrar_create(**kw)

    def individual_create_submit(self, **kw):
        self._check_portal_admin()
        return super().individual_create_submit(**kw)

    # ---- Update routes: User (and Admin) ----

    def indvidual_update(self, _id, **kw):
        self._check_portal_user()
        return super().indvidual_update(_id, **kw)

    @http.route(["/portal/registration/individual/view/<int:_id>"], type="http", auth="user", csrf=False)
    def individual_view_details(self, _id, **kw):
        self._check_portal_user()
        return super().individual_view_details(_id, **kw)

    def update_individual_submit(self, **kw):
        self._check_portal_user()
        
        # Capture the draft state BEFORE super() if possible, 
        # but super() might write to it.
        draft_id = kw.get("group_id")
        draft = False
        if draft_id:
            draft = request.env["draft.record"].sudo().browse(int(draft_id)).exists()

        res = super().update_individual_submit(**kw)

        # If it's a rejected draft, move it back to 'draft' state after update
        if draft and draft.state == 'rejected':
            draft.sudo().write({'state': 'draft'})
            _logger.info("Draft record %s reset to 'draft' state after update from portal.", draft.id)

        return res
