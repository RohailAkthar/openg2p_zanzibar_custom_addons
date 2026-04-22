import logging
import json
import re
import base64
import requests
from datetime import datetime, date
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

# Simple test route outside of class to test basic routing
@http.route("/zanzibar_test", type="json", auth="user", csrf=False)
def simple_test():
    return {"status": "SUCCESS", "message": "Zanzibar module is loaded!"}

from odoo.addons.g2p_social_registry_model.controllers.main import G2PSocialRegistryModel

class MockPhone:
    def __init__(self, no):
        self.phone_no = no

class MockID:
    def __init__(self, type_id, val):
        self.id_type = type_id
        self.value = val

class MockPartner:
    def __init__(self, draft_rec, env):
        self._draft = draft_rec
        self.env = env
        self._data = {}
        if draft_rec.partner_data:
            try:
                self._data = json.loads(draft_rec.partner_data)
            except Exception as e:
                _logger.error("JSON parse error: %s", e)

        self.id = draft_rec.id
        self.name = draft_rec.name or ''
        self.given_name = draft_rec.given_name or ''
        self.family_name = draft_rec.family_name or ''
        self.middle_name = draft_rec.middle_name or ''
        self.gender = draft_rec.gender or False
        self.birthdate = draft_rec.birthdate_date or False
        self.state = draft_rec.state or 'draft'
        
        # Build mock relations required by QWeb templates
        # Handle both IDs (from portal updates) and Names (from old imports)
        reg_val = self._data.get('region') or self._data.get('region_id')
        self.region = env['g2p.region'].sudo()
        if isinstance(reg_val, int):
            self.region = self.region.browse(reg_val)
        elif isinstance(reg_val, str):
            self.region = self.region.search([('name', '=ilike', reg_val.strip())], limit=1)
        if not self.region.exists():
            self.region = env['g2p.region'].sudo()
            
        dist_val = self._data.get('district') or self._data.get('district_id')
        self.district = env['g2p.district'].sudo()
        if isinstance(dist_val, int):
            self.district = self.district.browse(dist_val)
        elif isinstance(dist_val, str):
            # District search depends on region if available
            domain = [('name', '=ilike', dist_val.strip())]
            if self.region:
                domain = ['&'] + domain + [('province_id', '=', self.region.id)]
            self.district = self.district.search(domain, limit=1)
        if not self.district.exists():
            self.district = env['g2p.district'].sudo()
            
        # Robust phone handling: Template uses phone_number_ids and beneficiary_phone_number_ids
        mobile = self._data.get('phone') or self._data.get('mobile') or draft_rec.phone or ''
        self.phone = mobile
        self.phone_number_ids = [MockPhone(mobile)] if mobile else []
        self.beneficiary_phone_number_ids = [MockPhone(mobile)] if mobile else []
        
        self.reg_ids = []
        zan_id_str = self._data.get('zan_id') or self._data.get('benf_zan_id') or draft_rec.zan_id
        if zan_id_str:
            id_type = env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
            if id_type:
                self.reg_ids.append(MockID(id_type, zan_id_str))
                
        # Used directly by snippet
        self.benf_zan_id = zan_id_str or ''
        
        # Explicit fields for template compatibility
        self.active = True
        self.write_date = draft_rec.write_date or fields.Datetime.now()
        self.address = self._data.get('address') or ''
        self.street = self._data.get('street') or ''
        self.street2 = self._data.get('street2') or ''
        self.benf_post_code = self._data.get('benf_post_code') or ''
        self.disability = self._data.get('disability') or ''
        self.is_receiving_allowance = self._data.get('is_receiving_allowance') or ''
        self.has_health_insurance = self._data.get('has_health_insurance') or ''

        # Nominee address fields
        self.nominee_region = self._data.get('nominee_region', False)
        self.nominee_district = self._data.get('nominee_district', False)

        # Image fields: image_data_uri() expects bytes, not str
        # Convert base64 strings from JSON to bytes for template compatibility
        for img_field in ('image_1920', 'beneficiary_image', 'nominee_image', 'zan_image'):
            img_val = self._data.get(img_field)
            if img_val and isinstance(img_val, str):
                setattr(self, img_field, img_val.encode('utf-8'))
            else:
                setattr(self, img_field, img_val)

    def __getattr__(self, name):
        # Fallback to data dictionary
        return self._data.get(name, False)
        
    def __getitem__(self, key):
        # Make object subscriptable
        if hasattr(self, key):
            return getattr(self, key)
        elif key in self._data:
            return self._data[key]
        else:
            return False
            
    def __bool__(self):
        return True


