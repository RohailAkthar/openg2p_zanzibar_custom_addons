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
        const defaultColors = [
            '#3b82f6', // Blue
            '#ec4899', // Pink
            '#8b5cf6', // Violet
            '#10b981', // Emerald
            '#f59e0b', // Amber
            '#06b6d4', // Cyan
            '#ef4444', // Red
            '#6366f1'  // Indigo
        ];

        // Ensure Bar charts use multiple colors if only one is provided
        let bgColors = this.props.backgroundColor;
        if (!bgColors || bgColors.length <= 1) {
            bgColors = defaultColors.slice(0, this.props.data.length);
        }
        // Base options with datalabels enabled and sensible defaults
        let baseOptions = {
            maintainAspectRatio: false,
            onClick: (event, elements) => {
                if (elements.length > 0 && this.props.onSegmentClick) {
                    const index = elements[0].index;
                    const label = this.props.labels[index];
                    const value = this.props.data[index];

                    // Send info back to ZDashboard
                    this.props.onSegmentClick({
                        chartType: this.props.chartType,
                        label: label,
                        value: value
                    });
                }
            },
            scales: {
                x: {
                    display: this.props.type === 'bar',
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    display: this.props.type === 'bar',
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                }
            },
            layout: {
                padding: {
                    top: 0,
                    bottom: 20,      /* Increased bottom padding for X-axis labels */
                    left: 10,
                    right: 40        /* Increased right padding for "500" label */
                }
            },
            plugins: {
                legend: {
                    display: false,
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 12,
                        font: {
                            size: 11
                        }
                    }
                },
                datalabels: {
                    display: (context) => {
                        const value = context.dataset.data[context.dataIndex];
                        return value !== 0;
                    },
                    color: '#000000',    /* Changed to black for better visibility */
                    font: {
                        weight: 'bold',
                        size: 11
                    },
                    anchor: 'center',
                    align: 'center',
                    textAlign: 'center',
                    formatter: (value, context) => {
                        const type = context.chart.config.type;
                        if (type === 'bar') {
                            return value;
                        }
                        const label = this.props.labels[context.dataIndex] || "";
                        const dataset = context.chart.data.datasets[0].data;
                        const sum = dataset.reduce((a, b) => a + b, 0);
                        const percentage = sum > 0 ? ((value * 100) / sum).toFixed(0) + "%" : "0%";
                        return `${label}\n${value} (${percentage})`;
                    },
                    textShadowBlur: 2,
                    textShadowColor: 'rgba(255, 255, 255, 0.4)', /* Light shadow for black text */
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
                    backgroundColor: bgColors,
                    borderWidth: 1,
                    hoverOffset: 0,  /* Correct place to disable pop-out effect */
                }],
            },
            plugins: [ChartDataLabels],
            options: finalOptions,
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
