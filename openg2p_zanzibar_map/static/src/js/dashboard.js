/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { MapComponent } from "../components/map/map_component";
import { ChartComponent } from "../components/chart/chart";
import { KpiComponent } from "../components/kpi/kpi";

export class ZDashboard extends Component {
    setup() {
        this._t = _t;
        this.orm = useService("orm");
        this.user = useService("user");
        this.action = useService("action");

        // 1. Decoupled Language Switcher Map
        this.translations = {
            'en_US': {
                'Dashboard': 'Dashboard',
                'Refine Data': 'Refine Data',
                'Gender': 'Gender',
                'All Genders': 'All Genders',
                'Male': 'Male',
                'Female': 'Female',
                'Age Bracket': 'Age Bracket',
                'All Ages': 'All Ages',
                'Reset View': 'Reset View',
                'Total Pensioners': 'Total Pensioners',
                'Updating Data...': 'Updating Data...',
                'Age Distribution': 'Age Distribution',
                'Count': 'Count',
                'No data available': 'No data available',
                'Gender Split': 'Gender Split',
                'Region Distribution': 'Region Distribution',
                'Registrations': 'Registrations',
                'Access Restricted': 'Access Restricted',
                'Portal Mismatch': 'Portal Mismatch',
                'Permission Denied': 'You do not have permission to access the Pensioner Registry Dashboard.',
                'Use Portal Link': 'Please use the dedicated dashboard link provided to you.',
                'Contact Admin': 'Please contact your system administrator to request dashboard access.',
                'Back to Login': 'Back to Login Screen'
            },
            'sw_TZ': {
                'Dashboard': 'Dashibodi',
                'Refine Data': 'Chuja Takwimu',
                'Gender': 'Jinsia',
                'All Genders': 'Jinsia Zote',
                'Male': 'Wanaume',
                'Female': 'Wanawake',
                'Age Bracket': 'Umri',
                'All Ages': 'Umri Zote',
                'Reset View': 'Anza Upya',
                'Total Pensioners': 'Jumla ya Wazee',
                'Updating Data...': 'Inapakia...',
                'Age Distribution': 'Mgawanyiko wa Umri',
                'Count': 'Idadi',
                'No data available': 'Hakuna data',
                'Gender Split': 'Mgawanyiko wa Jinsia',
                'Region Distribution': 'Mgawanyiko wa Mkoa',
                'Registrations': 'Usajili',
                'Access Restricted': 'Ufikiaji Umezuiwa',
                'Portal Mismatch': 'Utofauti wa Portal',
                'Permission Denied': 'Hauna ruhusa ya kufikia Dashibodi ya Usajili wa Wazee.',
                'Use Portal Link': 'Tafadhali tumia kiungo maalum cha dashibodi ulichopewa.',
                'Contact Admin': 'Tafadhali wasiliana na msimamizi wa mfumo wako kuomba ufikiaji wa dashibodi.',
                'Back to Login': 'Rudi Kwenye Ingizo'
            }
        };

        this.state = useState({
            kpi: {},
            charts: {},
            map_data: {},
            map_geojson: {},
            loading: true,
            isAuthorized: false,
            isMinimalMode: sessionStorage.getItem('o_minimal_view') === '1',
            lang: sessionStorage.getItem('z_dashboard_lang') || 'en_US',
            currentUserName: this.user.name || "Dashboard User",
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
        this.switchLanguage = this.switchLanguage.bind(this);
        this.onBackToLogin = this.onBackToLogin.bind(this);
        this.logout = this.logout.bind(this);

        onWillStart(async () => {
            // Security Check (JS Layer)
            const isViewer = await this.user.hasGroup("openg2p_zanzibar_map.group_dashboard_viewer");
            const isAdmin = await this.user.hasGroup("base.group_system");
            const isMinimalMode = sessionStorage.getItem('o_minimal_view') === '1';

            // Strict Authorization: Access is only granted if user has permission AND is in minimal mode
            this.state.isAuthorized = (isViewer || isAdmin) && isMinimalMode;

            // Bounce Redirect: If an unauthorized user (like Admin on default URL) 
            // lands here, don't show the error screen, just bounce to home.
            if (!this.state.isAuthorized && !isMinimalMode) {
                window.location.hash = "#home";
                return;
            }

            if (this.state.isAuthorized) {
                await this.fetchData();
            }
        });
    }

    translate(text) {
        return this.translations[this.state.lang][text] || text;
    }

    switchLanguage(lang) {
        this.state.lang = lang;
        sessionStorage.setItem('z_dashboard_lang', lang);
        this.fetchData();
    }

    onBackToLogin() {
        // Secure Exit: Triggers a session logout
        this.logout();
    }

    logout() {
        // Clear all session flags so next login starts fresh
        sessionStorage.removeItem('o_minimal_view');
        sessionStorage.removeItem('o_minimal_no_access');
        sessionStorage.removeItem('o_dashboard_wrong_url');
        window.location.href = "/web/session/logout?redirect=/web";
    }

    async fetchData() {
        if (!this.state.isAuthorized) return;
        this.state.loading = true;
        const filters = { ...this.state.filters, lang: this.state.lang };

        try {
            const data = await this.orm.call("dashboard.logic", "get_dashboard_data", [], { filters });
            this.state.kpi = data.kpi || {};
            this.state.charts = data.charts || {};
            this.state.map_data = data.map_data || {};
            this.state.province_data = data.province_data || {};
            this.state.map_geojson = data.map_geojson || {};
        } catch (e) {
            console.error("Dashboard Fetch Error:", e);
        } finally {
            this.state.loading = false;
        }
    }

    setFilterGender(value) {
        this.state.filters.gender = value || null;
        this.fetchData();
    }

    setFilterAgeBucket(value) {
        this.state.filters.age_bucket = value || null;
        this.fetchData();
    }


    get hasActiveFilters() {
        const f = this.state.filters;
        return !!(f.gender || f.age_bucket || f.region || f.district);
    }

    applyFilterFromChart(payload) {
        if (!payload || !payload.chartType) return;

        if (payload.chartType === "gender") {
            const isMale = payload.label === "Male" || payload.label === this.translate("Male");
            const isFemale = payload.label === "Female" || payload.label === this.translate("Female");
            const g = isMale ? "male" : isFemale ? "female" : null;
            this.state.filters.gender = this.state.filters.gender === g ? null : g;
        } else if (payload.chartType === "age") {
            const key = payload.label;
            this.state.filters.age_bucket = this.state.filters.age_bucket === key ? null : key;
        } else if (payload.chartType === "region") {
            this.state.filters.region = this.state.filters.region === payload.label ? null : payload.label;
            this.state.filters.district = null;
        }
        this.fetchData();
    }

    applyFilterFromMap(payload) {
        if (!payload) return;

        if (payload.region !== undefined) {
            this.state.filters.region = payload.region;
            this.state.filters.district = null;
        }
        if (payload.district !== undefined) {
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