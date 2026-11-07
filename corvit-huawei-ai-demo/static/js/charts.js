/**
 * Corvit Huawei AI Demo — Chart.js chart builders.
 *
 * Every chart here is drawn from real numbers fetched from the Flask
 * JSON API (ml/predict.py, ml/train_model.py's saved test predictions,
 * and the live dataset) — nothing is invented client-side. Exposed as
 * window.ChartsApp so predictor.js and the insights page's inline
 * script can call into it without a bundler.
 */
(function () {
  "use strict";

  var CYAN = "#26d9e5";
  var BLUE = "#4c68f0";
  var INK_600 = "#8a96b8";
  var DANGER = "#ff5470";

  var CURRENCY_CODE = (document.body && document.body.getAttribute("data-currency")) || "PKR";

  var charts = {}; // canvasId -> Chart.js instance

  function fmtCrore(value) {
    return (value / 10000000).toFixed(2) + " Cr";
  }

  function fmtShortMoney(value) {
    if (Math.abs(value) >= 10000000) return (value / 10000000).toFixed(1) + "Cr";
    if (Math.abs(value) >= 100000) return (value / 100000).toFixed(1) + "L";
    return value.toLocaleString();
  }

  function fetchJSON(url) {
    return fetch(url)
      .then(function (r) {
        return r.json().then(function (body) {
          return { ok: r.ok, body: body };
        });
      })
      .then(function (result) {
        if (!result.ok || !result.body.success) {
          throw new Error((result.body && result.body.error) || "Request failed");
        }
        return result.body.data;
      });
  }

  function baseGridOptions() {
    return {
      grid: { color: "rgba(238, 242, 252, 0.07)" },
      ticks: { color: INK_600, font: { family: "IBM Plex Sans, sans-serif", size: 11 } },
    };
  }

  function destroyIfExists(canvasId) {
    if (charts[canvasId]) {
      charts[canvasId].destroy();
      delete charts[canvasId];
    }
  }

  // ------------------------------------------------------------------
  // Chart 1 / 4: plot size vs predicted price, with the current plot
  // highlighted as a marker (Predictor page).
  // ------------------------------------------------------------------
  function renderSizeVsPrice(canvasId, location, marker) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return Promise.resolve();

    var url = "/api/sample-predictions" + (location ? "?location=" + encodeURIComponent(location) : "");
    return fetchJSON(url).then(function (points) {
      var linePoints = points.map(function (p) {
        return { x: p.area_sqyd, y: p.predicted_price };
      });

      var datasets = [
        {
          type: "line",
          label: "Predefined plot sizes",
          data: linePoints,
          borderColor: BLUE,
          backgroundColor: "rgba(76, 104, 240, 0.12)",
          pointBackgroundColor: BLUE,
          pointRadius: 4,
          borderWidth: 2,
          tension: 0.25,
          fill: true,
        },
      ];

      if (marker && isFinite(marker.x) && isFinite(marker.y)) {
        datasets.push({
          type: "scatter",
          label: "Your plot",
          data: [marker],
          backgroundColor: CYAN,
          borderColor: "#06100f",
          borderWidth: 2,
          pointRadius: 8,
          pointHoverRadius: 9,
          showLine: false,
        });
      }

      destroyIfExists(canvasId);
      charts[canvasId] = new Chart(canvas.getContext("2d"), {
        type: "line",
        data: { datasets: datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "nearest", intersect: false },
          plugins: {
            legend: { labels: { color: INK_600, font: { size: 11 } } },
            tooltip: {
              callbacks: {
                label: function (ctx) {
                  return ctx.dataset.label + ": " + Math.round(ctx.parsed.x).toLocaleString() +
                    " sq yd → " + CURRENCY_CODE + " " + Math.round(ctx.parsed.y).toLocaleString();
                },
              },
            },
          },
          scales: {
            x: Object.assign({ type: "linear", title: { display: true, text: "Plot area (sq yd)", color: INK_600 } }, baseGridOptions()),
            y: Object.assign(
              { title: { display: true, text: "Predicted price (" + CURRENCY_CODE + ")", color: INK_600 },
                ticks: { color: INK_600, callback: function (v) { return fmtShortMoney(v); } } },
              { grid: baseGridOptions().grid }
            ),
          },
        },
      });
    }).catch(function (err) {
      console.error("size-vs-price chart failed:", err);
    });
  }

  // ------------------------------------------------------------------
  // Chart 2: actual vs. predicted price on the held-out test set
  // (Model Insights page).
  // ------------------------------------------------------------------
  function renderActualVsPredicted(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return Promise.resolve();

    return fetchJSON("/api/test-predictions").then(function (points) {
      var scatterData = points.map(function (p) {
        return { x: p.actual_price, y: p.predicted_price };
      });

      var allValues = points.reduce(function (acc, p) {
        acc.push(p.actual_price, p.predicted_price);
        return acc;
      }, []);
      var lo = Math.min.apply(null, allValues);
      var hi = Math.max.apply(null, allValues);

      destroyIfExists(canvasId);
      charts[canvasId] = new Chart(canvas.getContext("2d"), {
        type: "scatter",
        data: {
          datasets: [
            {
              label: "Test-set properties",
              data: scatterData,
              backgroundColor: "rgba(38, 217, 229, 0.75)",
              pointRadius: 3.5,
            },
            {
              type: "line",
              label: "Perfect prediction (y = x)",
              data: [
                { x: lo, y: lo },
                { x: hi, y: hi },
              ],
              borderColor: INK_600,
              borderDash: [6, 5],
              borderWidth: 1.5,
              pointRadius: 0,
              fill: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: INK_600, font: { size: 11 } } },
            tooltip: {
              callbacks: {
                label: function (ctx) {
                  return "Actual " + fmtShortMoney(ctx.parsed.x) + " / Predicted " + fmtShortMoney(ctx.parsed.y);
                },
              },
            },
          },
          scales: {
            x: Object.assign({ type: "linear", title: { display: true, text: "Actual price", color: INK_600 },
              ticks: { color: INK_600, callback: function (v) { return fmtShortMoney(v); } } }, { grid: baseGridOptions().grid }),
            y: Object.assign({ type: "linear", title: { display: true, text: "Predicted price", color: INK_600 },
              ticks: { color: INK_600, callback: function (v) { return fmtShortMoney(v); } } }, { grid: baseGridOptions().grid }),
          },
        },
      });
    }).catch(function (err) {
      console.error("actual-vs-predicted chart failed:", err);
    });
  }

  // ------------------------------------------------------------------
  // Chart 3: sample property-price distribution (Model Insights page).
  // ------------------------------------------------------------------
  function renderPriceDistribution(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return Promise.resolve();

    return fetchJSON("/api/dataset-stats").then(function (stats) {
      var edges = stats.price_histogram.bin_edges;
      var counts = stats.price_histogram.counts;
      var labels = counts.map(function (_, i) {
        return fmtCrore(edges[i]) + "–" + fmtCrore(edges[i + 1]);
      });

      destroyIfExists(canvasId);
      charts[canvasId] = new Chart(canvas.getContext("2d"), {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Properties (synthetic dataset, n=" + stats.total_records + ")",
              data: counts,
              backgroundColor: "rgba(76, 104, 240, 0.55)",
              borderColor: BLUE,
              borderWidth: 1,
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: INK_600, font: { size: 11 } } } },
          scales: {
            x: Object.assign({ title: { display: true, text: "Price range (crore " + CURRENCY_CODE + ")", color: INK_600 } }, baseGridOptions()),
            y: Object.assign({ title: { display: true, text: "Number of properties", color: INK_600 }, beginAtZero: true }, baseGridOptions()),
          },
        },
      });
    }).catch(function (err) {
      console.error("price distribution chart failed:", err);
    });
  }

  // ------------------------------------------------------------------
  // Dataset statistics table, by locality (Model Insights page).
  // ------------------------------------------------------------------
  function renderLocalityTable(tbodyId, noteId) {
    var tbody = document.getElementById(tbodyId);
    if (!tbody) return Promise.resolve();

    return fetchJSON("/api/dataset-stats").then(function (stats) {
      var entries = Object.keys(stats.records_per_location).map(function (loc) {
        return { loc: loc, count: stats.records_per_location[loc] };
      });
      entries.sort(function (a, b) {
        return b.count - a.count;
      });

      tbody.innerHTML = entries
        .map(function (e) {
          var pct = ((e.count / stats.total_records) * 100).toFixed(1);
          return (
            "<tr><td>" + e.loc + "</td><td>" + e.count.toLocaleString() +
            "</td><td>" + pct + "%</td></tr>"
          );
        })
        .join("");

      var note = document.getElementById(noteId);
      if (note) {
        note.textContent =
          stats.total_records.toLocaleString() + " synthetic records · area " +
          Math.round(stats.min_area_sqyd).toLocaleString() + "–" + Math.round(stats.max_area_sqyd).toLocaleString() +
          " sq yd · price " + fmtCrore(stats.min_price) + "–" + fmtCrore(stats.max_price);
      }
    }).catch(function (err) {
      tbody.innerHTML = '<tr><td colspan="3">Could not load dataset statistics.</td></tr>';
      console.error("locality table failed:", err);
    });
  }

  window.ChartsApp = {
    renderSizeVsPrice: renderSizeVsPrice,
    renderActualVsPredicted: renderActualVsPredicted,
    renderPriceDistribution: renderPriceDistribution,
    renderLocalityTable: renderLocalityTable,
  };
})();
