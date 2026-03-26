import json
import logging
from pathlib import Path

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class ZanzibarProvince(models.Model):
    _inherit = 'g2p.region'
    _description = 'Province'

    name = fields.Char(string="Province Name", required=True)
    code = fields.Char(string="Capitol")
    geojson_feature = fields.Text(
        string="GeoJSON Feature",
        help="GeoJSON feature payload for rendering this region on the map.",
    )


class ZanzibarDistrict(models.Model):
    _inherit = 'g2p.district'
    _description = 'Sri Lanka District'
    
    name = fields.Char(string="District Name", required=True)
    # Linking to the existing Region/Province table
    province_id = fields.Many2one('g2p.region', string="Province/Region", required=True)
    code = fields.Char(string="District Code")
    geojson_feature = fields.Text(
        string="GeoJSON Feature",
        help="GeoJSON feature payload for rendering this district on the map.",
    )

    # @api.model
    # def seed_geojson_from_lib(self):
    #     module_root = Path(__file__).resolve().parents[1]
    #     lib_dir = module_root / "static" / "lib"

    #     try:
    #         provinces = json.loads((lib_dir / "tz.json").read_text(encoding="utf-8"))
    #         districts = json.loads(
    #             (lib_dir / "geoBoundaries-TZA-ADM2.geojson").read_text(encoding="utf-8")
    #         )
    #     except Exception:
    #         _logger.exception("Failed loading static lib GeoJSON")
    #         return

    #     region_by_code = {}
    #     for feature in provinces.get("features", []):
    #         props = feature.get("properties") or {}
    #         if props.get("id"):
    #             region_by_code[props["id"]] = feature

    #     district_by_key = {}
    #     for feature in districts.get("features", []):
    #         props = feature.get("properties") or {}
    #         key = (props.get("province_code"), props.get("shapeName"))
    #         if key[0] and key[1]:
    #             district_by_key[key] = feature

    #     region_seed_to_lib_code = {
    #         "kaskazini_pemba": "TZ06",
    #         "kaskazini_unguja": "TZ07",
    #         "kusini_pemba": "TZ10",
    #         "kusini_unguja": "TZ11",
    #         "mjini_magharibi": "TZ15",
    #     }
    #     Region = self.env["g2p.region"]
    #     for seed_code, lib_code in region_seed_to_lib_code.items():
    #         region = Region.search([("code", "=", seed_code)], limit=1)
    #         feature = region_by_code.get(lib_code)
    #         if region and feature:
    #             region.geojson_feature = json.dumps(feature)

    #     district_seed_to_lib = {
    #         "chake_chake": ("TZ10", "Chake Chake"),
    #         "kaskazini_a": ("TZ07", "Kaskazini A"),
    #         "kaskazini_b": ("TZ07", "Kaskazini B"),
    #         "kati": ("TZ11", "Kati"),
    #         "kusini": ("TZ11", "Kusini"),
    #         "micheweni": ("TZ06", "Micheweni"),
    #         "mkoani": ("TZ10", "Mkoani"),
    #         "wete": ("TZ06", "Wete"),
    #         # ADM2 source has only "Mjini" in TZ15.
    #         "mjini_magharibi_a": ("TZ15", "Mjini"),
    #         "magharibi_b": ("TZ15", "Mjini"),
    #     }
    #     for seed_code, lookup in district_seed_to_lib.items():
    #         district = self.search([("code", "=", seed_code)], limit=1)
    #         feature = district_by_key.get(lookup)
    #         if district and feature:
    #             district.geojson_feature = json.dumps(feature)
