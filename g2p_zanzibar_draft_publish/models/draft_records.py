import json
from odoo import api, fields, models

class G2PDraftRecord(models.Model):
    _inherit = "draft.record"
    _order = "write_date desc, id desc"

    # Stored + tracked computed fields with inverse for full chatter logging
    _INV = "_inverse_mapped_fields"

    zan_id = fields.Char(string="Zan ID", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    given_name = fields.Char(string="Given Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    middle_name = fields.Char(string="Middle Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    family_name = fields.Char(string="Family Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    birthdate_date = fields.Date(string="Date of Birth", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    registration_date = fields.Date(string="Registration Date", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    phone = fields.Char(string="Phone", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_mobile = fields.Char(string="Nominee Mobile", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    region_id = fields.Many2one('g2p.region', string="Region", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    post_code = fields.Char(string="Post Code", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    district_id = fields.Many2one('g2p.district', string="District", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    gender = fields.Selection([('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], string="Gender", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True, readonly=True)
    has_disability = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Do you have any disability?", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    receives_allowance = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Are you receiving 5000 allowance from district council? (Below 70 years)", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    has_health_insurance = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Are you covered with any health insurance scheme?", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    # Nominee fields
    nominee_first_name = fields.Char(string="First Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_middle_name_display = fields.Char(string="Middle Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_last_name = fields.Char(string="Surname", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_gender = fields.Selection([('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], string="Nominee Gender", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True, readonly=True)
    nominee_zanid = fields.Char(string="Nominee ZanID", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_rel_benf = fields.Char(string="Relationship with beneficiary", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_house_street = fields.Char(string="House & Street", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_shehia = fields.Char(string="Nominee Shehia (Ward)", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_post_code_display = fields.Char(string="Nominee PO BOX / Post code", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_region_display = fields.Char(string="Nominee Region", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    nominee_district_display = fields.Char(string="Nominee District", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    # IDs fields
    id_type_1 = fields.Char(string="ID Type", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    id_number_1 = fields.Char(string="ID Number", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    id_type_2 = fields.Char(string="Nominee ID Type", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    id_number_2 = fields.Char(string="Nominee ID Number", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    # Payment Mode fields
    payment_mode = fields.Selection([
        ('bank', 'Bank'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_wallet', 'Mobile Wallet'),
        ('cash_pickup', 'Cash Pickup'),
        ('ezypesa', 'EzyPesa'),
        ('tigopesa', 'Tigo Pesa'),
        ('airtel_money', 'Airtel Money'),
        ('mpesa', 'M-Pesa'),
        ('halopesa', 'Halo Pesa')
    ], string="Preferred Payment Method", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    mobile_wallet = fields.Char(string="Mobile Wallet", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    bank_name = fields.Char(string="Bank Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    account_num = fields.Char(string="Account Number", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    account_name = fields.Char(string="Account Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    # Pension fields
    other_pension = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Are you receiving any other pension?", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    scheme_name = fields.Char(string="Scheme Name", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    # Address fields
    address_display = fields.Char(string="Address", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)
    shehia_display = fields.Char(string="Shehia (Ward)", compute="_compute_mapped_fields", inverse=_INV, store=True, tracking=True)

    rejected_by_user_id = fields.Many2one('res.users', string='Rejected By', readonly=True, tracking=True)
    
    # Field Officer Details for Draft Visibility (computed from portal creator)
    enumerator_name = fields.Char(string="Field Officer", compute="_compute_enumerator_details")
    enumerator_eid = fields.Char(string="Field Officer ID", compute="_compute_enumerator_details")

    name = fields.Char(string="Name", compute="_compute_name", store=True)
    age = fields.Integer(string="Age", compute="_compute_age")

    # Force partner_data to be a JSON object at the model level to prevent widget crashes
    partner_data = fields.Json(inherit_field=True, default={})

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

    @api.depends('birthdate_date')
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if record.birthdate_date:
                dob = record.birthdate_date
                record.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            else:
                record.age = 0

    @api.depends('create_uid')
    def _compute_enumerator_details(self):
        """Automatically pull field officer details from the draft creator for visibility."""
        for record in self:
            creator = record.create_uid
            if creator and creator.partner_id:
                record.enumerator_name = creator.name
                record.enumerator_eid = creator.partner_id.eid
            else:
                record.enumerator_name = False
                record.enumerator_eid = False

    @api.depends('partner_data')
    def _compute_mapped_fields(self):
        """Extract values from partner_data JSON blob for display in the UI."""
        all_fields = [
            'zan_id', 'given_name', 'middle_name', 'family_name', 'birthdate_date', 'registration_date',
            'phone', 'region_id', 'post_code', 'district_id', 'gender',
            'has_disability', 'receives_allowance', 'has_health_insurance',
            'nominee_first_name', 'nominee_middle_name_display', 'nominee_last_name',
            'nominee_gender', 'nominee_zanid', 'nominee_rel_benf',
            'nominee_house_street', 'nominee_shehia',
            'nominee_post_code_display', 'nominee_region_display', 'nominee_district_display',
            'id_type_1', 'id_number_1', 'id_type_2', 'id_number_2',
            'payment_mode', 'mobile_wallet', 'bank_name', 'account_num', 'account_name',
            'other_pension', 'scheme_name',
            'address_display', 'shehia_display',
        ]
        for record in self:
            pd = record.partner_data
            if not pd:
                for f in all_fields:
                    record[f] = False
                continue
            
            if isinstance(pd, str):
                try: pd = json.loads(pd)
                except: pd = {}
            
            # Post Code
            # 0. Core Details
            record.zan_id = pd.get('zan_id') or pd.get('benf_zan_id')
            record.given_name = pd.get('given_name')
            record.middle_name = pd.get('middle_name')
            record.family_name = pd.get('family_name')
            record.phone = pd.get('phone') or pd.get('mobile')
            
            bday = pd.get('birthdate')
            if bday and isinstance(bday, str):
                try: record.birthdate_date = fields.Date.from_string(bday[:10])
                except: record.birthdate_date = False
            else:
                record.birthdate_date = False
                
            reg_date = pd.get('registration_date')
            if reg_date and isinstance(reg_date, str):
                try: record.registration_date = fields.Date.from_string(reg_date[:10])
                except: record.registration_date = False
            else:
                record.registration_date = False

            record.post_code = pd.get('post_code') or pd.get('benf_post_code')

            # 1. Region Mapping (Robust Search)
            # Prioritize 'region' (portal) over 'region_id' (stale backend)
            reg_val = pd.get('region') or pd.get('region_id') or pd.get('region_name') or pd.get('state_name') or pd.get('state')
            reg_code = False
            
            reg = False
            if isinstance(reg_val, int):
                reg = self.env['g2p.region'].sudo().browse(reg_val)
                if not reg.exists(): reg = False
            elif isinstance(reg_val, str):
                reg_val = reg_val.strip()
                reg = self.env['g2p.region'].sudo().search([('name', '=ilike', reg_val)], limit=1)
            
            if reg:
                record.region_id = reg
                reg_code = reg.code
            else:
                record.region_id = False

            record.gender = pd.get('gender')
            
            # 2. District Mapping (Robust Search)
            dist_val = pd.get('district') or pd.get('district_id') or pd.get('benf_district')
            
            # If not found in standard keys, try dynamic region-specific keys (for legacy data)
            if not dist_val and record.region_id:
                reg_code = record.region_id.code or ''
                if reg_code:
                    dynamic_key = f"{reg_code}_district"
                    dist_val = pd.get(dynamic_key)
                    if not dist_val:
                        for dk in [f"{reg_code}District", f"{reg_code}_dist"]:
                            if pd.get(dk):
                                dist_val = pd[dk]
                                break
            
            dist = False
            if dist_val:
                search_params = [
                    '|', ('id', '=', dist_val if isinstance(dist_val, int) else 0),
                    ('name', '=ilike', dist_val if isinstance(dist_val, str) else '')
                ]
                if record.region_id:
                    extended_domain = ['&'] + search_params + [('province_id', '=', record.region_id.id)]
                    dist = self.env['g2p.district'].sudo().search(extended_domain, limit=1)
                
                if not dist:
                    dist = self.env['g2p.district'].sudo().search(search_params, limit=1)
                    
            record.district_id = dist
            
            # Additional Information
            record.has_disability = pd.get('disability') or pd.get('has_disability')
            record.receives_allowance = pd.get('is_receiving_allowance')
            record.has_health_insurance = pd.get('has_health_insurance')

            # Multi-choice mappings for readability
            GENDER_MAP = {'female': 'Female', 'male': 'Male', 'other': 'Other'}
            # Multi-choice mappings for readability
            GENDER_MAP = {'female': 'Female', 'male': 'Male', 'other': 'Other'}
            PAYMENT_MAP = {
                'bank': 'Bank',
                'bank_transfer': 'Bank Transfer',
                'mobile_wallet': 'Mobile Wallet',
                'cash_pickup': 'Cash Pickup',
                'ezypesa': 'EzyPesa',
                'tigopesa': 'Tigo Pesa',
                'airtel_money': 'Airtel Money',
                'mpesa': 'M-Pesa',
                'halopesa': 'Halo Pesa'
            }

            # Nominee Info (User-readable location mapping)
            nom_reg_val = pd.get('nominee_region')
            nom_dist_val = pd.get('nominee_district')
            
            # Map Nominee Region slug to name
            nom_reg_obj = False
            if nom_reg_val:
                search_val = nom_reg_val.replace('_', ' ') if isinstance(nom_reg_val, str) else nom_reg_val
                nom_reg_obj = self.env['g2p.region'].sudo().search([
                    '|', ('id', '=', nom_reg_val if isinstance(nom_reg_val, int) else 0),
                    ('name', '=ilike', search_val)
                ], limit=1)
            record.nominee_region_display = nom_reg_obj.name if nom_reg_obj else nom_reg_val
            
            # Map Nominee District slug to name
            nom_dist_obj = False
            if nom_dist_val:
                search_val = nom_dist_val.replace('_', ' ') if isinstance(nom_dist_val, str) else nom_dist_val
                domain = [
                    '|', ('id', '=', nom_dist_val if isinstance(nom_dist_val, int) else 0),
                    ('name', '=ilike', search_val)
                ]
                if nom_reg_obj:
                    domain = ['&'] + domain + [('province_id', '=', nom_reg_obj.id)]
                nom_dist_obj = self.env['g2p.district'].sudo().search(domain, limit=1)
                
                if not nom_dist_obj: # Fallback without region if first search failed
                    nom_dist_obj = self.env['g2p.district'].sudo().search([
                        '|', ('id', '=', nom_dist_val if isinstance(nom_dist_val, int) else 0),
                        ('name', '=ilike', search_val)
                    ], limit=1)
                    
            record.nominee_district_display = nom_dist_obj.name if nom_dist_obj else nom_dist_val

            record.nominee_first_name = pd.get('nominee_first_name')
            record.nominee_middle_name_display = pd.get('nominee_middle_name')
            record.nominee_last_name = pd.get('nominee_last_name')
            
            nom_gender_val = pd.get('nominee_gender')
            record.nominee_gender = GENDER_MAP.get(nom_gender_val, nom_gender_val)
            
            record.nominee_zanid = pd.get('nominee_zanid')
            record.nominee_rel_benf = pd.get('nominee_rel_benf')
            record.nominee_house_street = pd.get('nominee_house_street')
            record.nominee_shehia = pd.get('nominee_shehia')
            record.nominee_post_code_display = pd.get('nominee_post_code')

            # IDs
            record.id_type_1 = 'Zanzibar ID'
            record.id_number_1 = pd.get('benf_zan_id')
            record.id_type_2 = 'Nominee Zanzibar ID'
            record.id_number_2 = pd.get('nominee_zanid')

            # Payment Mode (Keys only - Odoo UI handles labels)
            record.payment_mode = pd.get('payment_mode')
            
            # Note: mobile_wallet field in model is used for the phone number
            # in Zanzibar context, whereas PAYMENT_MAP had some provider names.
            # We keep it as is from the JSON.
            record.mobile_wallet = pd.get('mobile_wallet')
            
            record.bank_name = pd.get('bank_name')
            record.account_num = pd.get('account_num')
            record.account_name = pd.get('account_name')

            # Pension
            record.other_pension = pd.get('other_pension')
            record.scheme_name = pd.get('scheme_name')

            # Address
            record.address_display = pd.get('address') or pd.get('street')
            record.shehia_display = pd.get('street2')

    def _inverse_mapped_fields(self):
        """Sync UI changes back to partner_data JSON blob."""
        for record in self:
            record._update_partner_data_from_fields()

    @api.model_create_multi
    def create(self, vals_list):
        saved_partner_data = []
        for vals in vals_list:
            saved_partner_data.append(vals.get('partner_data'))
            if not vals.get('partner_data'):
                vals['partner_data'] = '{}'
            # Ensure all fields expected by base draft.record.create() are present to prevent KeyError
            for field in [
                'given_name', 'family_name', 'middle_name', 'addl_name', 
                'gender', 'region', 'region_id', 'phone', 'zan_id'
            ]:
                if field not in vals:
                    vals[field] = False
        
        records = super().create(vals_list)
        
        for record, original_pd in zip(records, saved_partner_data):
            if original_pd:
                try:
                    original_data = json.loads(original_pd) if isinstance(original_pd, str) else (original_pd or {})
                    try:
                        base_data = json.loads(record.partner_data) if isinstance(record.partner_data, str) else (record.partner_data or {})
                    except:
                        base_data = {}
                    merged = {**base_data, **original_data}
                    merged["imported_record_state"] = "draft"
                    # Suppress tracking during initial creation setup to avoid "None -> Value" logs
                    record.sudo().with_context(mail_notrack=True).write({'partner_data': json.dumps(merged)})
                except:
                    pass
            else:
                # Suppress tracking during initial creation setup to avoid "None -> Value" logs
                record.with_context(mail_notrack=True)._update_partner_data_from_fields()
        return records

    def _clean_null_values(self, data):
        """Recursively convert None/False values to empty strings to prevent JS crashes."""
        if isinstance(data, dict):
            return {k: self._clean_null_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_null_values(v) for v in data]
        elif data is None or data is False:
            return ""
        return data

    def read(self, fields=None, load='_classic_read'):
        result = super().read(fields=fields, load=load)
        for record in result:
            if 'partner_data' in record:
                pd = record['partner_data']
                if not pd:
                    record['partner_data'] = {}
                elif isinstance(pd, str):
                    try:
                        val = json.loads(pd)
                        record['partner_data'] = self._clean_null_values(val) if val is not None else {}
                    except:
                        record['partner_data'] = {}
                elif isinstance(pd, (dict, list)):
                    record['partner_data'] = self._clean_null_values(pd)
        return result

    def web_read(self, specification):
        """Override for Odoo 17 form views to ensure partner_data is always a valid dict."""
        result = super().web_read(specification)
        # Odoo 17 web_read can return a list (standard) or a dict {'rows': [...]} in some contexts
        rows = result.get('rows', []) if isinstance(result, dict) else (result if isinstance(result, list) else [])
        for record in rows:
            if 'partner_data' in record:
                pd = record['partner_data']
                if not pd:
                    record['partner_data'] = {}
                elif isinstance(pd, str):
                    try:
                        val = json.loads(pd)
                        record['partner_data'] = self._clean_null_values(val) if val is not None else {}
                    except:
                        record['partner_data'] = {}
                elif isinstance(pd, (dict, list)):
                    record['partner_data'] = self._clean_null_values(pd)
        return result

    def write(self, vals):
        res = super().write(vals)
        if 'partner_data' not in vals:
            tracked_fields = [
                'zan_id', 'birthdate_date', 'registration_date', 'name', 'phone',
                'gender', 'nominee_mobile', 'post_code', 'district_id',
                'has_disability', 'receives_allowance', 'has_health_insurance',
                'nominee_first_name', 'nominee_middle_name_display', 'nominee_last_name',
                'nominee_gender', 'nominee_zanid', 'nominee_rel_benf',
                'nominee_house_street', 'nominee_shehia',
                'nominee_post_code_display', 'nominee_region_display', 'nominee_district_display',
                'payment_mode', 'mobile_wallet', 'bank_name', 'account_num', 'account_name',
                'other_pension', 'scheme_name', 'address_display', 'shehia_display',
            ]
            if any(f in vals for f in tracked_fields):
                for record in self:
                    record._update_partner_data_from_fields()
        return res

    def _update_partner_data_from_fields(self):
        self.ensure_one()
        raw_data = self.partner_data
        try:
            partner_data = json.loads(raw_data) if isinstance(raw_data, str) else (raw_data or {})
        except:
            partner_data = {}
        
        # Core fields
        partner_data["benf_zan_id"] = self.zan_id
        partner_data["birthdate"] = self.birthdate_date.isoformat() if self.birthdate_date else False
        partner_data["registration_date"] = self.registration_date.isoformat() if self.registration_date else False
        partner_data["name"] = self.name.upper() if self.name else False
        partner_data["given_name"] = self.given_name
        partner_data["family_name"] = self.family_name
        partner_data["middle_name"] = self.middle_name
        partner_data["phone"] = self.phone
        partner_data["nominee_mobile"] = self.nominee_mobile
        partner_data["post_code"] = self.post_code
        
        # Location: Use integer IDs for portal compatibility
        partner_data["region"] = self.region_id.id if self.region_id else False
        partner_data["region_id"] = self.region_id.id if self.region_id else False
        partner_data["region_name"] = self.region_id.name if self.region_id else False
        
        partner_data["district"] = self.district_id.id if self.district_id else False
        partner_data["district_id"] = self.district_id.id if self.district_id else False
        partner_data["district_name"] = self.district_id.name if self.district_id else False
        
        partner_data["disability"] = self.has_disability
        partner_data["is_receiving_allowance"] = self.receives_allowance
        partner_data["has_health_insurance"] = self.has_health_insurance
        partner_data["gender"] = self.gender

        # Nominee fields
        partner_data["nominee_first_name"] = self.nominee_first_name
        partner_data["nominee_middle_name"] = self.nominee_middle_name_display
        partner_data["nominee_last_name"] = self.nominee_last_name
        partner_data["nominee_gender"] = self.nominee_gender
        partner_data["nominee_zanid"] = self.nominee_zanid
        partner_data["nominee_rel_benf"] = self.nominee_rel_benf
        partner_data["nominee_house_street"] = self.nominee_house_street
        partner_data["nominee_shehia"] = self.nominee_shehia
        partner_data["nominee_post_code"] = self.nominee_post_code_display
        partner_data["nominee_region"] = self.nominee_region_display
        partner_data["nominee_district"] = self.nominee_district_display

        # Payment fields
        partner_data["payment_mode"] = self.payment_mode
        if self.payment_mode == 'mobile_wallet':
            partner_data["mobile_wallet"] = self.mobile_wallet
            # Clear bank fields
            partner_data["bank_name"] = ""
            partner_data["account_num"] = ""
            partner_data["account_name"] = ""
        elif self.payment_mode in ['bank', 'bank_transfer']:
            partner_data["bank_name"] = self.bank_name
            partner_data["account_num"] = self.account_num
            partner_data["account_name"] = self.account_name
            # Clear wallet fields
            partner_data["mobile_wallet"] = ""
        else:
            # Clear all if no mode or other mode selected
            partner_data["mobile_wallet"] = ""
            partner_data["bank_name"] = ""
            partner_data["account_num"] = ""
            partner_data["account_name"] = ""

        # Pension fields
        partner_data["other_pension"] = self.other_pension
        if self.other_pension == 'yes':
            partner_data["scheme_name"] = self.scheme_name
        else:
            partner_data["scheme_name"] = ""

        # Address
        partner_data["address"] = self.address_display
        partner_data["street2"] = self.shehia_display
        # Clean up any None/False values to prevent JS widget crashes (Object.entries(null) errors)
        final_pd = {}
        for k, v in partner_data.items():
            if v is False or v is None:
                final_pd[k] = ""
            else:
                final_pd[k] = v

        self.sudo().partner_data = json.dumps(final_pd)

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
            and self.env[f["relation"]].sudo().browse(v).exists(),
            "many2many": lambda v, f: isinstance(v, list)
            and all(self.env[f["relation"]].sudo().browse(x[1]).exists() for x in v),
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

        # --- Handle Field Officer (find or create) ---
        creator = self.create_uid
        if creator and creator.partner_id:
            enumerator_model = self.env["g2p.enumerator"].sudo()
            # De-duplication: check by name or EID
            enumerator = enumerator_model.search([
                "|", ("name", "=", creator.name),
                ("enumerator_user_id", "=", creator.partner_id.eid)
            ], limit=1)
            
            if not enumerator and creator.partner_id.eid:
                enumerator = enumerator_model.create({
                    "name": creator.name,
                    "enumerator_user_id": creator.partner_id.eid,
                    "data_collection_date": self.registration_date or fields.Date.today(),
                })
            
            if enumerator:
                partner.sudo().write({"enumerator_id": enumerator.id})

        # --- Create phone number records ---
        country_tz = self.env.ref("base.tz", raise_if_not_found=False)
        country_id = country_tz.id if country_tz else False

        benf_phone = partner_data.get("phone") or partner_data.get("mobile") or self.phone
        if benf_phone:
            self.env["g2p.phone.number"].sudo().create({
                "partner_id": partner.id,
                "phone_no": benf_phone,
                "phone_owner": "beneficiary",
                "country_id": country_id,
            })

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
            partner.sudo().write({'draft_record_id': self.id})
        
        self.write({"state": "published"})
        return partner

    def action_open_wizard_view_only(self):
        self.ensure_one()
        view_id = self.env.ref("g2p_zanzibar_draft_publish.view_draft_record_readonly_form").id
        return {
            "name": "Record Data",
            "type": "ir.actions.act_window",
            "res_model": "draft.record",
            "res_id": self.id,
            "view_mode": "form",
            "view_id": view_id,
            "target": "current",
        }
