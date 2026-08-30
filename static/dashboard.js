// ============================================================
// AIRFARE INTELLIGENCE - DASHBOARD
// ============================================================

// -------------------------
// MONEY FORMAT
// -------------------------

const money = (value) => {
    if (value === null || value === undefined || isNaN(Number(value))) {
        return "—";
    }

    return "₹" + Number(value).toLocaleString("en-IN", {
        maximumFractionDigits: 0
    });
};


// -------------------------
// API HELPER
// -------------------------

async function fetchJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
}


// -------------------------
// CHART STORAGE
// -------------------------

const charts = {};


// -------------------------
// CHART DEFAULTS
// -------------------------

if (typeof Chart !== "undefined") {
    Chart.defaults.font.family = "Inter, Arial, sans-serif";
    Chart.defaults.animation.duration = 1000;
}


// ============================================================
// LINE CHART
// ============================================================

function createLineChart(canvasId, labels, data, label, currency = false) {

    const canvas = document.getElementById(canvasId);

    if (!canvas) {
        console.warn(`Canvas #${canvasId} not found`);
        return;
    }

    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    charts[canvasId] = new Chart(canvas, {
        type: "line",

        data: {
            labels: labels,

            datasets: [{
                label: label,
                data: data,
                borderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.4,
                fill: true,

                backgroundColor: "rgba(20,150,225,0.10)",
                borderColor: "#1496E1",
                pointBackgroundColor: "#1496E1"
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            interaction: {
                intersect: false,
                mode: "index"
            },

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    backgroundColor: "#071C2F",
                    padding: 12,

                    callbacks: {
                        label: function(context) {

                            const value = context.parsed.y;

                            return currency
                                ? " " + money(value)
                                : " " + Number(value).toFixed(2);
                        }
                    }
                }
            },

            scales: {
                x: {
                    grid: {
                        display: false
                    },

                    ticks: {
                        color: "#6B8295"
                    }
                },

                y: {
                    beginAtZero: false,

                    grid: {
                        color: "rgba(20,100,150,0.08)"
                    },

                    ticks: {
                        color: "#6B8295",

                        callback: function(value) {
                            return currency ? money(value) : value;
                        }
                    }
                }
            }
        }
    });
}


// ============================================================
// ROUTE BAR CHART
// ============================================================

function createRouteChart(routeData) {

    const canvas = document.getElementById("routeChart");

    if (!canvas) {
        console.warn("Route chart canvas not found");
        return;
    }

    if (charts.routeChart) {
        charts.routeChart.destroy();
    }

    charts.routeChart = new Chart(canvas, {
        type: "bar",

        data: {
            labels: routeData.map(
                item => `${item.origin} → ${item.destination}`
            ),

            datasets: [{
                data: routeData.map(
                    item => Number(item.average_fare)
                ),

                borderRadius: 8,
                borderSkipped: false,

                backgroundColor: "rgba(20,150,225,0.75)",
                hoverBackgroundColor: "#1496E1"
            }]
        },

        options: {
            indexAxis: "y",

            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    backgroundColor: "#071C2F",
                    padding: 12,

                    callbacks: {
                        label: function(context) {
                            return " Average Fare: " +
                                money(context.parsed.x);
                        }
                    }
                }
            },

            scales: {
                x: {
                    beginAtZero: true,

                    grid: {
                        color: "rgba(20,100,150,0.08)"
                    },

                    ticks: {
                        color: "#6B8295",

                        callback: function(value) {
                            return money(value);
                        }
                    }
                },

                y: {
                    grid: {
                        display: false
                    },

                    ticks: {
                        color: "#263B4D"
                    }
                }
            }
        }
    });
}


// ============================================================
// SUMMARY CARDS
// ============================================================

function updateSummary(
    summaryData,
    monthlyIndexData,
    routeData,
    predictionData
) {

    const avg = document.getElementById("avg");
    const idx = document.getElementById("idx");
    const routes = document.getElementById("routes");
    const preds = document.getElementById("preds");


    // CURRENT MARKET AVERAGE FARE
    if (avg) {
        avg.textContent = money(
            summaryData.avg_market_fare
        );
    }


    // LATEST MONTHLY PRICE INDEX
    if (idx) {

        if (monthlyIndexData && monthlyIndexData.length) {

            const sorted = [...monthlyIndexData].sort(
                (a, b) =>
                    new Date(a.index_month) -
                    new Date(b.index_month)
            );

            const latest =
                sorted[sorted.length - 1];

            idx.textContent =
                Number(latest.index_value).toFixed(2);

        } else {
            idx.textContent = "—";
        }
    }


    // NUMBER OF ROUTES
    if (routes) {
        routes.textContent = routeData.length;
    }


    // NUMBER OF ML PREDICTIONS
    if (preds) {

        preds.textContent =
            Number(
                summaryData.total_predictions ||
                predictionData.length ||
                0
            ).toLocaleString("en-IN");
    }
}


