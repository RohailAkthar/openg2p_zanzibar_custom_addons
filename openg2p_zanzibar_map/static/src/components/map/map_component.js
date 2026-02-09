/** @odoo-module **/
import { Component, onWillStart, useRef, onMounted, onWillUpdateProps, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks"; // Import useService
import { loadJS, loadCSS } from "@web/core/assets";

const DISTRICT_TO_PROVINCE = {
    "Arusha": "TZ01", "Arusha Urban": "TZ01", "Karatu": "TZ01", "Longido": "TZ01",
    "Meru": "TZ01", "Monduli": "TZ01", "Ngorongoro": "TZ01",
    "Ilala": "TZ02", "Kinondoni": "TZ02", "Temeke": "TZ02", "Kigamboni": "TZ02", "Ubungo": "TZ02",
    "Iringa": "TZ04", "Iringa Urban": "TZ04", "Mafinga": "TZ04", "Kilolo": "TZ04", "Mufindi": "TZ04",
    "Mpanda": "TZ28", "Mpanda Urban": "TZ28", "Mlele": "TZ28", "Mpimbwe": "TZ28", "Nsimbo": "TZ28",
    "Moshi": "TZ09", "Moshi Urban": "TZ09", "Hai": "TZ09", "Mwanga": "TZ09", "Rombo": "TZ09", "Same": "TZ09", "Siha": "TZ09",
    "Chake Chake": "TZ10", "Mkoani": "TZ10",
    "Lindi": "TZ12", "Lindi Urban": "TZ12", "Kilwa": "TZ12", "Liwale": "TZ12", "Nachingwea": "TZ12", "Ruangwa": "TZ12",
    "Mjini": "TZ15", "Magharibi A": "TZ15", "Magharibi B": "TZ15",
    "Mtwara": "TZ17", "Mtwara Urban": "TZ17", "Masasi": "TZ17", "Masasi Urban": "TZ17", "Nanyumbu": "TZ17",
    "Newala": "TZ17", "Newala Urban": "TZ17", "Tandahimba": "TZ17",
    "Nyamagana": "TZ18", "Ilemela": "TZ18", "Buchosa": "TZ18", "Kwimba": "TZ18", "Magu": "TZ18", "Misungwi": "TZ18", "Sengerema": "TZ18", "Ukerewe": "TZ18",
    "Bagamoyo": "TZ19", "Chalinze": "TZ19", "Kibaha": "TZ19", "Kibaha Urban": "TZ19", "Kisarawe": "TZ19", "Mafia": "TZ19", "Mkuranga": "TZ19", "Rufiji": "TZ19",
    "Sumbawanga": "TZ20", "Sumbawanga Urban": "TZ20", "Kalambo": "TZ20", "Nkasi": "TZ20",
    "Singida": "TZ23", "Singida Urban": "TZ23", "Ikungi": "TZ23", "Iramba": "TZ23", "Itigi": "TZ23", "Manyoni": "TZ23", "Mkalama": "TZ23",
    "Tabora": "TZ24", "Tabora Urban": "TZ24", "Nzega": "TZ24", "Nzega Urban": "TZ24", "Igunga": "TZ24", "Kaliua": "TZ24", "Sikonge": "TZ24", "Urambo": "TZ24", "Uyui": "TZ24",
};

export class MapComponent extends Component {
    setup() {
        this.mapRef = useRef("map");
        this.notification = useService("notification"); // Initialize Notification Service
        this.map = null;
        this.provinceGeoJson = null;
        this.districtGeoJson = null;
        this.provinceData = {};
        
        // --- State ---
        this.currentLevel = "province";
        this.selectedProvinceCode = null;
        this.activeLabels = [];

        // --- Layers ---
        this.geoJsonLayer = null;
        this.labelLayer = null;
        this.lineLayer = null;

        onWillStart(async () => {
            await loadCSS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");
            await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");

            const style = document.createElement('style');
            style.innerHTML = `
                .map-label {
                    background: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    white-space: nowrap;
                    pointer-events: none;
                    text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                    font-family: sans-serif;
                    z-index: 1000;
                }
                .map-label div {
                    line-height: 1.2;
                    background: transparent !important;
                }
            `;
            document.head.appendChild(style);

            const [provinceRes, districtRes] = await Promise.all([
                fetch("/openg2p_zanzibar_map/static/lib/tz.json"),
                fetch("/openg2p_zanzibar_map/static/lib/geoBoundaries-TZA-ADM2.geojson"),
            ]);

            const fullProvinceData = await provinceRes.json();
            const zanzibarCodes = ["TZ06", "TZ07", "TZ10", "TZ11", "TZ15"];
            this.provinceGeoJson = {
                type: "FeatureCollection",
                features: fullProvinceData.features.filter(feature => 
                    zanzibarCodes.includes(feature.properties?.id)  
                )
                };
            this.districtGeoJson = await districtRes.json();
            this.provinceData = this.computeProvinceData(this.props.data || {});
        });

        onMounted(() => {
            this.renderMap();
        });

        onWillUpdateProps((nextProps) => {
            this.provinceData = this.computeProvinceData(nextProps.data || {});
            this.refreshCurrentLayer();
        });
        
        onWillUnmount(() => {
            if (this.map) {
                this.map.off();
                this.map.remove();
            }
        });
    }

    computeProvinceData(mapData) {
        const result = {};
        if (!this.districtGeoJson?.features) return result;
        for (const feature of this.districtGeoJson.features) {
            const district = feature.properties?.shapeName;
            if (!district) continue;
            const province = DISTRICT_TO_PROVINCE[district];
            if (!province) continue;
            const value = mapData[district] || 0;
            result[province] = (result[province] || 0) + value;
        }
        return result;
    }

    getColor(density) {
        return density > 1000 ? "#0d47a1" :
               density > 500  ? "#1565c0" :
               density > 200  ? "#1976d2" :
               density > 100  ? "#1e88e5" :
               density > 50   ? "#2196f3" :
               density > 20   ? "#42a5f5" :
               density > 10   ? "#64b5f6" :
                                "#90caf9";
    }

    renderMap() {
        const el = this.mapRef.el;
        if (!el) return;
        el.style.width = "100%";
        el.style.height = "100%";
        el.style.minHeight = "400px";

        if (!this.map) {
            this.map = L.map(el, { zoomControl: true, scrollWheelZoom: false, attributionControl: false });
            this.lineLayer = L.layerGroup().addTo(this.map);
            this.labelLayer = L.layerGroup().addTo(this.map);
            this.map.on('zoomend moveend', () => this.updateLabelVisibility());
        }

        this.currentLevel = "province";
        this.selectedProvinceCode = null;
        this.renderProvinceLayer();
    }

    clearGeoLayer() {
        if (this.geoJsonLayer) { 
            this.map.removeLayer(this.geoJsonLayer); 
            this.geoJsonLayer = null; 
        }
        this.labelLayer.clearLayers();
        this.lineLayer.clearLayers();
        this.activeLabels = [];
    }

    refreshCurrentLayer() {
        if (this.map) {
            if (this.currentLevel === "province") this.renderProvinceLayer();
            else if (this.currentLevel === "district" && this.selectedProvinceCode)
                this.renderDistrictLayer(this.selectedProvinceCode);
        }
    }

    createLabel(feature, layer, name, value, total) {
        const percent = total ? ((value / total) * 100).toFixed(1) : 0;
        const bounds = layer.getBounds();
        const center = bounds.getCenter();
        const area = (bounds.getNorthEast().lat - bounds.getSouthWest().lat) * (bounds.getNorthEast().lng - bounds.getSouthWest().lng);
        
        const smallThreshold = this.currentLevel === 'province' ? 0.5 : 0.05; 
        const isSmall = area < smallThreshold;

        let labelPos = center;
        let line = null;



        const fontSize = 12;
        const html = `
            <div style="text-align:center; transform: translate(-50%, -50%);">
                <strong style="font-size:${fontSize}px; color:#222">${name}</strong><br/>
                <span style="font-size:${fontSize - 1}px; color:#444">${value} (${percent}%)</span>
            </div>`;

        const marker = L.marker(labelPos, {
            icon: L.divIcon({ className: "map-label", html: html, iconSize: null }),
            interactive: false,
        });

        this.activeLabels.push({ marker, line, area, labelPos });
        marker.addTo(this.labelLayer);
    }

    updateLabelVisibility() {
        if (!this.map || this.activeLabels.length === 0) return;
        const zoom = this.map.getZoom();
        const occupiedRects = [];
        const sorted = [...this.activeLabels].sort((a, b) => b.area - a.area);

        sorted.forEach(item => {
            const { marker, line, labelPos, area } = item;

            const point = this.map.latLngToContainerPoint(labelPos);
            const w = 80; const h = 40;
            const rect = { left: point.x - w/2, right: point.x + w/2, top: point.y - h/2, bottom: point.y + h/2 };

            let overlap = false;
            for (const occ of occupiedRects) {
                if (rect.left < occ.right && rect.right > occ.left && rect.top < occ.bottom && rect.bottom > occ.top) {
                    overlap = true;
                    break;
                }
            }
          
        });
    }

    setLabelOpacity(item, opacity) {
        const el = item.marker.getElement();
        if (el) el.style.opacity = opacity;
        if (item.line) item.line.setStyle({ opacity: opacity, fillOpacity: opacity });
    }

    renderProvinceLayer() {
        if (!this.map || !this.provinceGeoJson) return;
        this.clearGeoLayer();
        const total = Object.values(this.provinceData).reduce((sum, v) => sum + v, 0);

        this.geoJsonLayer = L.geoJson(this.provinceGeoJson, {
            style: (feature) => {
                const code = feature.properties?.id;
                return { fillColor: this.getColor(this.provinceData[code] || 0), weight: 1, color: "white", dashArray: "3", fillOpacity: 0.7 };
            },
            onEachFeature: (feature, layer) => {
                const code = feature.properties.id;
                const value = this.provinceData[code] || 0;
                
                layer.on("click", () => {
                    // if (this.props.onRegionClick) this.props.onRegionClick({ region: code });
                    this.drillDownToProvince(code);
                });

                this.createLabel(feature, layer, feature.properties.name, value, total);
            }
        }).addTo(this.map);

        this.map.fitBounds(this.geoJsonLayer.getBounds(), { animate: true });
        // const currentZoom = this.map.getZoom();
        // this.map.setZoom(currentZoom + 0.5);
        this.updateLabelVisibility();
    }

    drillDownToProvince(code) {
        // --- NEW: Check if districts exist before drilling down ---
        const hasDistricts = this.districtGeoJson?.features.some(
            f => DISTRICT_TO_PROVINCE[f.properties?.shapeName] === code
        );

        if (!hasDistricts) {
            // Display disappearing alert
            this.notification.add("No district data available for this region.", { 
                type: "warning",
                sticky: false // Allows it to disappear automatically
            });
            return;
        }

        // Proceed if districts exist
        this.currentLevel = "district";
        this.selectedProvinceCode = code;
        this.renderDistrictLayer(code);
    }

    renderDistrictLayer(provinceCode) {
        if (!this.map || !this.districtGeoJson) return;
        this.clearGeoLayer();

        const districtFeatures = this.districtGeoJson.features.filter(f => DISTRICT_TO_PROVINCE[f.properties?.shapeName] === provinceCode);
        const total = districtFeatures.reduce((sum, f) => sum + (this.props.data[f.properties.shapeName] || 0), 0);

        this.geoJsonLayer = L.geoJson({ type: "FeatureCollection", features: districtFeatures }, {
            style: (feature) => {
                const val = this.props.data[feature.properties.shapeName] || 0;
                return { fillColor: this.getColor(val), weight: 1, color: "white", dashArray: "3", fillOpacity: 0.7 };
            },
            onEachFeature: (feature, layer) => {
                const name = feature.properties.shapeName;
                const value = this.props.data[name] || 0;

                layer.on("click", () => this.renderProvinceLayer());

                this.createLabel(feature, layer, name, value, total);
            }
        }).addTo(this.map);

        if (this.geoJsonLayer.getLayers().length) {
            this.map.fitBounds(this.geoJsonLayer.getBounds(), { animate: true });
        }
        
        this.updateLabelVisibility();

        this.map.once("click", (e) => {
            if (e.originalEvent.target.classList.contains('leaflet-container')) {
                this.currentLevel = "province";
                this.selectedProvinceCode = null;
                this.renderProvinceLayer();
            }
        });
    }
}

MapComponent.template = "openg2p_zanzibar_map.MapComponent";
MapComponent.props = {
    data: { type: Object, optional: true },
    onRegionClick: { type: Function, optional: true },
    onDistrictClick: { type: Function, optional: true },
};