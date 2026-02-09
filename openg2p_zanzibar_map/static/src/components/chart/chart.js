/** @odoo-module */
/* global Chart */

import { Component, onMounted, onWillStart, onWillUpdateProps, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartComponent extends Component {
    setup() {
        this.canvasRef = useRef("canvas");
        this.chartInstance = null;

        onWillStart(async () => {
            // Load Chart.js and the Datalabels plugin
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js");
            await loadJS("https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0");
            // Register the datalabels plugin globally once it's loaded
            // if (Chart && ChartDataLabels) {
            //     Chart.register(ChartDataLabels);
            // }
        });

        onMounted(() => this.renderChart());

        onWillUpdateProps(() => {
            if (this.chartInstance) {
                this.chartInstance.destroy();
                this.chartInstance = null;
            }
        });
    }

    patched() {
        if (this.canvasRef.el && !this.chartInstance) {
            this.renderChart();
        }
    }

  renderChart() {
        if (!this.canvasRef.el || !this.props.labels || !this.props.data) return;
        const ctx = this.canvasRef.el.getContext("2d");

        // Base options with datalabels enabled and sensible defaults
        let baseOptions = {
            maintainAspectRatio: false,
            layout: {
                padding: 10
            },
            plugins: {
                legend: {
                    display: false, // Default legend display
                },
                datalabels: {
                       display: (context) => {
                        const value = context.dataset.data[context.dataIndex];
                        return value !== 0;
                    },
                    color: '#ffffff', // Changed to white for visibility
                    font: {
                        weight: 'bold',
                        size: 11
                    },
                    anchor: 'center',
                    align: 'center',  // For pie/doughnut charts, 'end' often works better
                    textAlign: 'center',
                    formatter: (value, context) => {
                        const label = this.props.labels[context.dataIndex] || "";
                        const dataset = context.chart.data.datasets[0].data;
                        const sum = dataset.reduce((a, b) => a + b, 0);
                        const percentage = sum > 0 ? ((value * 100) / sum).toFixed(0) + "%" : "0%";
                        return `${label}\n${value} (${percentage})`;
                    },
                    textShadowBlur: 3,
                    textShadowColor: 'rgba(0, 0, 0, 0.5)',
                }
            }
        };

        // Deep merge for plugins, shallow merge for other options
        let finalOptions = { ...baseOptions, ...(this.props.options || {}) };

        if (this.props.options && this.props.options.plugins) {
            finalOptions.plugins = {
                ...baseOptions.plugins, // Start with base plugins
                ...(this.props.options.plugins || {}), // Merge custom plugins from props
            };
            // Ensure datalabels from baseOptions are not lost if props.options.plugins
            // doesn't explicitly define them or overrides them partially
            finalOptions.plugins.datalabels = {
                ...(baseOptions.plugins.datalabels || {}),
                ...(this.props.options.plugins.datalabels || {})
            };
            // Ensure legend from baseOptions is not lost if props.options.plugins
            // doesn't explicitly define them or overrides them partially
            finalOptions.plugins.legend = {
                ...(baseOptions.plugins.legend || {}),
                ...(this.props.options.plugins.legend || {})
            };
        }

        this.chartInstance = new Chart(ctx, {
            type: this.props.type,
            data: {
                labels: this.props.labels,
                datasets: [{
                    data: this.props.data,
                    backgroundColor: this.props.backgroundColor,
                    borderWidth: 1,
                }],
            },
            plugins: [ChartDataLabels],
            options: finalOptions, // Use the carefully merged options
        });
    }
}
// ... props remain the same
ChartComponent.template = "g2p_social_registry_dashboard.ChartTemplate";

ChartComponent.props = {
    type: { type: String, optional: true },
    labels: { type: Array, optional: true },
    title: { type: String, optional: true },
    data_label: { type: String, optional: true },
    data: { type: Array, optional: true },
    backgroundColor: { type: Array, optional: true },
    options: { type: Object, optional: true },
    size: { type: String, optional: true },
    chartType: { type: String, optional: true },
    onSegmentClick: { type: Function, optional: true },
};
