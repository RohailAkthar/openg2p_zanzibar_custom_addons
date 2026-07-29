import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    def init(self):
        super().init()
        # Automatically clean up existing duplicate phone rows in DB on module upgrade
        try:
            self.env.cr.execute("""
                DELETE FROM g2p_phone_number
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY partner_id, TRIM(phone_no), COALESCE(phone_owner, 'beneficiary')
                            ORDER BY id ASC
                        ) as rnum
                        FROM g2p_phone_number
                    ) t WHERE t.rnum > 1
                );
            """)
        except Exception as e:
            _logger.warning("Could not execute phone cleanup in init: %s", str(e))

    def _deduplicate_phone_numbers(self):
        for partner in self:
            all_phones = self.env["g2p.phone.number"].sudo().search([("partner_id", "=", partner.id)], order="id asc")
            seen = set()
            to_unlink = self.env["g2p.phone.number"].sudo()
            for p in all_phones:
                key = (str(p.phone_no).strip(), p.phone_owner or "beneficiary")
                if key in seen:
                    to_unlink |= p
                else:
                    seen.add(key)
            if to_unlink:
                to_unlink.sudo().unlink()

            # Recompute clean phone string for partner.phone (beneficiary active numbers only, unique, separated by ', ')
            benf_phones = partner.phone_number_ids.filtered(
                lambda r: not r.disabled and r.phone_no and r.phone_owner in ["beneficiary", False]
            ).mapped("phone_no")
            unique_phones = list(dict.fromkeys(p.strip() for p in benf_phones if p and p.strip()))
            clean_str = ", ".join(unique_phones)
            if partner.phone != clean_str:
                super(ResPartner, partner).write({"phone": clean_str})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Requirement: Direct Excel upload shows as 'Yes'
            if self.env.context.get("import_file"):
                vals["db_import"] = "yes"
            # Requirement: Approved from draft shows as 'No'
            elif vals.get("db_import") == "yes":
                vals["db_import"] = "no"
        partners = super().create(vals_list)
        partners._deduplicate_phone_numbers()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if "phone_number_ids" in vals or "phone" in vals:
            self._deduplicate_phone_numbers()
        return res

    benf_post_code = fields.Char(string="Post Code", tracking=True)
    benf_zan_id = fields.Char(string="Zanzibar ID", compute="_compute_benf_zan_id", readonly=True, store=True)
    disability = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Do you have any disability?",
        tracking=True
    )
    type_of_disability = fields.Char(
        string="Type of Disease / Disability",
        tracking=True
    )
    is_receiving_allowance = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="Are you receiving 5000 allowance from district council? (Below 70 years)",
        tracking=True
    )
    has_health_insurance = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="Are you covered with any health insurance scheme?",
        tracking=True
    )
    status = fields.Selection(
        [
            ("active", "Active"),
            ("Suspended", "Suspended"),
            ("Deceased", "Deceased"),
            ("Inactive", "Inactive"),
        ],
        string="Status",
        default="active",
        tracking=True
    )
    @api.depends("reg_ids.value", "reg_ids.id_type")
    def _compute_benf_zan_id(self):
        for record in self:
            val = False
            # Check for Zanzibar ID in reg_ids
            if record.reg_ids:
                zan_id_record = record.reg_ids.filtered(lambda r: r.id_type.name == "Zanzibar ID")
                if zan_id_record:
                    val = zan_id_record[0].value
            record.benf_zan_id = val

    x_region_code=fields.Char("X_Reg")
    
    x_district_code=fields.Char("X_dist")

    pensioner_id=fields.Char(string="Pensioner ID")
    middle_name = fields.Char(string="Middle Name", translate=False, tracking=True)

    @api.onchange("is_group", "family_name", "given_name", "middle_name", "addl_name")
    def name_change(self):
        vals = {}
        if not self.is_group:
            parts = [self.given_name, self.middle_name, self.family_name]
            # Filter None, False or empty strings
            parts = [p.strip() for p in parts if p and p.strip()]
            name = " ".join(parts)
            vals.update({"name": name.upper()})
            self.update(vals)

    def enable_registrant(self):
        res = super().enable_registrant()
        self.write({"status": "active"})
        return res

    def mark_registrant_as_duplicated(self, partner_ids):
        partners = self.browse([int(p) for p in partner_ids if p])
        if partners:
            partners.write({"is_duplicated": True})

    def reset_duplicate_flag(self, is_group):
        active_val = "FALSE" if self.env.context.get("scan_inactive_only") else "TRUE"
        query = f"""
            UPDATE res_partner
            SET is_duplicated = FALSE
            WHERE is_registrant = TRUE AND is_group = {is_group} AND active = {active_val}
        """
        _logger.debug("Custom reset DB Query: %s" % query)
        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None

    def get_duplicate_registrants(self, is_group, id_types, group_condition):
        active_val = "FALSE" if self.env.context.get("scan_inactive_only") else "TRUE"
        query = f"""
            SELECT
            id_type.name AS id_name, reg_id.value AS id_value, STRING_AGG(partner.id::text, ',')
            AS partner_ids
            FROM res_partner AS partner
            INNER JOIN g2p_reg_id AS reg_id ON reg_id.partner_id = partner.id
            JOIN g2p_id_type AS id_type ON id_type.id = reg_id.id_type
            LEFT JOIN g2p_group_kind AS group_kind ON group_kind.id = partner.kind
            WHERE is_registrant = TRUE AND id_type.name IN {id_types} AND is_group = {is_group}
              AND partner.active = {active_val}
              AND {group_condition}
            GROUP BY id_type.name, reg_id.value
            HAVING COUNT(partner.id) > 1
        """
        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
            individual_duplicates = self._cr.dictfetchall()
            return individual_duplicates
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None

    def get_duplicate_group_members(self, group_ids, id_types):
        active_val = "FALSE" if self.env.context.get("scan_inactive_only") else "TRUE"
        query = f"""
            SELECT
            id_type.name AS id_name, reg_id.value AS id_value, STRING_AGG(group_member.group::text, ',')
            AS partner_ids, STRING_AGG(group_member.individual::text, ',') AS individual_ids
            FROM res_partner AS partner
            JOIN g2p_group_membership AS group_member ON partner.id = group_member.individual
            INNER JOIN g2p_reg_id AS reg_id ON reg_id.partner_id = partner.id
            JOIN g2p_id_type AS id_type ON id_type.id = reg_id.id_type
            WHERE partner.is_registrant = TRUE AND id_type.name IN {id_types}
              AND partner.active = {active_val}
              AND group_member.group IN ({group_ids})
            GROUP BY id_type.name, reg_id.value
            HAVING COUNT(partner.id) > 1
        """
        try:
            self._cr.execute(query)  # pylint: disable=sql-injection
            group_duplicates = self._cr.dictfetchall()
            return group_duplicates
        except Exception as e:
            _logger.error("Database Query Error: %s", e)
            raise UserError(_("Database Query Error: %s") % e) from None