// ============================================================
// MONTHLY AIRFARE PRICE INDEX
// ============================================================

function renderMonthlyIndexChart(data) {

    if (!data || !data.length) {
        console.warn("No monthly index data available");
        return;
    }


    const sorted = [...data].sort(
        (a, b) =>
            new Date(a.index_month) -
            new Date(b.index_month)
    );


    const labels = sorted.map(item => {

        const date = new Date(item.index_month);

        return date.toLocaleDateString("en-IN", {
            month: "short",
            year: "numeric"
        });
    });


    const values = sorted.map(
        item => Number(item.index_value)
    );


    createLineChart(
        "indexChart",
        labels,
        values,
        "Monthly Airfare Price Index",
        false
    );
}


// ============================================================
// LEAD-TIME FARE CURVE
// ============================================================

function renderLeadTimeChart(data) {

    if (!data || !data.length) {
        console.warn("No lead-time data available");
        return;
    }


    const sorted = [...data].sort(
        (a, b) =>
            Number(a.advance_days) -
            Number(b.advance_days)
    );


    createLineChart(
        "leadChart",

        sorted.map(
            item => "T+" + item.advance_days
        ),

        sorted.map(
            item => Number(item.weighted_fare)
        ),

        "Weighted Fare",

        true
    );
}


// ============================================================
// FARE HEATMAP
// ============================================================

function renderHeatmap(data) {

    const container =
        document.getElementById("heatmap");

    if (!container) {
        return;
    }


    if (!data || !data.length) {

        container.innerHTML = `
            <div class="rec">
                No heatmap data available.
            </div>
        `;

        return;
    }


    const days = [
        ...new Set(
            data.map(
                item => Number(item.advance_days)
            )
        )
    ].sort((a, b) => a - b);


    const routes = [
        ...new Set(
            data.map(
                item =>
                    `${item.origin}-${item.destination}`
            )
        )
    ];


    const fares = data
        .map(item => Number(item.average_fare))
        .filter(value => !isNaN(value));


    if (!fares.length) {
        return;
    }


    const minFare = Math.min(...fares);
    const maxFare = Math.max(...fares);


    container.style.gridTemplateColumns =
        `180px repeat(${days.length}, minmax(100px,1fr))`;


    container.innerHTML = `
        <div class="hmh route-heading">
            ROUTE
        </div>
    `;


    days.forEach(day => {

        container.innerHTML += `
            <div class="hmh">
                T+${day}
            </div>
        `;
    });


    routes.forEach(route => {

        const [origin, destination] =
            route.split("-");


        container.innerHTML += `
            <div class="hmr">
                ${origin} → ${destination}
            </div>
        `;


        days.forEach(day => {

            const item = data.find(
                row =>
                    row.origin === origin &&
                    row.destination === destination &&
                    Number(row.advance_days) === day
            );


            if (!item) {

                container.innerHTML += `
                    <div class="hmc empty">
                        —
                    </div>
                `;

                return;
            }


            const fare =
                Number(item.average_fare);


            const intensity =
                (fare - minFare) /
                (maxFare - minFare || 1);


            const alpha =
                0.12 + intensity * 0.68;


            container.innerHTML += `
                <div
                    class="hmc"
                    style="
                        background: rgba(
                            20,
                            150,
                            225,
                            ${alpha}
                        );
                    "
                    title="${origin} → ${destination} | T+${day} | ${money(fare)}"
                >
                    ${money(fare)}
                </div>
            `;
        });
    });
}


// ============================================================
// PREDICTION ROUTE SELECTOR
// ============================================================

function setupPredictionSelector(predictionData) {

    const select =
        document.getElementById("routeSelect");

    if (!select) {
        return;
    }


    const routes = [
        ...new Set(
            predictionData.map(
                item =>
                    `${item.origin}-${item.destination}`
            )
        )
    ].sort();


    select.innerHTML =
        `<option value="">All routes</option>`;


    routes.forEach(route => {

        const [origin, destination] =
            route.split("-");


        select.innerHTML += `
            <option value="${route}">
                ${origin} → ${destination}
            </option>
        `;
    });


    select.onchange = async function() {

        try {

            const selected =
                select.value;


            let data;


            if (selected) {

                data = await fetchJSON(
                    "/api/predictions?route=" +
                    encodeURIComponent(selected)
                );

            } else {

                data = predictionData;
            }


            renderPredictions(data);

        } catch (error) {

            console.error(
                "Prediction filter error:",
                error
            );
        }
    };
}


