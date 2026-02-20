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

                const [provinceRes, districtRes] = await Promise.all([
                    fetch("/openg2p_zanzibar_map/static/lib/tz.json"),
                    fetch("/openg2p_zanzibar_map/static/lib/geoBoundaries-TZA-ADM2.geojson"),
                ]);

                if (!provinceRes.ok || !districtRes.ok) {
                    throw new Error("GeoJSON Load Error");
                }

                const fullProvinceData = await provinceRes.json();
                const fullDistrictData = await districtRes.json();

                const zanzibarCodes = ["TZ06", "TZ07", "TZ10", "TZ11", "TZ15"];
                const PEMBA_CODES = ["TZ06", "TZ10"];

                const SHIFT_X = 0;
                const SHIFT_Y = -0.3;

                const transform = (f, code) =>
                    PEMBA_CODES.includes(code)
                        ? this.shiftFeature(f, SHIFT_X, SHIFT_Y)
                        : f;

                this.provinceGeoJson = {
                    type: "FeatureCollection",
                    features: fullProvinceData.features
                        .filter((f) => zanzibarCodes.includes(f.properties?.id))
                        .map((f) => transform(f, f.properties.id)),
                };

                this.districtGeoJson = {
                    type: "FeatureCollection",
                    features: fullDistrictData.features
                        .filter((f) =>
                            zanzibarCodes.includes(f.properties?.province_code)
                        )
                        .map((f) =>
                            transform(f, f.properties?.province_code)
                        ),
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
            () => [this.props.province_data, this.props.data, this.currentLevel]
        );

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });
    }

    // ----------------------------
    // Normalization
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
    // Geometry Shift
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
    // Dynamic Gradient
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
        if (this.currentLevel === "province") {
            this.renderProvinceLayer();
        } else if (this.selectedProvinceCode) {
            this.renderDistrictLayer(this.selectedProvinceCode);
        }
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
        if (this.map && this.geoJsonLayer) {
            this.map.fitBounds(this.geoJsonLayer.getBounds(), {
                padding: [5, 5],
                animate: true,
            });
        }
    }

    // ----------------------------
    // Province Layer
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
            this.props?.province_data
        );
        console.log("Normalized Province Data:", normProvinceData);
        console.log("Province  features:", this.props?.province_data);
        let mapTotal = 0;

        this.provinceGeoJson.features.forEach((f) => {
            const normId = this.normalizeString(f.properties.id);
            const normName = this.normalizeString(f.properties.name);
            mapTotal +=
                normProvinceData[normId] ||
                normProvinceData[normName] ||
                0;
        });

        this.geoJsonLayer = L.geoJson(this.provinceGeoJson, {
            style: (f) => ({
                fillColor:
                    PROVINCE_COLORS[f.properties.id] || "#e2e8f0",
                weight: 2,
                color: "#ffffff",
                opacity: 1,
                fillOpacity: 0.85,
            }),
            onEachFeature: (f, layer) => {
                const normId = this.normalizeString(f.properties.id);
                const normName = this.normalizeString(
                    f.properties.name
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
        console.log("Drill down to province code:", code);
        console.log("District GeoJSON features:", this.districtGeoJson?.features);
        const hasData = this.districtGeoJson?.features.some(
            (f) => f.properties?.province_code === code
        );
        console.log("Has data for drill down:", hasData);
        if (!hasData) return;

        this.currentLevel = "district";
        this.selectedProvinceCode = code;
        this.renderDistrictLayer(code);
    }
    // ----------------------------
    // District Layer
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

        const features =
            this.districtGeoJson.features.filter(
                (f) =>
                    f.properties?.province_code === code
            );

        const normDistrictData = this.normalizeData(
            this.props?.data
        );

        const values = Object.values(normDistrictData);
        const maxValue =
            values.length > 0
                ? Math.max(...values)
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
                            this.currentLevel =
                                "province";
                            this.selectedProvinceCode =
                                null;

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
    filters: { type: Object, optional: true },
    onMapClick: { type: Function, optional: true },
};