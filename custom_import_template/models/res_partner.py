import logging
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"


    import_zan_id = fields.Char(string="Zanzibar ID", help="Technical field used for importing Zanzibar ID")
    import_full_name = fields.Char(string="Beneficiary Name", help="Technical field used for importing Full Name")
    import_nominee_full_name = fields.Char(string="Next of Kin Name / Closest Relative Name", help="Technical field used for importing Nominee Full Name")
    import_shehia = fields.Char(string="Shehia (Ward)", help="Technical field used for importing Shehia (Ward)")
    import_region = fields.Char(string="Region (Import)", help="Technical field used for importing Region")
    import_district = fields.Char(string="District (Import)", help="Technical field used for importing District")
    import_status = fields.Char(string="Status (Import)", help="Technical field used for importing Status")
    import_mobile = fields.Char(string="Mobile", help="Technical field used for importing Mobile")
    import_disability = fields.Char(string="Disability Status", help="Technical field used for importing Disability Status")

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Individuals'),
            'template': '/custom_import_template/static/xls/individual_import_template.xlsx',
        }]

    def _split_full_name(self, full_name):
        """Splits a full name into (first, middle, surname)."""
        if not full_name:
            return "", "", ""
        parts = full_name.split()
        if len(parts) == 1:
            return parts[0], "", ""
        elif len(parts) == 2:
            return parts[0], "", parts[1]
        else:
            return parts[0], parts[1], " ".join(parts[2:])

    def _normalize_tz_phone(self, number):
        if not number:
            return ""
        clean_number = "".join(c for c in str(number).strip() if c.isdigit() or c == '+')
        if not clean_number:
            return ""
        if clean_number.startswith('+255'):
            return clean_number
        if clean_number.startswith('255'):
            return '+' + clean_number
        if clean_number.startswith('0'):
            return '+255' + clean_number[1:]
        if len(clean_number) == 9 and clean_number[0] in ('6', '7'):
            return '+255' + clean_number
        return clean_number

    def _prepare_import_vals(self, vals):
        """Prepares import values in bulk to avoid per-record writes."""
        # 1. Handle Full Name
        if vals.get('import_full_name'):
            first, middle, surname = self._split_full_name(vals['import_full_name'])
            vals.setdefault('given_name', first)
            vals.setdefault('middle_name', middle)
            vals.setdefault('family_name', surname)

        # 2. Ensure Name Populated
        if not vals.get('name'):
            given_name = vals.get('given_name') or ''
            middle_name = vals.get('middle_name') or ''
            family_name = vals.get('family_name') or ''

            if given_name or middle_name or family_name:
                name_parts = []
                if family_name:
                    if given_name or middle_name:
                        name_parts.append(f"{family_name},")
                    else:
                        name_parts.append(family_name)
                if given_name:
                    name_parts.append(given_name)
                if middle_name:
                    name_parts.append(middle_name)
                
                fullname = " ".join(filter(None, name_parts)).upper()
                if fullname:
                    vals['name'] = fullname

        # 3. Handle Shehia (Ward) -> Address
        if vals.get('import_shehia'):
            vals['address'] = vals['import_shehia']

        # 4. Handle Nominee Full Name
        if vals.get('import_nominee_full_name'):
            first, middle, surname = self._split_full_name(vals['import_nominee_full_name'])
            vals.update({
                'nominee_first_name': first,
                'nominee_middle_name': middle,
                'nominee_last_name': surname,
            })

        # 5. Handle Payment Mode
        if vals.get('account_num'):
            vals['payment_mode'] = 'bank'

        # 6. Normalize Status Value and sync Active/Disabled state
        status_in = vals.get('import_status') or vals.get('status')
        if status_in:
            status_val = str(status_in).strip().lower()
            if status_val == 'active':
                vals.update({
                    'status': 'active',
                    'active': True,
                    'disabled': False,
                    'disabled_reason': False,
                    'disabled_by': False,
                })
            else:
                mapped_status = 'Suspended'
                if status_val in ('decesed', 'deceased'):
                    mapped_status = 'Deceased'
                elif status_val == 'inactive':
                    mapped_status = 'Inactive'
                elif status_val == 'suspended':
                    mapped_status = 'Suspended'
                
                vals.update({
                    'status': mapped_status,
                    'active': False,
                    'disabled': fields.Datetime.now(),
                    'disabled_reason': _('Imported as %s') % mapped_status,
                    'disabled_by': self.env.user.id,
                })

        # 7. Normalize Yes/No selection fields to lowercase 'yes' / 'no'
        for fld in ('disability', 'is_receiving_allowance', 'has_health_insurance'):
            val_in = vals.get(fld)
            if val_in:
                val_str = str(val_in).strip().lower()
                if val_str in ('yes', 'y', '1', 'true'):
                    vals[fld] = 'yes'
                elif val_str in ('no', 'n', '0', 'false'):
                    vals[fld] = 'no'

        # Also support import_disability technical field
        if vals.get('import_disability'):
            dis_val = str(vals['import_disability']).strip().lower()
            if dis_val in ('yes', 'y', '1', 'true'):
                vals['disability'] = 'yes'
            elif dis_val in ('no', 'n', '0', 'false'):
                vals['disability'] = 'no'

        # Normalize Gender field case-insensitively
        if vals.get('gender'):
            g_val = str(vals['gender']).strip().lower()
            if g_val in ('male', 'm'):
                vals['gender'] = 'Male'
            elif g_val in ('female', 'f'):
                vals['gender'] = 'Female'
            elif g_val in ('other', 'o'):
                vals['gender'] = 'Other'

        # 8. Set standard phone and mobile fields if imported via import_mobile
        mobile_in = vals.get('import_mobile')
        if mobile_in:
            norm_val = self._normalize_tz_phone(mobile_in)
            vals['import_mobile'] = norm_val
            vals['phone'] = norm_val
            vals['mobile'] = norm_val

        # Normalize any other phone numbers case-insensitively
        for fld in ('phone', 'mobile', 'nominee_mobile'):
            val = vals.get(fld)
            if val:
                vals[fld] = self._normalize_tz_phone(val)

    def _handle_import_lookups(self, vals_list):
        """Batch search for Region and District IDs with case-insensitivity."""
        regions_found = {}
        districts_found = {}
        
        region_names = list({v['import_region'] for v in vals_list if v.get('import_region')})
        if region_names:
            domain = ['|'] * (len(region_names) - 1)
            for name in region_names:
                domain.append(('name', '=ilike', name))
            regions = self.env['g2p.region'].sudo().search(domain)
            regions_found = {r.name.lower(): r.id for r in regions}

        district_names = list({v['import_district'] for v in vals_list if v.get('import_district')})
        if district_names:
            domain = ['|'] * (len(district_names) - 1)
            for name in district_names:
                domain.append(('name', '=ilike', name))
            districts = self.env['g2p.district'].sudo().search(domain)
            districts_found = {d.name.lower(): d.id for d in districts}

        for vals in vals_list:
            if vals.get('import_region'):
                rid = regions_found.get(vals['import_region'].lower())
                if rid:
                    vals['region'] = rid
            if vals.get('import_district'):
                did = districts_found.get(vals['import_district'].lower())
                if did:
                    vals['district'] = did

    def _handle_custom_import_logic(self, vals_list, records):
        """Helper to handle IDs in batch to avoid per-record database lookups."""
        if not vals_list or not records:
            return

        # 1. Batch lookup for the Zanzibar ID type (Performance: Search once instead of 40,000 times)
        zan_id_type = self.env['g2p.id.type'].sudo().search([('name', '=ilike', 'Zanzibar ID')], limit=1)
        if not zan_id_type:
            return

        reg_ids_to_create = []
        
        # 2. Process records in batch
        for i, record in enumerate(records):
            vals = vals_list[i] if i < len(vals_list) else vals_list[-1]
            zan_val = vals.get('import_zan_id')
            if not zan_val:
                continue

            # Check for existing IDs to avoid duplicates (filtered is fast for memory records)
            existing_id = record.sudo().reg_ids.filtered(lambda r: r.id_type == zan_id_type)
            if existing_id:
                if existing_id[0].value != zan_val:
                    existing_id[0].write({'value': zan_val, 'status': 'valid'})
            else:
                reg_ids_to_create.append({
                    'partner_id': record.id,
                    'id_type': zan_id_type.id,
                    'value': zan_val,
                    'status': 'valid',
                })

        # 3. Bulk create all Registrant IDs in a single database operation
        if reg_ids_to_create:
            self.env['g2p.reg.id'].sudo().create(reg_ids_to_create)

    def _sync_beneficiary_phone(self, mobile):
        if not mobile:
            return
            
        # Get active beneficiary numbers
        active_phones = self.phone_number_ids.filtered(
            lambda p: (p.phone_owner == 'beneficiary' or not p.phone_owner) and not p.disabled
        )
        
        exists_active = False
        for phone in active_phones:
            if phone.phone_no == mobile:
                exists_active = True
            else:
                # Disable old active number
                phone.write({
                    'disabled': fields.Datetime.now(),
                    'disabled_by': self.env.user.id
                })
        
        if not exists_active:
             self.env['g2p.phone.number'].create({
                 'partner_id': self.id,
                 'phone_no': mobile,
                 'phone_owner': 'beneficiary',
                 'country_id': self.env.ref('base.tz').id
             })

    def _sync_partner_phone_field(self):
        for record in self:
            active_phones = record.phone_number_ids.filtered(lambda p: not p.disabled)
            phone_val = ",".join(active_phones.mapped("phone_no"))
            if record.phone != phone_val:
                super(ResPartner, record).write({'phone': phone_val})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_import_vals(vals)
        self._handle_import_lookups(vals_list)
        records = super().create(vals_list)
        
        # Optimized batch handling for Zanzibar IDs
        self._handle_custom_import_logic(vals_list, records)

        # Sync beneficiary phone numbers
        for idx, record in enumerate(records):
            vals = vals_list[idx] if idx < len(vals_list) else vals_list[-1]
            mobile_val = vals.get('import_mobile') or vals.get('mobile') or vals.get('phone')
            if mobile_val:
                record._sync_beneficiary_phone(mobile_val)

        # Sync the partner phone field
        records._sync_partner_phone_field()

        return records

    def write(self, vals):
        self._prepare_import_vals(vals)
        self._handle_import_lookups([vals])
        res = super().write(vals)
        
        # Consistent handling for writes
        self._handle_custom_import_logic([vals], self)

        # Sync beneficiary phone numbers
        mobile_val = vals.get('import_mobile') or vals.get('mobile') or vals.get('phone')
        if mobile_val:
            for record in self:
                record._sync_beneficiary_phone(mobile_val)

        # Sync the partner phone field
        self._sync_partner_phone_field()

        return res

class G2PPhoneNumber(models.Model):
    _inherit = "g2p.phone.number"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for partner in records.mapped('partner_id'):
            partner._sync_partner_phone_field()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ('phone_no', 'disabled', 'partner_id')):
            for partner in self.mapped('partner_id'):
                partner._sync_partner_phone_field()
        return res
