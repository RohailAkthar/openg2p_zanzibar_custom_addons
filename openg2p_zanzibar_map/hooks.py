import json
import logging
from pathlib import Path

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _load_geojson_sources():
    module_root = Path(__file__).resolve().parent
    lib_dir = module_root / "static" / "lib"
    provinces = json.loads((lib_dir / "tz.json").read_text(encoding="utf-8"))
    districts = json.loads(
        (lib_dir / "geoBoundaries-TZA-ADM2.geojson").read_text(encoding="utf-8")
    )
    return provinces, districts


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Region = env["g2p.region"]
    District = env["g2p.district"]

    try:
        province_geojson, district_geojson = _load_geojson_sources()
    except Exception:
        _logger.exception("Failed to load map geometry from static/lib")
        return

    region_by_code = {}
    for feature in province_geojson.get("features", []):
        props = feature.get("properties") or {}
        region_code = props.get("id")
        if region_code:
            region_by_code[region_code] = feature

    district_by_key = {}
    for feature in district_geojson.get("features", []):
        props = feature.get("properties") or {}
        key = (props.get("province_code"), props.get("shapeName"))
        if key[0] and key[1]:
            district_by_key[key] = feature

    region_seed_to_lib_code = {
        "kaskazini_pemba": "TZ06",
        "kaskazini_unguja": "TZ07",
        "kusini_pemba": "TZ10",
        "kusini_unguja": "TZ11",
        "mjini_magharibi": "TZ15",
    }
    for seed_code, lib_code in region_seed_to_lib_code.items():
        region = Region.search([("code", "=", seed_code)], limit=1)
        feature = region_by_code.get(lib_code)
        if region and feature:
            region.geojson_feature = json.dumps(feature)

    district_seed_to_lib = {
        "chake_chake": ("TZ10", "Chake Chake"),
        "kaskazini_a": ("TZ07", "Kaskazini A"),
        "kaskazini_b": ("TZ07", "Kaskazini B"),
        "kati": ("TZ11", "Kati"),
        "kusini": ("TZ11", "Kusini"),
        "micheweni": ("TZ06", "Micheweni"),
        "mkoani": ("TZ10", "Mkoani"),
        "wete": ("TZ06", "Wete"),
        # ADM2 source only has "Mjini" for TZ15. Reuse it for both local district codes.
        "mjini_magharibi_a": ("TZ15", "Mjini"),
        "magharibi_b": ("TZ15", "Mjini"),
    }
    for seed_code, lookup in district_seed_to_lib.items():
        district = District.search([("code", "=", seed_code)], limit=1)
        feature = district_by_key.get(lookup)
        if district and feature:
            district.geojson_feature = json.dumps(feature)