class G2PDisableRegistrantWizard(models.TransientModel):
    _inherit = "g2p.disable.registrant.wizard"

    disabled_reason_selection = fields.Selection(
        [
            ("Suspended", "Suspended"),
            ("Deceased", "Deceased"),
            ("Inactive", "Inactive"),
        ],
        string="Reason",
        required=True,
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Attachments",
    )

    @api.onchange("disabled_reason_selection")
    def _onchange_disabled_reason_selection(self):
        if self.disabled_reason_selection:
            self.disabled_reason = self.disabled_reason_selection

    def disable_registrant(self):
        for rec in self:
            if rec.partner_id:
                rec.partner_id.write({
                    "status": rec.disabled_reason_selection
                })
            if rec.attachment_ids:
                backend = rec.partner_id.get_registry_documents_store()
                if not backend:
                    backend = self.env.ref("storage_backend.default_storage_backend", raise_if_not_found=False)
                for attachment in rec.attachment_ids:
                    datas_str = attachment.datas.decode("utf-8") if isinstance(attachment.datas, bytes) else attachment.datas
                    self.env["storage.file"].create({
                        "name": attachment.name,
                        "data": datas_str,
                        "backend_id": backend.id if backend else False,
                        "registrant_id": rec.partner_id.id,
                    })
                rec.attachment_ids.unlink()
        return super().disable_registrant()



