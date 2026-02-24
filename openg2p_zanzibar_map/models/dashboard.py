# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class DashboardLogic(models.Model):
    _name = "dashboard.logic"
    _description = "Dashboard Logic"

    @api.model
    def get_dashboard_data(self, filters=None):
        filters = filters or {}

        Partner = self.env["res.partner"]
        District = self.env["g2p.district"]
        Region = self.env["g2p.region"]

        # ---------------------------------------------------
        # Base Domain (Individuals Only)
        # ---------------------------------------------------
        domain = [
            ("is_registrant", "=", True),
            ("is_group", "=", False),
        ]

        # Gender filter
        if filters.get("gender"):
            gender_filter = [
                filters["gender"].lower(),
                filters["gender"].capitalize(),
            ]
            domain.append(("gender", "in", gender_filter))

        # ---------------------------------------------------
        # Region Filter
        # ---------------------------------------------------
        selected_region = False
        if filters.get("region"):
            selected_region = Region.search(
                ['|',("code", "=", filters["region"]), ("name", "=", filters["region"])], limit=1
            )
            if selected_region:
                domain.append(("region", "=", selected_region.id))


        # ---------------------------------------------------
        # District Filter
        # ---------------------------------------------------
        selected_district = False
        if filters.get("district"):
            selected_district = District.search(
                ['|', ("code", "=", filters["district"]), ("name", "=", filters["district"])], limit=1
            )
            if selected_district:
                domain.append(("district", "=", selected_district.id))

        partners = Partner.search(domain)

        # ---------------------------------------------------
        # Age Bucket Filtering (Python — as requested)
        # ---------------------------------------------------
        age_bucket = filters.get("age_bucket")
        if age_bucket:
            filtered_ids = []

            for p in partners:
                if not p.age or p.age == "No Birthdate!":
                    continue
                try:
                    age = int(p.age)
                except (TypeError, ValueError):
                    continue

                if age_bucket == "70-75" and 70 <= age <= 75:
                    filtered_ids.append(p.id)
                elif age_bucket == "76-80" and 76 <= age <= 80:
                    filtered_ids.append(p.id)
                elif age_bucket == "81-85" and 81 <= age <= 85:
                    filtered_ids.append(p.id)
                elif age_bucket == "86-90" and 86 <= age <= 90:
                    filtered_ids.append(p.id)
                elif age_bucket == "91-95" and 91 <= age <= 95:
                    filtered_ids.append(p.id)
                elif age_bucket == "96-100" and 96 <= age <= 100:
                    filtered_ids.append(p.id)
                elif age_bucket == "101+" and age > 100:
                    filtered_ids.append(p.id)

            partners = Partner.browse(filtered_ids)

        total_partners = len(partners)

        # ---------------------------------------------------
        # Groups Count (Fixed Region/District Logic)
        # ---------------------------------------------------
        group_domain = [
            ("is_registrant", "=", True),
            ("is_group", "=", True),
        ]

        if filters.get("gender"):
            gender_filter = [
                filters["gender"].lower(),
                filters["gender"].capitalize(),
            ]
            group_domain.append(("gender", "in", gender_filter))

        if selected_region:
            group_domain.append(("region", "=", selected_region.id))

        if selected_district:
            group_domain.append(("district", "=", selected_district.id))

        total_groups = Partner.search_count(group_domain)

        # ---------------------------------------------------
        # Age Bucket Aggregation
        # ---------------------------------------------------
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

        # ---------------------------------------------------
        # Geographic Aggregation
        # ---------------------------------------------------
        district_counts = {}
        province_counts = {}
        province_counts_name_only = {}
        


        if age_bucket:
            # When filtered by age, build manually from partners
            for p in partners:
                if p.district:
                    district_counts[p.district.name] = (
                        district_counts.get(p.district.name, 0) + 1
                    )
                    if p.district.code:
                        district_counts[p.district.code] = (
                            district_counts.get(p.district.code, 0) + 1
                        )

                if p.region:
                    if p.region.code:
                        province_counts[p.region.code] = (
                            province_counts.get(p.region.code, 0) + 1
                        )
                    if p.region.name:
                        province_counts[p.region.name] = (
                            province_counts.get(p.region.name, 0) + 1
                        )
                        province_counts_name_only[p.region.name] = (
                            province_counts_name_only.get(p.region.name, 0) + 1
                        )

        else:
            # District aggregation
            partners_by_district = Partner.read_group(
                domain=domain + [("district", "!=", False)],
                fields=["district"],
                groupby=["district"],
            )

            for row in partners_by_district:
                d = District.browse(row["district"][0])
                count = row["district_count"]

                district_counts[d.name] = count
                if d.code:
                    district_counts[d.code] = count

            # Province aggregation
            partners_by_province = Partner.read_group(
                domain=domain + [("region", "!=", False)],
                fields=["region"],
                groupby=["region"],
            )

            for row in partners_by_province:
                region = Region.browse(row["region"][0])
                count = row["region_count"]

                if region.code:
                    province_counts[region.code] = count
                if region.name:
                    province_counts[region.name] = count
                    province_counts_name_only[region.name] = count

        # ---------------------------------------------------
        # Chart Region Data (Names Only)
        # ---------------------------------------------------
        region_data = {}
        chart_labels = []
        chart_values = []

        for key, value in province_counts_name_only.items():
                chart_labels.append(key)
                chart_values.append(value)

        if chart_labels:
            region_data = {
                "labels": chart_labels,
                "datasets": [
                    {
                        "label": "Registrations",
                        "data": chart_values,
                        "backgroundColor": "#4e73df",
                    }
                ],
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
            "province_data": province_counts,
        }

    # ---------------------------------------------------
    # Gender Distribution
    # ---------------------------------------------------
    def _gender_distribution(self, partners):
        result = {"Male": 0, "Female": 0, "Unknown": 0}

        for p in partners:
            if not p.gender:
                result["Unknown"] += 1
            elif p.gender.lower() == "male":
                result["Male"] += 1
            elif p.gender.lower() == "female":
                result["Female"] += 1
            else:
                result["Unknown"] += 1

        return result