// ============================================================
// ML FUTURE PREDICTIONS
// ============================================================

function renderPredictions(data) {

    const container =
        document.getElementById("predictionList");

    if (!container) {
        return;
    }


    if (!data || !data.length) {

        container.innerHTML = `
            <div class="pred">
                No prediction data available.
            </div>
        `;

        return;
    }


    container.innerHTML =
        data
            .slice(0, 80)
            .map(item => `

                <div class="pred">

                    <div>
                        <b>
                            ${item.origin}
                            →
                            ${item.destination}
                        </b>

                        <br>

                        <span class="airline">
                            ${item.airline}
                        </span>
                    </div>

                    <div>
                        T+${item.advance_days}
                    </div>

                    <b>
                        ${money(item.predicted_fare)}
                    </b>

                </div>

            `)
            .join("");
}


// ============================================================
// BOOKING RECOMMENDATIONS
// ============================================================

async function loadRecommendations() {

    const container =
        document.getElementById("recommendations");

    if (!container) {
        return;
    }


    try {

        const data =
            await fetchJSON(
                "/api/recommendations"
            );


        if (!data || !data.length) {

            container.innerHTML = `
                <div class="rec">
                    <small>
                        No booking recommendations available.
                    </small>
                </div>
            `;

            return;
        }


        container.innerHTML =
            data.map(item => `

                <div class="rec">

                    <div class="rec-route">

                        <strong>
                            ${item.origin}
                            →
                            ${item.destination}
                        </strong>

                        <span class="rec-window">
                            T+${item.recommended_advance_days}
                        </span>

                    </div>

                    <div class="rec-fare">

                        <b>
                            ${money(
                                item.recommended_average_fare
                            )}
                        </b>

                        <small>
                            Recommended average fare
                        </small>

                    </div>

                    <small class="rec-message">
                        ${item.recommendation || ""}
                    </small>

                </div>

            `).join("");


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );


        container.innerHTML = `
            <div class="rec">
                <small>
                    Unable to load recommendations.
                </small>
            </div>
        `;
    }
}


// ============================================================
// MAIN DASHBOARD
// ============================================================

async function loadDashboard() {

    console.log(
        "Loading AirFare Intelligence..."
    );


    try {

        const [

            summaryData,

            leadTimeIndexData,

            monthlyIndexData,

            routeData,

            heatmapData,

            predictionData

        ] = await Promise.all([

            fetchJSON("/api/summary"),

            fetchJSON("/api/index"),

            fetchJSON("/api/monthly-index"),

            fetchJSON("/api/routes"),

            fetchJSON("/api/heatmap"),

            fetchJSON("/api/predictions")

        ]);


        console.log(
            "All dashboard data loaded."
        );


        // -------------------------
        // SUMMARY
        // -------------------------

        updateSummary(
            summaryData,
            monthlyIndexData,
            routeData,
            predictionData
        );


        // -------------------------
        // MONTHLY PRICE INDEX
        // -------------------------

        renderMonthlyIndexChart(
            monthlyIndexData
        );


        // -------------------------
        // ROUTE ANALYTICS
        // -------------------------

        createRouteChart(
            routeData
        );


        // -------------------------
        // LEAD-TIME CURVE
        // -------------------------

        renderLeadTimeChart(
            leadTimeIndexData
        );


        // -------------------------
        // HEATMAP
        // -------------------------

        renderHeatmap(
            heatmapData
        );


        // -------------------------
        // PREDICTIONS
        // -------------------------

        setupPredictionSelector(
            predictionData
        );

        renderPredictions(
            predictionData
        );


        // -------------------------
        // RECOMMENDATIONS
        // -------------------------

        await loadRecommendations();


        console.log(
            "AIRFARE DASHBOARD READY"
        );

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

        showDashboardError();
    }
}


// ============================================================
// ERROR MESSAGE
// ============================================================

function showDashboardError() {

    const old =
        document.getElementById(
            "dashboard-error"
        );

    if (old) {
        old.remove();
    }


    const message =
        document.createElement("div");


    message.id =
        "dashboard-error";


    message.style.cssText = `
        position:fixed;
        bottom:20px;
        right:20px;
        padding:16px 20px;
        background:#071C2F;
        color:white;
        border-radius:12px;
        z-index:9999;
        font-family:Inter,Arial;
        box-shadow:0 10px 30px rgba(0,0,0,.2);
    `;


    message.innerHTML = `
        <strong>
            Dashboard data error
        </strong>
        <br>
        <small>
            Check Flask, MySQL and API endpoints.
        </small>
    `;


    document.body.appendChild(message);


    setTimeout(() => {
        message.remove();
    }, 6000);
}


// ============================================================
// START
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);