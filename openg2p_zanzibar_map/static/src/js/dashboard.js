/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { MapComponent } from "../components/map/map_component";
import { ChartComponent } from "../components/chart/chart";
import { KpiComponent } from "../components/kpi/kpi";
export class ZDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            kpi: {},
            charts: {},
            map_data: {},
            loading: true,
            filters: {
                gender: null,
                age_bucket: null,
                region: null,
                district: null,
            },
        });
        this.applyFilterFromChart = this.applyFilterFromChart.bind(this);
        // this.applyFilterFromMap = this.applyFilterFromMap.bind(this);
        this.setFilterGender = this.setFilterGender.bind(this);
        this.setFilterAgeBucket = this.setFilterAgeBucket.bind(this);
        this.clearFilters = this.clearFilters.bind(this);
        this.fetchData = this.fetchData.bind(this);
        onWillStart(async () => {
            await this.fetchData();
        });
    }
    get hasActiveFilters() {
        const f = this.state.filters;
        return f.gender || f.age_bucket || f.region || f.district;
    }
    async fetchData() {
        this.state.loading = true;
        const filters = { ...this.state.filters };
        const data = await this.orm.call("dashboard.logic", "get_dashboard_data", [], { filters });
        this.state.kpi = data.kpi || {};
        this.state.charts = data.charts || {};
        this.state.map_data = data.map_data || {};
        this.state.loading = false;
    }
    clearFilters() {
        this.state.filters = {
            gender: null,
            age_bucket: null,
            region: null,
            district: null,
        };
        this.fetchData();
    }
    applyFilterFromChart(payload) {
        if (!payload || !payload.chartType) return;
        if (payload.chartType === "gender") {
            const g = payload.label === "Male" ? "male" : payload.label === "Female" ? "female" : null;
            this.state.filters.gender = this.state.filters.gender === g ? null : g;
            this.state.filters.age_bucket = null;
            this.state.filters.region = null;
            this.state.filters.district = null;
        } else if (payload.chartType === "age") {
            const ageKeys = ["18-69", "70-79", "80-89", "90+"];
            const key = ageKeys.find((k) => payload.label === k) || null;
            this.state.filters.age_bucket = this.state.filters.age_bucket === key ? null : key;
            this.state.filters.gender = null;
            this.state.filters.region = null;
            this.state.filters.district = null;
        } else if (payload.chartType === "region") {
            this.state.filters.region = this.state.filters.region === payload.label ? null : payload.label;
            this.state.filters.district = null;
            this.state.filters.gender = null;
            this.state.filters.age_bucket = null;
        }
        this.fetchData();
    }
    // applyFilterFromMap(payload) {
    // if (!payload) return;
    // if (payload.region !== undefined) {
    // this.state.filters.region = payload.region === this.state.filters.region ? null : payload.region;
    // this.state.filters.district = null;
    // }
    // if (payload.district !== undefined) {
    // this.state.filters.district = payload.district === this.state.filters.district ? null : payload.district;
    // }
    // this.fetchData();
    // }
    setFilterGender(value) {
        this.state.filters.gender = value || null;
        this.state.filters.district = null;
        this.state.filters.region = null;
        this.fetchData();
    }
    setFilterAgeBucket(value) {
        this.state.filters.age_bucket = value || null;
        this.state.filters.region = null;
        this.state.filters.district = null;
        this.fetchData();
    }
}
ZDashboard.template = "openg2p_zanzibar_map.MainLayout";
ZDashboard.components = { MapComponent, ChartComponent, KpiComponent };
registry.category("actions").add("z_dashboard_main", ZDashboard);