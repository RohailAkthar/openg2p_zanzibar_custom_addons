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

    def _handle_custom_import_logic(self, vals):
        """Helper to handle IDs that depend on record creation."""
        # Handle Zanzibar ID
        if 'import_zan_id' in vals and vals['import_zan_id']:
            zan_id_type = self.env['g2p.id.type'].sudo().search([('name', '=ilike', 'Zanzibar ID')], limit=1)
            if zan_id_type:
                for record in self:
                    existing_id = record.sudo().reg_ids.filtered(lambda r: r.id_type == zan_id_type)
                    if existing_id:
                        # Minimize writes
                        if existing_id[0].value != vals['import_zan_id']:
                            existing_id[0].write({'value': vals['import_zan_id'], 'status': 'valid'})
                    else:
                        self.env['g2p.reg.id'].sudo().create({
                            'partner_id': record.id,
                            'id_type': zan_id_type.id,
                            'value': vals['import_zan_id'],
                            'status': 'valid',
                        })

        # Zanzibar ID is handled in the Optimized logic above
        pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_import_vals(vals)
        self._handle_import_lookups(vals_list)
        records = super().create(vals_list)
        # Zanzibar ID still needs to be handled after creation
        for i, record in enumerate(records):
            record._handle_custom_import_logic(vals_list[i])
        return records

    def write(self, vals):
        self._prepare_import_vals(vals)
        self._handle_import_lookups([vals])
        res = super().write(vals)
        self._handle_custom_import_logic(vals)
        return res
