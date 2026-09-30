import json
import logging
from pathlib import Path
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class G2PShehia(models.Model):
    _name = "g2p.shehia"
    _description = "G2P Shehia (Ward)"
    _order = "name ASC"

    name = fields.Char(string="Shehia Name", required=True, index=True)
    district_id = fields.Many2one(
        "g2p.district",
        string="District",
        required=True,
        ondelete="restrict",
        index=True,
    )
    region_id = fields.Many2one(
        "g2p.region",
        string="Region",
        related="district_id.province_id",
        store=True,
        readonly=True,
        index=True,
    )
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def seed_shehias_from_json(self):
        """Seed master data of 391 Shehias from data/shehias.json."""
        json_file = Path(__file__).resolve().parent.parent / "data" / "shehias.json"
        if not json_file.exists():
            _logger.warning("Shehia seed file %s does not exist.", json_file)
            return

        with open(json_file, "r", encoding="utf-8") as f:
            shehia_data = json.load(f)

        District = self.env["g2p.district"].sudo()
        district_cache = {}
        for d in District.search([]):
            district_cache[d.name.strip().lower()] = d.id

        created_count = 0
        updated_count = 0

        for item in shehia_data:
            s_name = item.get("name", "").strip()
            d_name = item.get("district", "").strip().lower()
            d_id = district_cache.get(d_name)

            if not d_id:
                # Fallback search
                d_rec = District.search([("name", "=ilike", d_name)], limit=1)
                if d_rec:
                    d_id = d_rec.id
                    district_cache[d_name] = d_id
                else:
                    _logger.warning("District '%s' not found for Shehia '%s'", d_name, s_name)
                    continue

            existing = self.sudo().search([
                ("name", "=ilike", s_name),
                ("district_id", "=", d_id),
            ], limit=1)

            if not existing:
                self.sudo().create({
                    "name": s_name,
                    "district_id": d_id,
                    "active": True,
                })
                created_count += 1
            else:
                updated_count += 1

        _logger.info("Shehia seed completed: %d created, %d verified.", created_count, updated_count)
