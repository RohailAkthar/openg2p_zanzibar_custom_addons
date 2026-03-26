/** @odoo-module **/
import {
    Component,
    onWillStart,
    useRef,
    onMounted,
    onWillUpdateProps,
    onWillUnmount,
    useEffect,
} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS, loadCSS } from "@web/core/assets";

export class MapComponent extends Component {
    setup() {
        this.mapRef = useRef("map");
        this.notification = useService("notification");

        this.map = null;
        this.geoJsonLayer = null;
        this.markerLayer = null;

        this.currentLevel = "province";
        this.selectedProvinceCode = null;

        onWillStart(async () => {
            try {
                await loadJS("https://unpkg.com/chroma-js@2.4.2/chroma.min.js");
                await loadCSS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");
                await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");

                const mapGeojson = this.props?.map_geojson || {};
                this.provinceGeoJson = mapGeojson.provinces || {
                    type: "FeatureCollection",
                    features: [],
                };
                this.districtGeoJson = mapGeojson.districts || {
                    type: "FeatureCollection",
                    features: [],
                };
            } catch (err) {
                console.error("Map Init Failed:", err);
                this.notification.add("Map failed to load", { type: "danger" });
            }
        });

        onMounted(() => {
            if (this.mapRef.el) {
                this.renderMap();
            }
        });

        onWillUpdateProps((nextProps) => {
            if (!nextProps?.filters?.region && this.currentLevel === "district") {
                this.currentLevel = "province";
                this.selectedProvinceCode = null;
            }
        });

        useEffect(
            () => {
                if (this.map) {
                    this.refreshCurrentLayer();
                }
            },
            () => [
                this.props.province_data,
                this.props.data,
                this.props.map_geojson,
                this.currentLevel,
            ]
        );

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });
    }

    // ----------------------------
    // Normalization (unchanged)
    // ----------------------------
    normalizeString(str) {
        if (!str) return "";
        return str
            .toString()
            .toLowerCase()
            .trim()
            .replace(/[-_]/g, " ")
            .replace(/\s+/g, " ");
    }

    normalizeData(dataObj) {
        if (!dataObj) return {};
        const normalized = {};
        for (const [key, value] of Object.entries(dataObj)) {
            normalized[this.normalizeString(key)] = value;
        }
        return normalized;
    }

    // ----------------------------
    // Geometry Shift – used ONLY to close the gap between Unguja and Pemba
    // ----------------------------
    shiftFeature(feature, dx, dy) {
        const shift = (coords) =>
            Array.isArray(coords[0])
                ? coords.map(shift)
                : [coords[0] + dx, coords[1] + dy];

        return {
            ...feature,
            geometry: {
                ...feature.geometry,
                coordinates: shift(feature.geometry.coordinates),
            },
        };
    }

    // ----------------------------
    // Dynamic Gradient (unchanged)
    // ----------------------------
    getGradientColor(baseColor, value, max) {
        const safeMax = max > 0 ? max : 1;

        const scale = chroma
            .scale([chroma(baseColor).darken(2), baseColor, "#38bdf8"])
            .mode("lch")
            .domain([0, safeMax / 2, safeMax]);

        return scale(value).hex();
    }

    renderMap() {
        if (!this.mapRef.el || typeof L === "undefined") return;

        this.map = L.map(this.mapRef.el, {
            zoomControl: false,
            attributionControl: false,
            zoomSnap: 0.1,
            scrollWheelZoom: false,
            doubleClickZoom: false,
        });

        this.markerLayer = L.layerGroup().addTo(this.map);
        this.renderProvinceLayer();
    }

    refreshCurrentLayer() {
        this.syncGeoJsonFromProps();
        if (this.currentLevel === "province") {
            this.renderProvinceLayer();
        } else if (this.selectedProvinceCode) {
            this.renderDistrictLayer(this.selectedProvinceCode);
        }
    }

    syncGeoJsonFromProps() {
        const mapGeojson = this.props?.map_geojson || {};
        this.provinceGeoJson = mapGeojson.provinces || {
            type: "FeatureCollection",
            features: [],
        };
        this.districtGeoJson = mapGeojson.districts || {
            type: "FeatureCollection",
            features: [],
        };
    }

    addValueMarker(latlng, name, value, percent) {
        const percentStr =
            percent > 0
                ? `<br/><span style="font-size: 0.8em; color: #e2e8f0;">(${percent.toFixed(
                      1
                  )}%)</span>`
                : "";

        const icon = L.divIcon({
            className: "o_map_text_label",
            html: `
                <div style="text-align: center;">
                    <span class="o_map_label_name">${name}</span><br/>
                    <span class="o_map_label_value">${value.toLocaleString()}</span>
                    ${percentStr}
                </div>
            `,
            iconSize: [0, 0],
            iconAnchor: [0, 0],
        });

        L.marker(latlng, { icon, interactive: false }).addTo(this.markerLayer);
    }

    fitToLayer() {
        if (!this.map || !this.geoJsonLayer) return;

        const bounds = this.geoJsonLayer.getBounds();

        if (bounds.isValid()) {
            this.map.fitBounds(bounds, {
                padding: [5, 5],
                animate: true,
            });
        } else {
            this.map.setView([-6.1659, 35.7516], 6.5);
        }
    }

    getVisibleDistrictFeatures(code) {
        const allFeatures = this.districtGeoJson?.features || [];
        return allFeatures.filter((f) => {
            const provinceCode = f.properties?.province_code;
            return provinceCode === code;
        });
    }

    // ----------------------------
    // Province Layer – with Pemba → Unguja shift
    // ----------------------------
    renderProvinceLayer() {
        if (!this.provinceGeoJson) return;

        if (this.geoJsonLayer) {
            this.map.removeLayer(this.geoJsonLayer);
        }
        this.markerLayer.clearLayers();

        const PROVINCE_COLORS = {
            TZ06: "#34d399",
            TZ07: "#60a5fa",
            TZ10: "#fbbf24",
            TZ11: "#f87171",
            TZ15: "#a78bfa",
        };

        const normProvinceData = this.normalizeData(
            this.props?.province_data || {}
        );

        // === SHIFT PEMBA CLOSER TO UNGUJA (no empty ocean gap) ===
        // Tune the two numbers below if the gap is still too big/small.
        // Pemba is originally north of Unguja → we move it south (negative dy) and slightly west.
        const SHIFT_X = 0;
        const SHIFT_Y = -0.3;

        const shiftedFeatures = (this.provinceGeoJson.features || []).map((f) => {
            const name = (f.properties?.name || "").toString().toLowerCase();
            if (name.includes("pemba")) {
                return this.shiftFeature(f, SHIFT_X, SHIFT_Y);
            }
            return f; // Unguja and any other provinces stay at real coordinates
        });

        const shiftedProvinceGeoJson = {
            type: "FeatureCollection",
            features: shiftedFeatures,
        };

        // Sum total using original data (properties never change)
        let mapTotal = 0;
        for (const f of this.provinceGeoJson.features || []) {
            const normId = this.normalizeString(f.properties?.id);
            const normName = this.normalizeString(f.properties?.name);
            const val =
                normProvinceData[normId] ||
                normProvinceData[normName] ||
                0;
            mapTotal += val;
        }

        this.geoJsonLayer = L.geoJson(shiftedProvinceGeoJson, {
            style: (f) => ({
                fillColor:
                    PROVINCE_COLORS[f.properties.id] || "#e2e8f0",
                weight: 2,
                color: "#ffffff",
                opacity: 1,
                fillOpacity: 0.85,
            }),
            onEachFeature: (f, layer) => {
                const normId = this.normalizeString(f.properties?.id);
                const normName = this.normalizeString(
                    f.properties?.name
                );
                const val =
                    normProvinceData[normId] ||
                    normProvinceData[normName] ||
                    0;

                const percent = mapTotal
                    ? (val / mapTotal) * 100
                    : 0;

                this.addValueMarker(
                    layer.getBounds().getCenter(),
                    f.properties.name,
                    val,
                    percent
                );

                layer.on({
                    mouseover: (e) =>
                        e.target.setStyle({
                            weight: 3,
                            fillOpacity: 1,
                        }),
                    mouseout: (e) =>
                        this.geoJsonLayer.resetStyle(e.target),
                    click: () => {
                        this.props?.onMapClick?.({
                            region: f.properties.name,
                        });
                        this.drillDownToProvince(
                            f.properties.id
                        );
                    },
                });
            },
        }).addTo(this.map);

        this.fitToLayer();
    }

    drillDownToProvince(code) {
        const hasDistricts = this.getVisibleDistrictFeatures(code).length > 0;
        if (!hasDistricts) return;

        this.currentLevel = "district";
        this.selectedProvinceCode = code;
        this.renderDistrictLayer(code);
    }

    // ----------------------------
    // District Layer (unchanged – only one island is shown, no gap)
    // ----------------------------
    renderDistrictLayer(code) {
        if (!this.districtGeoJson) return;

        if (this.geoJsonLayer) {
            this.map.removeLayer(this.geoJsonLayer);
        }
        this.markerLayer.clearLayers();

        const PROVINCE_COLORS = {
            TZ06: "#34d399",
            TZ07: "#60a5fa",
            TZ10: "#fbbf24",
            TZ11: "#f87171",
            TZ15: "#a78bfa",
        };

        const parentColor =
            PROVINCE_COLORS[code] || "#94a3b8";

        const normDistrictData = this.normalizeData(
            this.props?.data || {}
        );

        const features = this.getVisibleDistrictFeatures(code);

        const visibleValues = features.map((f) => {
            const normName = this.normalizeString(f.properties?.shapeName);
            return normDistrictData[normName] || 0;
        });
        const maxValue =
            visibleValues.length > 0
                ? Math.max(...visibleValues)
                : 0;

        this.geoJsonLayer = L.geoJson(
            { type: "FeatureCollection", features },
            {
                style: (f) => {
                    const normName =
                        this.normalizeString(
                            f.properties.shapeName
                        );

                    return {
                        fillColor: this.getGradientColor(
                            parentColor,
                            normDistrictData[normName] || 0,
                            maxValue
                        ),
                        weight: 1.5,
                        color: "#ffffff",
                        fillOpacity: 0.85,
                    };
                },
                onEachFeature: (f, layer) => {
                    const normName =
                        this.normalizeString(
                            f.properties.shapeName
                        );
                    const val =
                        normDistrictData[normName] || 0;

                    this.addValueMarker(
                        layer.getBounds().getCenter(),
                        f.properties.shapeName,
                        val,
                        0
                    );

                    layer.on({
                        mouseover: (e) =>
                            e.target.setStyle({
                                weight: 3,
                                fillOpacity: 1,
                            }),
                        mouseout: (e) =>
                            this.geoJsonLayer.resetStyle(
                                e.target
                            ),
                        click: () => {
                            this.currentLevel = "province";
                            this.selectedProvinceCode = null;

                            this.props?.onMapClick?.({
                                region: null,
                            });

                            this.renderProvinceLayer();
                        },
                    });
                },
            }
        ).addTo(this.map);

        this.fitToLayer();
    }
}

MapComponent.template =
    "openg2p_zanzibar_map.MapComponent";

MapComponent.props = {
    data: { type: Object, optional: true },
    province_data: { type: Object, optional: true },
    map_geojson: { type: Object, optional: true },
    filters: { type: Object, optional: true },
    onMapClick: { type: Function, optional: true },
};