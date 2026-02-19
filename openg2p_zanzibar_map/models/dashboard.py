# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, models
from datetime import date

_logger = logging.getLogger(__name__)


class DashboardLogic(models.Model):
    _name = "dashboard.logic"
    _description = "Dashboard Logic"

    @api.model
    def get_dashboard_data(self, filters=None):
        filters = filters or {}
        Partner = self.env["res.partner"]
        District = self.env["g2p.district"]

        # Base domain: individual registrants only
        domain = [
            ("is_registrant", "=", True),
            ("is_group", "=", False),
        ]

        if filters.get("gender"):
            domain.append(("gender", "=", filters["gender"]))

        region_districts = self.env["g2p.district"]
        district = self.env["g2p.district"]

        if filters.get("region"):
            region_districts = District.search([("province_id.code", "=", filters["region"])])
            if region_districts:
                domain.append(("district", "in", region_districts.ids))
            else:
                domain.append(("district", "=", False))

        if filters.get("district"):
            district = District.search([("name", "=", filters["district"])], limit=1)
            if district:
                domain.append(("district", "=", district.id))

        partners = Partner.search(domain)

        # Age filter in Python (age may be computed)
        age_bucket = filters.get("age_bucket")
        if age_bucket:
            filtered = []
            for p in partners:
                if not p.age or p.age == "No Birthdate!":
                    continue
                try:
                    age = int(p.age)
                except (TypeError, ValueError):
                    continue

                if age_bucket == "18-69" and 18 <= age <= 69:
                    filtered.append(p.id)
                elif age_bucket == "70-75" and 70 <= age <= 75:
                    filtered.append(p.id)
                elif age_bucket == "76-80" and 76 <= age <= 80:
                    filtered.append(p.id)
                elif age_bucket == "81-85" and 81 <= age <= 85:
                    filtered.append(p.id)
                elif age_bucket == "86-90" and 86 <= age <= 90:
                    filtered.append(p.id)
                elif age_bucket == "91-95" and 91 <= age <= 95:
                    filtered.append(p.id)
                elif age_bucket == "96-100" and 96 <= age <= 100:
                    filtered.append(p.id)
                elif age_bucket == "101+" and age > 100:
                    filtered.append(p.id)
            partners = Partner.browse(filtered)

        total_partners = len(partners)

        # Groups: same filters except is_group = True
        group_domain = [
            ("is_registrant", "=", True),
            ("is_group", "=", True),
        ]
        if filters.get("gender"):
            group_domain.append(("gender", "ilike", filters["gender"]))
        if region_districts:
            group_domain.append(("district", "in", region_districts.ids))
        if district:
            group_domain.append(("district", "=", district.id))
        total_groups = Partner.search_count(group_domain)

        age_buckets = {
            "70-75": 0,
            "76-80": 0,
            "81-85": 0,
            "86-90": 0,
            "91-95": 0,
            "96-100": 0,
            "101+": 0,
        }
        for p in partners:
            if not p.age or p.age == "No Birthdate!":
                continue
            try:
                age = int(p.age)
            except (TypeError, ValueError):
                continue

            if 70 <= age <= 75:
                age_buckets["70-75"] += 1
            elif 76 <= age <= 80:
                age_buckets["76-80"] += 1
            elif 81 <= age <= 85:
                age_buckets["81-85"] += 1
            elif 86 <= age <= 90:
                age_buckets["86-90"] += 1
            elif 91 <= age <= 95:
                age_buckets["91-95"] += 1
            elif 96 <= age <= 100:
                age_buckets["96-100"] += 1
            elif age > 100:
                age_buckets["101+"] += 1

        district_counts = {}
        if age_bucket:
            for p in  partners:
                if p.district:
                    name = p.district.name
                    district_counts[name] = district_counts.get(name, 0) + 1
        else:
            map_domain = domain + [("district", "!=", False)]
            partners_by_district = Partner.read_group(
                domain=map_domain,
                fields=["district"],
                groupby=["district"],
            )
            for row in partners_by_district:
                d = District.browse(row["district"][0])
                district_counts[d.name] = row["district_count"]

        # Get region-wise data
        region_data = {}
        if not filters.get('region'):  
            districts = self.env['g2p.district'].search_read(
                domain=[],
                fields=['id', 'name', 'province_id']
            )
            
            # Create a mapping of district IDs to province names
            district_to_province = {
                d['id']: d.get('province_id') and d['province_id'][1] or 'Unknown'
                for d in districts
            }
            
            # Get partner counts by district
            partner_counts = {}
            partner_data = Partner.read_group(
                domain=domain + [("district", "!=", False)],
                fields=['district'],
                groupby=['district'],
            )
            
            # Aggregate counts by province
            province_counts = {}
            for row in partner_data:
                district_id = row['district'][0]
                province_name = district_to_province.get(district_id, 'Unknown')
                province_counts[province_name] = province_counts.get(province_name, 0) + row['district_count']
            
            # Prepare data for the chart
            if province_counts:
                region_data = {
                    'labels': list(province_counts.keys()),
                    'datasets': [{
                        'label': 'Registrations',
                        'data': list(province_counts.values()),
                        'backgroundColor': '#4e73df',
                    }]
                }
        
        return {
            "kpi": {
                "total_pensioners": total_partners,
                "total_groups": total_groups,
            },
            "charts": {
                "age": age_buckets,
                "gender": self._gender_distribution(partners),
                "region_data": region_data,
            },
            "map_data": district_counts,
        }

    def _gender_distribution(self, partners):
        result = {"Male": 0, "Female": 0, "Unknown": 0}
        for p in partners:
            if p.gender is None:
                result["Unknown"] += 1
            elif p.gender.lower() == "male":
                result["Male"] += 1
            elif p.gender.lower() == "female":
                result["Female"] += 1
        return result
