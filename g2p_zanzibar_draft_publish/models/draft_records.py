import json
from odoo import api, fields, models

class G2PDraftRecord(models.Model):
    _inherit = "draft.record"

    zan_id = fields.Char(string="Zan ID")
    given_name = fields.Char(string="Given Name")
    middle_name = fields.Char(string="Middle Name")
    family_name = fields.Char(string="Family Name")
    birthdate_date = fields.Date(string="Date of Birth")
    registration_date = fields.Date(string="Registration Date")
    nominee_mobile = fields.Char(string="Nominee Mobile")

    name = fields.Char(string="Name", compute="_compute_name", store=True)

    @api.depends('given_name', 'middle_name', 'family_name')
    def _compute_name(self):
        for record in self:
            name_parts = []
            if record.family_name:
                name_parts.append(record.family_name + ",")
            if record.given_name:
                name_parts.append(record.given_name)
            if record.middle_name:
                name_parts.append(record.middle_name)
            record.name = " ".join(name_parts).strip()

    @api.model_create_multi
    def create(self, vals_list):
        # Save the original rich partner_data before base class overwrites it
        saved_partner_data = []
        for vals in vals_list:
            saved_partner_data.append(vals.get('partner_data'))
            # Provide defaults for fields expected by base create to prevent KeyError
            for field in ['given_name', 'family_name', 'addl_name', 'gender', 'region', 'phone']:
                if field not in vals:
                    vals[field] = False
        
        records = super().create(vals_list)
        
        # Restore the original rich partner_data, merging with base-generated data
        for record, original_pd in zip(records, saved_partner_data):
            if original_pd:
                try:
                    original_data = json.loads(original_pd) if isinstance(original_pd, str) else (original_pd or {})
                    # Load what base class generated (minimal subset)
                    try:
                        base_data = json.loads(record.partner_data) if isinstance(record.partner_data, str) else (record.partner_data or {})
                    except (json.JSONDecodeError, TypeError):
                        base_data = {}
                    # Merge: original data takes priority, but keep base-generated keys
                    merged = {**base_data, **original_data}
                    merged["imported_record_state"] = "draft"
                    record.sudo().write({'partner_data': json.dumps(merged)})
                except (json.JSONDecodeError, TypeError):
                    pass
            else:
                record._update_partner_data_from_fields()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Only auto-update partner_data from fields if partner_data was NOT explicitly provided
        if 'partner_data' not in vals:
            if any(f in vals for f in ['zan_id', 'birthdate_date', 'registration_date', 'name', 'phone', 'gender', 'nominee_mobile']):
                for record in self:
                    record._update_partner_data_from_fields()
        return res

    def _update_partner_data_from_fields(self):
        self.ensure_one()
        try:
            partner_data = json.loads(self.partner_data or "{}")
        except (json.JSONDecodeError, TypeError):
            partner_data = {}
        
        if self.zan_id:
            partner_data["benf_zan_id"] = self.zan_id
        if self.birthdate_date:
            partner_data["birthdate"] = self.birthdate_date.isoformat()
        if self.registration_date:
            partner_data["registration_date"] = self.registration_date.isoformat()
        if self.name:
            partner_data["name"] = self.name.upper()
        if self.given_name:
            partner_data["given_name"] = self.given_name
        if self.family_name:
            partner_data["family_name"] = self.family_name
        if self.middle_name:
            partner_data["middle_name"] = self.middle_name
        if self.phone:
            partner_data["phone"] = self.phone
        
        if self.nominee_mobile:
            partner_data["nominee_mobile"] = self.nominee_mobile
        if self.gender:
            partner_data["gender"] = self.gender

        self.sudo().partner_data = json.dumps(partner_data)

    def _return_wizard_with_context(self, view_id):
        """Override to reconstruct phone_number_ids and reg_ids ORM commands
        from plain string values stored in partner_data."""
        result = super()._return_wizard_with_context(view_id)
        ctx = result.get("context", {})
        json_data = json.loads(self.partner_data or "{}")

        # Reconstruct phone records from plain strings
        # The wizard view uses beneficiary_phone_number_ids and nominee_phone_number_ids
        # (from relative_nominee module), not phone_number_ids
        country_tz = self.env.ref("base.tz", raise_if_not_found=False)
        country_id = country_tz.id if country_tz else False

        benf_phone = json_data.get("phone") or self.phone
        if benf_phone:
            benf_phone_cmd = [(0, 0, {
                "phone_no": benf_phone,
                "phone_owner": "beneficiary",
                "country_id": country_id,
            })]
            ctx["default_beneficiary_phone_number_ids"] = benf_phone_cmd
            ctx["default_phone_number_ids"] = benf_phone_cmd

        nominee_phone = json_data.get("nominee_mobile") or self.nominee_mobile
        if nominee_phone:
            nom_phone_cmd = [(0, 0, {
                "phone_no": nominee_phone,
                "phone_owner": "nominee",
                "country_id": country_id,
            })]
            ctx["default_nominee_phone_number_ids"] = nom_phone_cmd
            ctx["default_nominee_mobile"] = nominee_phone
            # Also append to phone_number_ids
            existing = ctx.get("default_phone_number_ids", [])
            ctx["default_phone_number_ids"] = existing + nom_phone_cmd

        # Reconstruct reg_ids from plain strings
        reg_ids = []
        benf_zan_id = json_data.get("benf_zan_id") or self.zan_id
        if benf_zan_id:
            id_type = self.env["g2p.id.type"].sudo().search(
                [("name", "=", "Zanzibar ID")], limit=1
            )
            if id_type:
                reg_ids.append((0, 0, {
                    "id_type": id_type.id,
                    "value": benf_zan_id,
                    "status": "valid",
                }))

        nominee_zan_id = json_data.get("nominee_zanid")
        if nominee_zan_id:
            id_type = self.env["g2p.id.type"].sudo().search(
                [("name", "=", "Nominee Zanzibar ID")], limit=1
            )
            if id_type:
                reg_ids.append((0, 0, {
                    "id_type": id_type.id,
                    "value": nominee_zan_id,
                    "status": "valid",
                }))

        if reg_ids:
            ctx["default_reg_ids"] = reg_ids

        result["context"] = ctx
        return result

    def action_publish(self):
        self.ensure_one()
        partner_data = json.loads(self.partner_data or "{}")

        partner_model = self.env["res.partner"]
        fields_metadata = partner_model.fields_get()
        valid_data = {}

        validators = {
            "char": lambda v, f: isinstance(v, str),
            "text": lambda v, f: isinstance(v, str),
            "integer": lambda v, f: isinstance(v, int),
            "float": lambda v, f: isinstance(v, (int, float)),
            "boolean": lambda v, f: isinstance(v, bool),
            "many2one": lambda v, f: isinstance(v, int)
            and self.env[f["relation"]].browse(v).exists(),
            "many2many": lambda v, f: isinstance(v, list)
            and all(self.env[f["relation"]].browse(x[1]).exists() for x in v),
            "one2many": lambda v, f: isinstance(v, list),
            "datetime": lambda v, f: True,
            "date": lambda v, f: True,
            "selection": lambda v, f: v in [option[0] for option in f.get("selection", [])],
            "binary": lambda v, f: isinstance(v, (str, bytes)),
        }

        # Exclude relational ORM command fields — we create those explicitly after partner creation
        skip_fields = {'phone_number_ids', 'reg_ids'}
        for field_name, value in partner_data.items():
            if field_name in skip_fields:
                continue
            if field_name not in fields_metadata:
                continue
            field_info = fields_metadata[field_name]
            field_type = field_info.get("type")
            if validators.get(field_type, lambda v, f: False)(value, field_info):
                valid_data[field_name] = value

        valid_data.update(
            {
                "db_import": "yes",
                "is_registrant": True,
                "is_group": False,
                "imported_record_state": "published",
            }
        )

        if partner_data.get("name"):
            valid_data["name"] = partner_data["name"]
        else:
            given_name = partner_data.get("given_name") or ""
            family_name = partner_data.get("family_name") or ""
            middle_name = partner_data.get("middle_name") or ""
            valid_data["name"] = " ".join(filter(None, [family_name + "," if family_name else "", given_name, middle_name])).strip()

        partner = partner_model.sudo().create(valid_data)

        # --- Create phone number records with correct phone_owner ---
        country_tz = self.env.ref("base.tz", raise_if_not_found=False)
        country_id = country_tz.id if country_tz else False

        benf_phone = partner_data.get("phone") or self.phone
        if benf_phone:
            self.env["g2p.phone.number"].sudo().create({
                "partner_id": partner.id,
                "phone_no": benf_phone,
                "phone_owner": "beneficiary",
                "country_id": country_id,
            })

        # NOTE: Nominee phone is NOT created here — the `relative_nominee` module's
        # res.partner.create() override auto-creates it via _sync_nominee_phone()
        # when nominee_mobile is set in valid_data.

        # --- Create registration ID records ---
        benf_zan_id = partner_data.get("benf_zan_id") or self.zan_id
        if benf_zan_id:
            id_type = self.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
            if id_type:
                existing_reg = self.env["g2p.reg.id"].sudo().search([
                    ("partner_id", "=", partner.id),
                    ("id_type", "=", id_type.id),
                    ("value", "=", benf_zan_id.strip())
                ], limit=1)
                if not existing_reg:
                    self.env["g2p.reg.id"].sudo().create({
                        "partner_id": partner.id,
                        "id_type": id_type.id,
                        "value": benf_zan_id.strip(),
                        "status": "valid",
                    })

        nominee_zan_id = partner_data.get("nominee_zanid")
        if nominee_zan_id:
            id_type = self.env["g2p.id.type"].sudo().search([("name", "=", "Nominee Zanzibar ID")], limit=1)
            if id_type:
                existing_reg = self.env["g2p.reg.id"].sudo().search([
                    ("partner_id", "=", partner.id),
                    ("id_type", "=", id_type.id),
                    ("value", "=", nominee_zan_id.strip())
                ], limit=1)
                if not existing_reg:
                    self.env["g2p.reg.id"].sudo().create({
                        "partner_id": partner.id,
                        "id_type": id_type.id,
                        "value": nominee_zan_id.strip(),
                        "status": "valid",
                    })

        # Link the partner back to the original draft record (if field exists)
        if 'draft_record_id' in partner_model._fields:
            partner.draft_record_id = self.id
        
        self.write({"state": "published"})
        return partner
