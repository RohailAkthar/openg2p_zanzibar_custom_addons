# -*- coding: utf-8 -*-
import logging
import random
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    def _generate_10_digit_unique_ids(self, count):
        """Generates a batch of unique 10-digit random IDs in a single query."""
        if count <= 0:
            return []
        
        generated_ids = set()
        while len(generated_ids) < count:
            val = str(random.SystemRandom().randint(1000000000, 9999999999))
            generated_ids.add(val)
        
        # Check database for existing ones
        existing = self.env['res.partner'].sudo().search([('unique_id', 'in', list(generated_ids))])
        existing_ids = set(existing.mapped('unique_id'))
        
        valid_ids = generated_ids - existing_ids
        
        needed = count - len(valid_ids)
        if needed > 0:
            valid_ids.update(self._generate_10_digit_unique_ids(needed))
            
        return list(valid_ids)

    def generate_unique_id(self):
        to_generate = self.filtered(lambda r: r.is_registrant and not r.unique_id)
        if not to_generate:
            return
            
        unique_vals = self._generate_10_digit_unique_ids(len(to_generate))
        for rec, val in zip(to_generate, unique_vals):
            rec.write({
                'unique_id': val,
                'pensioner_id': val
            })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Set is_registrant=True if imported or approved from draft
            if self.env.context.get("import_file") or vals.get("imported_record_state") == "published" or vals.get("draft_record_id"):
                vals["is_registrant"] = True
                
        records = super().create(vals_list)

        # Generate unique ID for any registrant records that are created and don't have one
        registrants = records.filtered(lambda r: r.is_registrant and not r.unique_id)
        if registrants:
            registrants.generate_unique_id()

        return records

    def write(self, vals):
        # Validate unique_id/pensioner_id uniqueness to prevent DB crash
        if 'unique_id' in vals and vals['unique_id']:
            existing = self.env['res.partner'].sudo().search([
                ('unique_id', '=', vals['unique_id']),
                ('id', 'not in', self.ids)
            ], limit=1)
            if existing:
                raise ValidationError(_("The Unique ID '%s' is already assigned to another partner (ID: %s).") % (vals['unique_id'], existing.id))

        if 'pensioner_id' in vals and vals['pensioner_id']:
            existing = self.env['res.partner'].sudo().search([
                ('pensioner_id', '=', vals['pensioner_id']),
                ('id', 'not in', self.ids)
            ], limit=1)
            if existing:
                raise ValidationError(_("The Pensioner ID '%s' is already assigned to another partner (ID: %s).") % (vals['pensioner_id'], existing.id))

        # If coming from draft or imported, ensure is_registrant is set
        if vals.get('draft_record_id') or vals.get('imported_record_state') == 'published':
            vals['is_registrant'] = True

        res = super().write(vals)

        # Generate unique ID for any registrant records that don't have one
        registrants = self.filtered(lambda r: r.is_registrant and not r.unique_id)
        if registrants:
            registrants.generate_unique_id()

        return res