class PartnerRow:
    def __init__(self, partner):
        self._partner = partner
        self.id = partner.id
        self.active = partner.active
        self.write_date = partner.write_date
        self.state = "published"

        self.state = "published"

        # Robust retrieval of Zanzibar ID with fallbacks
        zan_id = getattr(partner, 'benf_zan_id', False)
        if not zan_id:
            zanzibar_id_rec = partner.reg_ids.filtered(lambda r: r.id_type.name == 'Zanzibar ID')
            zan_id = zanzibar_id_rec[0].value if zanzibar_id_rec else ''
        
        # Final fallback to original draft record if available via many2one link
        if not zan_id and hasattr(partner, 'draft_record_id') and partner.draft_record_id:
            zan_id = partner.draft_record_id.zan_id
            
        self.benf_zan_id = zan_id or ''

    def __getattr__(self, name):
        return getattr(self._partner, name)

    def __getitem__(self, key):
        return getattr(self._partner, key, False)

    def __bool__(self):
        return True

class ZanzibarPortalDraft(G2PSocialRegistryModel):

    @http.route("/portal/registration/zan_id_lookup", type="json", auth="user", csrf=False)
    def zan_id_lookup(self, zan_id):
        if not zan_id:
            return {"status": "ERROR", "message": "Zan ID is required"}

        # 1. Check in database (Mirror from main.py)
        id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
        if not id_type:
            return {"status": "ERROR", "message": "Zanzibar ID type not found in system"}

        # Check for any "active" (non-rejected) record in draft or published state
        active_rec = request.env['draft.record'].sudo().search([
            ('zan_id', '=', zan_id.strip()),
            ('state', '!=', 'rejected')
        ], limit=1)

        if active_rec:
            if active_rec.state == 'published':
                return {
                    "status": "ALREADY_EXISTS",
                    "message": "Beneficiary with this Zan ID already exists in the system."
                }
            else:
                return {
                    "status": "ALREADY_EXISTS_IN_DRAFT",
                    "message": "Beneficiary with this Zan ID already exists in Not Verified records."
                }

        # If no active draft found (all are rejected or none exist), 
        # check if there's a record in the registry
        reg_id = (
            request.env["g2p.reg.id"]
            .sudo()
            .search([("id_type", "=", id_type.id), ("value", "=", zan_id.strip())], limit=1)
        )

        if reg_id and reg_id.partner_id:
            # It's in the registry. Is it "Rejected"?
            # We treat it as rejected if an accompanying rejected draft exists
            # and we've already confirmed no active draft exists.
            has_rejected_draft = request.env['draft.record'].sudo().search([
                ('zan_id', '=', zan_id.strip()),
                ('state', '=', 'rejected')
            ], limit=1)

            if not has_rejected_draft:
                return {
                    "status": "ALREADY_EXISTS",
                    "message": "Beneficiary with this Zan ID already exists in the system."
                }

        # 3. Call External API (Mirror from main.py)
        try:
            url = "https://mock-api.credissuer.com/validate-zan"
            payload = {"zan_id": zan_id}
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                status = result.get("status")

                if status and status.lower() == "success":
                    api_data = result.get("data", {})
                    
                    street2 = api_data.get("ward_name", "")
                    
                    # Gender Lookup
                    gender_str = api_data.get("gender", "")
                    gender_val = ""
                    if gender_str:
                        domain = ['|', ('code', '=ilike', gender_str), ('value', '=ilike', gender_str)]
                        found = request.env["gender.type"].sudo().search(domain, limit=1)
                        if found:
                            gender_val = found.value
                        else:
                            if gender_str.lower() in ['female', 'f', 'woman']:
                                gender_val = 'female'
                            elif gender_str.lower() in ['male', 'm', 'man']:
                                gender_val = 'male'
                            else:
                                gender_val = gender_str
                    
                    data = {
                        "status": "SUCCESS",
                        "firstname": api_data.get("first_name", ""),
                        "lastname": api_data.get("surname", ""),
                        "middle_name": api_data.get("middle_name", ""),
                        "dob": api_data.get("dob", ""),
                        "gender": gender_val,
                        "mobile": api_data.get("mobile_number", ""),
                        "street": api_data.get("address", ""),
                        "street2": street2,
                        "benf_post_code": api_data.get("po_box", ""),
                    }

                    # Age Validation
                    dob_str = data.get("dob")
                    if dob_str:
                        try:
                            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                        except ValueError:
                            try:
                                dob = datetime.strptime(dob_str, "%d-%m-%Y").date()
                            except ValueError:
                                dob = None
                        
                        if dob:
                            today = date.today()
                            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                            if age < 69:
                                return {
                                    "status": "NOT_ELIGIBLE", 
                                    "message": f"The citizen is not eligible for ZUPS scheme!. Age is  {age}, but must be 69+."
                                }

                    return data
                else:
                    return {"status": "NOT_FOUND", "message": "Zan ID not found in external registry"}
            else:
                return {"status": "ERROR", "message": f"ZAN ID does not exist in eGAZ system, Please try with a Valid ZAN ID!"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    @http.route("/portal/registration/phone_lookup", type="json", auth="user", csrf=False)
    def phone_lookup(self, phone):
        if not phone:
            return {"status": "ERROR", "message": "Phone number is required"}

        # Clean phone number (remove spaces, dashes, etc.)
        clean_phone = "".join(char for char in phone if char.isdigit())

        # 1. Check in draft records via g2p.phone.number relationship
        # First find phone records, then check if they belong to draft records
        phone_records = (
            request.env["g2p.phone.number"]
            .sudo()
            .search([("phone_no", "=", clean_phone), ("phone_owner", "=", "beneficiary")])
        )

        for phone_rec in phone_records:
            # Check if this phone belongs to a draft record
            if phone_rec.partner_id and any(d.state != 'rejected' for d in phone_rec.partner_id.draft_record_ids):
                return {
                    "status": "ALREADY_EXISTS_IN_DRAFT",
                    "message": "Beneficiary with this phone number already exists in Not Verified records."
                }

        for phone_rec in phone_records:
            # Check if this phone belongs to a published partner with NO non-rejected draft records
            if phone_rec.partner_id and not any(d.state != 'rejected' for d in phone_rec.partner_id.draft_record_ids):
                # If there is a rejected draft, we allow it.
                # If there are NO drafts (e.g. direct import), we still block it as it's "in the system".
                if not any(d.state == 'rejected' for d in phone_rec.partner_id.draft_record_ids):
                    return {
                        "status": "ALREADY_EXISTS",
                        "message": "Beneficiary with this phone number already exists in the system."
                    }

        # 3. Return success if phone is available
        return {
            "status": "SUCCESS",
            "message": "Phone number is available for registration."
        }

    @http.route("/portal/registration/nominee_phone_lookup", type="json", auth="user", csrf=False)
    def nominee_phone_lookup(self, phone):
        if not phone:
            return {"status": "ERROR", "message": "Nominee phone number is required"}

        # Clean phone number (remove spaces, dashes, etc.)
        clean_phone = "".join(char for char in phone if char.isdigit())

        # Check in draft records via nominee_mobile field (ignore rejected)
        draft_records_with_nominee_phone = (
            request.env["draft.record"]
            .sudo()
            .search([("nominee_mobile", "=", clean_phone), ("state", "!=", "rejected")], limit=1)
        )

        if draft_records_with_nominee_phone:
            return {
                "status": "ALREADY_EXISTS_IN_DRAFT",
                "message": "Nominee with this phone number already exists in Not Verified records."
            }

        # Check in published partners via nominee_mobile field
        published_partners_with_nominee_phone = (
            request.env["res.partner"]
            .sudo()
            .search([("nominee_mobile", "=", clean_phone)], limit=1)
        )

        if published_partners_with_nominee_phone:
            # Check if there's an accompanying rejected draft
            has_rejected_draft = request.env['draft.record'].sudo().search([
                ('nominee_mobile', '=', clean_phone),
                ('state', '=', 'rejected')
            ], limit=1)

            if not has_rejected_draft:
                return {
                    "status": "ALREADY_EXISTS",
                    "message": "Nominee with this phone number already exists in the system."
                }

        return {
            "status": "SUCCESS",
            "message": "Nominee phone number is available for registration."
        }

    @http.route("/portal/registration/nominee_zan_id_lookup", type="json", auth="user", csrf=False)
    def nominee_zan_id_lookup(self, nominee_zanid):
        if not nominee_zanid:
            return {"status": "ERROR", "message": "Zan ID is required"}

        # 1. Check in database (Mirror from main.py)
        # id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Nominee Zanzibar ID")], limit=1)
        # ... (main.py version is commented out, so I'll follow that and jump to External API)

        # 2. Call External API (Mirror from main.py)
        try:
            response = requests.get("https://mocki.io/v1/4661e182-00d4-4f26-a450-e4e96a7cc075", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SUCCESS":
                    # Map Mock API fields to Nominee Fields (Mirror from main.py)
                    mapped_data = {
                        "status": "SUCCESS",
                        "message": "Found!",
                        "nominee_first_name": data.get("firstname", ""),
                        "nominee_last_name": data.get("lastname", ""),
                        "nominee_gender": data.get("gender", "").lower(),
                        "nominee_mobile": data.get("mobile", ""),
                        "nominee_house_street": data.get("street", ""),
                        "nominee_shehia": data.get("street2", ""),
                        "nominee_rel_benf": data.get("relationship", ""),
                        "nominee_region": data.get("region", ""),
                        "nominee_district": data.get("district", ""),
                        "nominee_post_code": data.get("postcode", ""),
                    }
                    return mapped_data
                else:
                    return {"status": "NOT_FOUND", "message": "Nominee Zan ID not found in external registry"}
            else:
                return {"status": "ERROR", "message": f"External API error: {response.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    @http.route(
        ["/portal/registration/group/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def group_create_submit(self, **kw):
        try:
            head_name = kw.get("name")
            
            # Mirror additional_data dict from main.py (lines 200-230)
            additional_data = {
                "name": head_name,
                "birthdate": kw.get("birthdate"),
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "address": kw.get("address"),
                # Social Status Information
                "num_preg_lact_women": int(kw.get("num_preg_lact_women", 0))
                if kw.get("num_preg_lact_women")
                else 0,
                "num_malnourished_children": int(kw.get("num_malnourished_children", 0))
                if kw.get("num_malnourished_children")
                else 0,
                "num_disabled": int(kw.get("num_disabled", 0)) if kw.get("num_disabled") else 0,
                "type_of_disability": kw.get("type_of_disability"),
                # Economic Status Information
                "caste_ethnic_group": kw.get("caste_ethnic_group"),
                "belong_to_protected_groups": kw.get("belong_to_protected_groups"),
                "other_vulnerable_status": kw.get("other_vulnerable_status"),
                "income_sources": kw.get("income_sources"),
                "annual_income": kw.get("annual_income", False),
                "owns_two_wheeler": kw.get("owns_two_wheeler"),
                "owns_three_wheeler": kw.get("owns_three_wheeler"),
                "owns_four_wheeler": kw.get("owns_four_wheeler"),
                "owns_cart": kw.get("owns_cart"),
                "land_ownership": kw.get("land_ownership"),
                "type_of_land_owned": kw.get("type_of_land_owned"),
                "land_size": float(kw.get("land_size", 0.0)) if kw.get("land_size") else 0.0,
                "owns_house": kw.get("owns_house"),
                "owns_livestock": kw.get("owns_livestock"),
            }

            # Mandatory flags for group draft
            partner_data = additional_data.copy()
            partner_data.update({
                "is_registrant": True,
                "is_group": True,
                "db_import": "yes",
                "user_id": request.env.user.id,
            })
            
            # Create the draft record for the group
            vals = {
                'name': head_name,
                'given_name': head_name.split(" ")[0] if head_name else "",
                'family_name': head_name.split(" ")[-1] if head_name else "",
                'registration_date': fields.Date.today(),
                'state': 'draft',
                'partner_data': json.dumps(partner_data),
            }
            request.env['draft.record'].sudo().create(vals)
            
            return request.redirect("/portal/registration/group")

        except Exception as e:
            _logger.exception("Error while submitting group registration: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": f"An error occurred: {str(e)}"},
            )

    @http.route("/portal/registration/individual", type="http", auth="user")
    def individual_list(self, **kw):
        self.check_roles("Agent")
        
        # Get draft records
        draft_records = request.env["draft.record"].sudo().search([
            ('state', 'in', ['draft', 'published', 'rejected'])
        ], order='write_date desc, id desc')
        
        # Get published partners (res.partner records that were created from drafts)
        # Check if draft_record_id field exists
        if 'draft_record_id' in request.env["res.partner"]._fields:
            published_partners = request.env["res.partner"].sudo().search([
                ('is_registrant', '=', True),
                ('is_group', '=', False),
                ('db_import', '=', 'yes'),
                ('draft_record_id', '!=', False),
            ], order='write_date desc, id desc')
        else:
            # Fallback for when field doesn't exist yet (during upgrade)
            published_partners = request.env["res.partner"].sudo().search([
                ('is_registrant', '=', True),
                ('is_group', '=', False),
                ('db_import', '=', 'yes'),
            ], order='write_date desc, id desc')
        
        # Combine both lists
        all_individuals = []
        
        # Add draft records
        for draft in draft_records:
            mock_partner = MockPartner(draft, request.env)
            all_individuals.append(mock_partner)
        
        # Add published partners
        for partner in published_partners:
            # Only show if the original draft record still exists (if field exists)
            show_partner = True
            if 'draft_record_id' in request.env["res.partner"]._fields:
                if partner.draft_record_id and partner.draft_record_id.exists():
                    show_partner = True
                else:
                    show_partner = False
            
            if show_partner:
                all_individuals.append(PartnerRow(partner))
            
        return request.render("g2p_registration_portal_base.individual_list", {"individual": all_individuals})

    def _get_reg_ids_command(self, kw):
        reg_ids = []
        if kw.get("benf_zan_id"):
            id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Zanzibar ID")], limit=1)
            if id_type:
                reg_ids.append((0, 0, {
                    "id_type": id_type.id,
                    "value": kw.get("benf_zan_id"),
                    "status": "valid",
                }))
        if kw.get("nominee_zanid"):
            id_type = request.env["g2p.id.type"].sudo().search([("name", "=", "Nominee Zanzibar ID")], limit=1)
            if id_type:
                reg_ids.append((0, 0, {
                    "id_type": id_type.id,
                    "value": kw.get("nominee_zanid"),
                    "status": "valid",
                }))
        return reg_ids

    def _validate_tz_phone(self, phone):
        """Validate Tanzania phone number format.
        After stripping +255/255/0 prefix, the local number must start with 6 or 7
        and be exactly 9 digits. Returns error message or None if valid.
        """
        if not phone:
            return None  # Empty phone is allowed (not required)
        # Strip common prefixes to get local number
        local = phone
        if local.startswith('+255'):
            local = local[4:]
        elif local.startswith('255'):
            local = local[3:]
        elif local.startswith('0'):
            local = local[1:]
        # Validate: must be 9 digits starting with 6 or 7
        if local and not re.match(r'^[67][0-9]{8}$', local):
            return "Phone number must start with 6 or 7 after +255 and be 9 digits"
        return None

    def _validate_id_type(self, id_type_name, value):
        """Validate an ID value against the regex pattern defined in the ID Type configuration.
        Returns error message or None if valid.
        """
        if not value:
            return None
        id_type = request.env["g2p.id.type"].sudo().search([("name", "=", id_type_name)], limit=1)
        if id_type and id_type.id_validation:
            if not re.match(id_type.id_validation, value):
                return f"Invalid format for {id_type_name}. Please match the required pattern."
        return None

    @http.route(
        ["/portal/registration/individual/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def individual_create_submit(self, **kw):
        try:
            # Validate phone numbers before processing
            phone_error = self._validate_tz_phone(kw.get("mobile"))
            if phone_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Beneficiary Mobile: {phone_error}"},
                )
            nominee_phone_error = self._validate_tz_phone(kw.get("nominee_mobile"))
            if nominee_phone_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Nominee Mobile: {nominee_phone_error}"},
                )

            # Validate IDs before processing
            zan_id_error = self._validate_id_type("Zanzibar ID", kw.get("benf_zan_id"))
            if zan_id_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Beneficiary Zan ID: {zan_id_error}"},
                )
            nominee_zan_id_error = self._validate_id_type("Nominee Zanzibar ID", kw.get("nominee_zanid"))
            if nominee_zan_id_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Nominee Zan ID: {nominee_zan_id_error}"},
                )

            user = request.env.user
            # Name construction logic from main.py
            name = ""
            if kw.get("family_name"):
                name += kw.get("family_name") + ", "
            if kw.get("given_name"):
                name += kw.get("given_name") + " "
            if kw.get("middle_name"):
                name += kw.get("middle_name") + " "
            if kw.get("addl_name"):
                name += kw.get("addl_name") + " "
            
            if kw.get("birthdate") == "":
                birthdate = False
            else:
                birthdate = kw.get("birthdate")

            # Mirror data dict from main.py (lines 481-534)
            data = {
                "given_name": kw.get("given_name"),
                "middle_name": kw.get("middle_name"),
                "addl_name": kw.get("addl_name"),
                "family_name": kw.get("family_name"),
                "name": name.strip(),
                "birthdate": birthdate,
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "user_id": user.id,
                "is_registrant": True,
                "is_group": False,
                # Additional fields
                "address": ", ".join(filter(None, [kw.get("street"), kw.get("street2")])),
                "occupation": kw.get("occupation"),
                "income": float(kw.get("income", 0.0)) if kw.get("income") else 0.0,
                "education_level": kw.get("education_level"),
                "employment_status": kw.get("employment_status"),
                "marital_status": kw.get("marital_status"),
                # Nominee Info
                "nominee_first_name": kw.get("nominee_first_name"),
                "nominee_middle_name": kw.get("nominee_middle_name"),
                "nominee_last_name": kw.get("nominee_last_name"),
                "nominee_mobile": kw.get("nominee_mobile"),
                "nominee_gender": kw.get("nominee_gender"),
                "nominee_zanid": kw.get("nominee_zanid"),
                "nominee_rel_benf": kw.get("nominee_rel_benf"),
                "nominee_house_street": kw.get("nominee_house_street"),
                "nominee_shehia": kw.get("nominee_shehia"),
                "nominee_region": kw.get("nominee_region"),
                "nominee_district": kw.get("nominee_district"),
                "nominee_post_code": kw.get("nominee_post_code"),
                # Pension Info
                "other_pension": kw.get("other_pension"),
                "scheme_name": kw.get("scheme_name"),
                # Payment Info
                "payment_mode": kw.get("payment_mode"),
                "bank_name": kw.get("bank_name"),
                "account_num": kw.get("account_num"),
                "account_name": kw.get("account_name"),
                "mobile_wallet": kw.get("mobile_wallet"),
                # New Fields
                "street": kw.get("street"),
                "street2": kw.get("street2"),
                "region": int(kw.get("region")) if kw.get("region") else False,
                "district": int(kw.get("district")) if kw.get("district") else False,
                "benf_post_code": kw.get("benf_post_code"),
                # "benf_zan_id" removed (stored in reg_ids)
                "disability": kw.get("disability"),
                "is_receiving_allowance": kw.get("is_receiving_allowance"),
                "has_health_insurance": kw.get("has_health_insurance"),
            }

            # Store phone numbers as plain strings only (ORM records created on publish)
            if kw.get("mobile"):
                data["phone"] = kw.get("mobile")
            if kw.get("nominee_mobile"):
                data["nominee_mobile"] = kw.get("nominee_mobile")

            # Store IDs as plain strings only (ORM records created on publish)
            if kw.get("benf_zan_id"):
                data["benf_zan_id"] = kw.get("benf_zan_id")
            if kw.get("nominee_zanid"):
                data["nominee_zanid"] = kw.get("nominee_zanid")

            # Handle images (Mirror from main.py)
            if kw.get("nominee_image"):
                data["nominee_image"] = base64.b64encode(kw.get("nominee_image").read()).decode('utf-8')
            if kw.get("zan_image"):
                data["zan_image"] = base64.b64encode(kw.get("zan_image").read()).decode('utf-8')
            if kw.get("beneficiary_image"):
                image_data = base64.b64encode(kw.get("beneficiary_image").read()).decode('utf-8')
                data["image_1920"] = image_data
                data["beneficiary_image"] = image_data # Mirroring the sync in update_individual_submit

            # Create the draft record
            vals = {
                'given_name': kw.get('given_name'),
                'middle_name': kw.get('middle_name'),
                'family_name': kw.get('family_name'),
                'addl_name': kw.get('addl_name'),
                'zan_id': kw.get('benf_zan_id'),
                'birthdate_date': birthdate,
                'registration_date': fields.Date.today(),
                'gender': kw.get('gender'),
                'phone': kw.get('mobile'),
                'nominee_mobile': kw.get('nominee_mobile'),
                'state': 'draft',
                'name': name.strip(),
                'partner_data': json.dumps(data),
            }
            request.env['draft.record'].sudo().create(vals)
            return request.redirect("/portal/registration/individual")
        except Exception as e:
            _logger.exception("Error while submitting individual registration: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": f"Error while submitting individual registration: {str(e)}"},
            )

    @http.route(["/portal/registration/individual/update/<int:_id>"], type="http", auth="user", csrf=False)
    def indvidual_update(self, _id, **kw):
        self.check_roles("Agent")
        try:
            gender = request.env["gender.type"].sudo().search([])
            regions = request.env["g2p.region"].sudo().search([])
            districts = request.env["g2p.district"].sudo().search([])
            id_types = request.env["g2p.id.type"].sudo().search([])
            
            beneficiary = request.env["draft.record"].sudo().browse(_id).exists()
            if not beneficiary:
                return super().indvidual_update(_id, **kw)

            if beneficiary.state == "published":
                return request.redirect(f"/portal/registration/individual/view/{_id}")

            mock_partner = MockPartner(beneficiary, request.env)

            return request.render("g2p_registration_portal_base.individual_update_form_template", {
                "beneficiary": mock_partner,
                "gender": gender,
                "regions": regions,
                "districts": districts,
                "id_types": id_types,
            })
        except Exception as e:
            _logger.exception("Error loading individual update view: %s", str(e))
            return request.render("g2p_registration_portal_base.error_template", {
                "error_message": "An error occurred while loading the view: " + str(e)
            })

    @http.route(
        "/portal/registration/individual/update/submit",
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def update_individual_submit(self, **kw):
        try:
            # Validate phone numbers before processing
            phone_error = self._validate_tz_phone(kw.get("mobile"))
            if phone_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Beneficiary Mobile: {phone_error}"},
                )
            nominee_phone_error = self._validate_tz_phone(kw.get("nominee_mobile"))
            if nominee_phone_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Nominee Mobile: {nominee_phone_error}"},
                )

            # Validate IDs before processing
            zan_id_error = self._validate_id_type("Zanzibar ID", kw.get("benf_zan_id"))
            if zan_id_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Beneficiary Zan ID: {zan_id_error}"},
                )
            nominee_zan_id_error = self._validate_id_type("Nominee Zanzibar ID", kw.get("nominee_zanid"))
            if nominee_zan_id_error:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": f"Nominee Zan ID: {nominee_zan_id_error}"},
                )

            draft_id = kw.get("group_id")
            if not draft_id:
                # Fallback to base class if no draft_id (though in this module it should be draft_id)
                return super().update_individual_submit(**kw)

            draft = request.env["draft.record"].sudo().browse(int(draft_id)).exists()
            if not draft:
                return super().update_individual_submit(**kw)

            if draft.state == "published":
                return request.redirect(f"/portal/registration/individual/view/{draft.id}")

            try:
                current_data = json.loads(draft.partner_data or '{}')
            except:
                current_data = {}
            
            def normalize_space(text):
                if not isinstance(text, str):
                    return text
                return " ".join(text.split()).strip()

            # Mirror field_map from main.py (lines 582-617)
            field_map = {
                "given_name": "given_name",
                "middle_name": "middle_name",
                "addl_name": "addl_name",
                "family_name": "family_name",
                "gender": "gender",
                "email": "email",
                "occupation": "occupation",
                "education_level": "education_level",
                "employment_status": "employment_status",
                "marital_status": "marital_status",
                "nominee_first_name": "nominee_first_name",
                "nominee_middle_name": "nominee_middle_name",
                "nominee_last_name": "nominee_last_name",
                "nominee_mobile": "nominee_mobile",
                "nominee_gender": "nominee_gender",
                "nominee_zanid": "nominee_zanid",
                "nominee_rel_benf": "nominee_rel_benf",
                "nominee_house_street": "nominee_house_street",
                "nominee_shehia": "nominee_shehia",
                "nominee_region": "nominee_region",
                "nominee_district": "nominee_district",
                "nominee_post_code": "nominee_post_code",
                "other_pension": "other_pension",
                "scheme_name": "scheme_name",
                "payment_mode": "payment_mode",
                "bank_name": "bank_name",
                "account_num": "account_num",
                "account_name": "account_name",
                "mobile_wallet": "mobile_wallet",
                "street": "street",
                "street2": "street2",
                "benf_post_code": "benf_post_code",
                "disability": "disability",
                "is_receiving_allowance": "is_receiving_allowance",
                "has_health_insurance": "has_health_insurance",
            }

            vals = current_data.copy()
            for kw_key, val_key in field_map.items():
                if kw_key in kw:
                    vals[val_key] = normalize_space(kw.get(kw_key))

            # Special handling for birthdate
            if "birthdate" in kw:
                vals["birthdate"] = kw.get("birthdate") if kw.get("birthdate") != "" else False

            # Special handling for address
            street = kw.get("street") if "street" in kw else (current_data.get("street") or "")
            street2 = kw.get("street2") if "street2" in kw else (current_data.get("street2") or "")
            vals["address"] = ", ".join(filter(None, [street, street2]))

            # Numeric fields
            if "income" in kw:
                try: vals["income"] = float(kw.get("income", 0.0))
                except: pass

            # Mandatory relational fields
            if "region" in kw:
                try: 
                    reg_id = int(kw.get("region")) if kw.get("region") else False
                    vals["region"] = reg_id
                    vals["region_id"] = reg_id
                except: pass
            if "district" in kw:
                try: 
                    dist_id = int(kw.get("district")) if kw.get("district") else False
                    vals["district"] = dist_id
                    vals["district_id"] = dist_id
                except: pass

            # Extra specific fields
            if "disability" in kw: vals["disability"] = kw.get("disability")
            if "is_receiving_allowance" in kw: vals["is_receiving_allowance"] = kw.get("is_receiving_allowance")
            if "has_health_insurance" in kw: vals["has_health_insurance"] = kw.get("has_health_insurance")
            if "benf_post_code" in kw: vals["benf_post_code"] = kw.get("benf_post_code")
            if "street" in kw: vals["street"] = kw.get("street")
            if "street2" in kw: vals["street2"] = kw.get("street2")
            
            # Combine address
            if "street" in kw or "street2" in kw:
                vals["address"] = ", ".join(filter(None, [kw.get("street"), kw.get("street2")]))

            # Name construction
            f_name = kw.get("family_name") if "family_name" in kw else (current_data.get("family_name") or "")
            g_name = kw.get("given_name") if "given_name" in kw else (current_data.get("given_name") or "")
            m_name = kw.get("middle_name") if "middle_name" in kw else (current_data.get("middle_name") or "")
            a_name = kw.get("addl_name") if "addl_name" in kw else (current_data.get("addl_name") or "")
            
            new_parts = []
            if f_name: new_parts.append(f_name + ",")
            if g_name: new_parts.append(g_name)
            if m_name: new_parts.append(m_name)
            if a_name: new_parts.append(a_name)
            vals["name"] = " ".join(" ".join(new_parts).split()).strip()

            # Store phone numbers as plain strings only (ORM records created on publish)
            if kw.get("mobile"):
                vals["phone"] = normalize_space(kw.get("mobile"))
            if kw.get("nominee_mobile"):
                vals["nominee_mobile"] = normalize_space(kw.get("nominee_mobile"))

            # Store IDs as plain strings only (ORM records created on publish)
            if kw.get("benf_zan_id"):
                vals["benf_zan_id"] = kw.get("benf_zan_id")
            if kw.get("nominee_zanid"):
                vals["nominee_zanid"] = kw.get("nominee_zanid")

            # Image Handling (Mirror from main.py lines 765-774)
            if kw.get("nominee_image"):
                vals["nominee_image"] = base64.b64encode(kw.get("nominee_image").read()).decode('utf-8')
            if kw.get("zan_image"):
                vals["zan_image"] = base64.b64encode(kw.get("zan_image").read()).decode('utf-8')
            if kw.get("beneficiary_image"):
                image_data = base64.b64encode(kw.get("beneficiary_image").read()).decode('utf-8')
                vals["image_1920"] = image_data
                vals["beneficiary_image"] = image_data

            # Mandatory flags
            vals.update({
                "is_registrant": True,
                "is_group": False,
                "db_import": "yes",
            })

            # Write back to draft - Simplified as all fields are now computed in the backend
            draft.write({
                'partner_data': json.dumps(vals),
            })
            return request.redirect("/portal/registration/individual")
        except Exception as e:
            _logger.exception("Error while updating individual registration: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": f"An error occurred: {str(e)}"},
            )

    @http.route(
        ["/portal/registration/individual/view/<int:_id>"],
        type="http",
        auth="user",
        csrf=False,
    )
    def individual_view_details(self, _id, **kw):
        self.check_roles("Agent")
        try:
            gender = request.env["gender.type"].sudo().search([])
            regions = request.env["g2p.region"].sudo().search([])
            districts = request.env["g2p.district"].sudo().search([])
            id_types = request.env["g2p.id.type"].sudo().search([])

            beneficiary = request.env["draft.record"].sudo().browse(_id).exists()
            if not beneficiary:
                return super().individual_view_details(_id, **kw)

            mock_partner = MockPartner(beneficiary, request.env)

            return request.render("g2p_social_registry_model.individual_view_details_readonly", {
                "beneficiary": mock_partner,
                "gender": gender,
                "regions": regions,
                "districts": districts,
                "id_types": id_types,
            })
        except Exception as e:
            _logger.exception("Error loading individual details view: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": f"An error occurred while loading the view: {str(e)}"},
            )
