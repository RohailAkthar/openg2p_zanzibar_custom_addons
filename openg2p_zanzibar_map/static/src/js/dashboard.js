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
        this.applyFilterFromMap = this.applyFilterFromMap.bind(this);
        this.clearFilters = this.clearFilters.bind(this);
        this.fetchData = this.fetchData.bind(this);
        
        onWillStart(async () => {
            await this.fetchData();
        });
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

    /**
     * Updated to be additive. Clicking a chart adds to existing filters.
     */
    applyFilterFromChart(payload) {
        if (!payload || !payload.chartType) return;

        if (payload.chartType === "gender") {
            const g = payload.label === "Male" ? "male" : payload.label === "Female" ? "female" : null;
            this.state.filters.gender = this.state.filters.gender === g ? null : g;
        } else if (payload.chartType === "age") {
            const key = payload.label;
            this.state.filters.age_bucket = this.state.filters.age_bucket === key ? null : key;
        } else if (payload.chartType === "region") {
            this.state.filters.region = this.state.filters.region === payload.label ? null : payload.label;
            this.state.filters.district = null; // Clear district if region changes
        }
        this.fetchData();
    }

    /**
     * Map Click Handler: Updates filters and triggers chart reload
     */
    applyFilterFromMap(payload) {
        if (!payload) return;
        
        if (payload.region !== undefined) {
            // If clicking the same region, we don't necessarily toggle off 
            // because the map needs to stay drilled down.
            this.state.filters.region = payload.region;
            this.state.filters.district = null;
        }
        if (payload.district !== undefined) {
            // Toggle district if clicked twice, otherwise set it
            this.state.filters.district = this.state.filters.district === payload.district ? null : payload.district;
        }
        this.fetchData();
    }

    clearFilters() {
        this.state.filters = { gender: null, age_bucket: null, region: null, district: null };
        this.fetchData();
    }
}
ZDashboard.template = "openg2p_zanzibar_map.MainLayout";
ZDashboard.components = { MapComponent, ChartComponent, KpiComponent };
registry.category("actions").add("z_dashboard_main", ZDashboard);