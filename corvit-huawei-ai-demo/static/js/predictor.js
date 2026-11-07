/**
 * Corvit Huawei AI Demo — AI Price Predictor page logic.
 *
 * Handles the area/dimensions mode tabs, quick-select plot sizes, an
 * instant client-side unit conversion readout, and submitting to the
 * authoritative /api/predict endpoint. The frontend's own area math
 * mirrors utils/area_converter.py purely for live feedback as the
 * customer types — the backend recomputes and validates everything
 * from scratch, and its response is the only source of the predicted
 * price (see app.py's api_predict).
 */
(function () {
  "use strict";

  // Mirrors config.py's documented conversion constants exactly.
  var SQFT_PER_SQYD = 9;
  var SQM_PER_SQYD = 0.836127;
  var SQYD_PER_ACRE = 4840;

  function toSqyd(value, unit) {
    switch (unit) {
      case "sqft":
        return value / SQFT_PER_SQYD;
      case "sqm":
        return value / SQM_PER_SQYD;
      case "acre":
        return value * SQYD_PER_ACRE;
      default:
        return value;
    }
  }

  function allUnits(valueSqyd) {
    return {
      sqyd: valueSqyd,
      sqft: valueSqyd * SQFT_PER_SQYD,
      sqm: valueSqyd * SQM_PER_SQYD,
      acre: valueSqyd / SQYD_PER_ACRE,
    };
  }

  function fmt(value, decimals) {
    if (!isFinite(value)) return "—";
    return value.toLocaleString(undefined, {
      minimumFractionDigits: decimals || 0,
      maximumFractionDigits: decimals || 0,
    });
  }

  var CURRENCY_CODE = (document.body && document.body.getAttribute("data-currency")) || "PKR";

  function fmtMoney(value) {
    if (!isFinite(value)) return "—";
    return CURRENCY_CODE + " " + Math.round(value).toLocaleString();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("predictor-form");
    if (!form) return; // not on the predictor page

    var MIN_SQYD = parseFloat(document.body.getAttribute("data-min-sqyd")) || 120;
    var MAX_SQYD = parseFloat(document.body.getAttribute("data-max-sqyd")) || 10000;

    var modeTabs = document.querySelectorAll(".mode-tab");
    var areaFields = document.getElementById("mode-area-fields");
    var dimFields = document.getElementById("mode-dimensions-fields");
    var currentMode = "area";

    var inputArea = document.getElementById("input-area");
    var inputRatio = document.getElementById("input-ratio");
    var inputLength = document.getElementById("input-length");
    var inputBreadth = document.getElementById("input-breadth");
    var inputAreaCheck = document.getElementById("input-area-check");
    var inputUnit = document.getElementById("input-unit");
    var inputLocation = document.getElementById("input-location");

    var liveReadout = document.getElementById("live-readout");
    var rangeNote = document.getElementById("range-note");
    var convChips = {
      sqyd: document.getElementById("conv-sqyd"),
      sqft: document.getElementById("conv-sqft"),
      sqm: document.getElementById("conv-sqm"),
      acre: document.getElementById("conv-acre"),
    };

    var formError = document.getElementById("form-error");
    var formErrorText = document.getElementById("form-error-text");
    var predictBtn = document.getElementById("predict-btn");
    var predictBtnLabel = document.getElementById("predict-btn-label");

    var resultEmpty = document.getElementById("result-empty");
    var resultContent = document.getElementById("result-content");

    // ---------------------------------------------------------------
    // Mode tabs
    // ---------------------------------------------------------------
    function setMode(mode) {
      currentMode = mode;
      modeTabs.forEach(function (tab) {
        var active = tab.getAttribute("data-mode") === mode;
        tab.classList.toggle("is-active", active);
        tab.setAttribute("aria-selected", active ? "true" : "false");
      });
      areaFields.hidden = mode !== "area";
      dimFields.hidden = mode !== "dimensions";
      updateLiveReadout();
    }

    modeTabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        setMode(tab.getAttribute("data-mode"));
      });
    });

    // ---------------------------------------------------------------
    // Quick plot-size selection
    // ---------------------------------------------------------------
    var quickChips = document.querySelectorAll("#quick-size-picker .quick-size-chip");
    quickChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        quickChips.forEach(function (c) {
          c.classList.remove("is-selected");
        });
        chip.classList.add("is-selected");

        setMode("area");
        inputUnit.value = "sqyd";
        inputArea.value = chip.getAttribute("data-size");
        updateLiveReadout();
        inputArea.focus();
      });
    });

    // ---------------------------------------------------------------
    // Live area calculation + unit-conversion readout (instant,
    // client-side — see module docstring above).
    // ---------------------------------------------------------------
    function currentAreaSqyd() {
      var unit = inputUnit.value;
      if (currentMode === "area") {
        var area = parseFloat(inputArea.value);
        if (!isFinite(area) || area <= 0) return null;
        return toSqyd(area, unit);
      }
      var length = parseFloat(inputLength.value);
      var breadth = parseFloat(inputBreadth.value);
      if (!isFinite(length) || !isFinite(breadth) || length <= 0 || breadth <= 0) return null;
      return toSqyd(length * breadth, unit);
    }

    function updateLiveReadout() {
      var areaSqyd = currentAreaSqyd();

      if (areaSqyd === null) {
        liveReadout.textContent = "";
        Object.keys(convChips).forEach(function (k) {
          convChips[k].textContent = "—";
        });
        rangeNote.textContent = "";
        return;
      }

      var units = allUnits(areaSqyd);
      convChips.sqyd.textContent = fmt(units.sqyd, 2);
      convChips.sqft.textContent = fmt(units.sqft, 2);
      convChips.sqm.textContent = fmt(units.sqm, 2);
      convChips.acre.textContent = fmt(units.acre, 4);

      var inRange = areaSqyd >= MIN_SQYD && areaSqyd <= MAX_SQYD;

      if (currentMode === "dimensions") {
        liveReadout.textContent = "= " + fmt(units.sqyd, 2) + " sq yd";
      } else {
        liveReadout.textContent = "";
      }

      rangeNote.textContent = inRange
        ? "Within the " + fmt(MIN_SQYD) + "–" + fmt(MAX_SQYD) + " sq yd prediction range."
        : "Outside the " + fmt(MIN_SQYD) + "–" + fmt(MAX_SQYD) + " sq yd prediction range — conversion still works, but a prediction will not be available.";
    }

    [inputArea, inputRatio, inputUnit].forEach(function (el) {
      el.addEventListener("input", updateLiveReadout);
    });
    [inputLength, inputBreadth, inputAreaCheck].forEach(function (el) {
      el.addEventListener("input", updateLiveReadout);
    });

    // ---------------------------------------------------------------
    // Submit -> authoritative backend prediction
    // ---------------------------------------------------------------
    function showError(message) {
      formErrorText.textContent = message;
      formError.hidden = false;
    }

    function clearError() {
      formError.hidden = true;
      formErrorText.textContent = "";
    }

    function setLoading(isLoading) {
      predictBtn.disabled = isLoading;
      predictBtnLabel.innerHTML = isLoading
        ? '<span class="spinner" aria-hidden="true"></span> Predicting…'
        : "Predict property price";
    }

    function renderResult(data) {
      resultEmpty.hidden = true;
      resultContent.hidden = false;

      document.getElementById("result-location-badge").textContent = data.input.location || "Baseline locality";
      document.getElementById("result-price").textContent = data.prediction.predicted_price_formatted;
      document.getElementById("result-price-sub").textContent =
        "≈ " + data.prediction.price_in_crore.toFixed(2) + " crore " + data.prediction.currency;

      document.getElementById("chip-sqyd").textContent = fmtMoney(data.prediction.price_per_sqyd);
      document.getElementById("chip-sqft").textContent = fmtMoney(data.prediction.price_per_sqft);
      document.getElementById("chip-acre").textContent = fmtMoney(data.prediction.price_per_acre);
      document.getElementById("chip-area").textContent = fmt(data.input.area.sqyd, 2);

      var dims = data.input.dimensions;
      var dimsLabel = fmt(dims.length_sqyd, 2) + " × " + fmt(dims.breadth_sqyd, 2) + " yd" +
        (dims.estimated ? " (estimated)" : "");

      var metaRows = [
        ["Dimensions used", dimsLabel],
        ["Locality used", data.input.location || "Baseline"],
        ["Area in square meters", fmt(data.input.area.sqm, 2) + " m²"],
        ["Area in acres", fmt(data.input.area.acre, 4) + " acres"],
      ];
      document.getElementById("result-meta-list").innerHTML = metaRows
        .map(function (row) {
          return '<div class="result-meta-row"><span class="k">' + row[0] + '</span><span class="v">' + row[1] + "</span></div>";
        })
        .join("");

      document.getElementById("result-disclaimer").textContent = data.disclaimer;

      if (window.ChartsApp) {
        window.ChartsApp.renderSizeVsPrice(
          "sizeVsPriceChart",
          data.input.location,
          { x: data.input.area.sqyd, y: data.prediction.predicted_price }
        );
      }

      resultContent.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      clearError();

      var payload = {
        unit: inputUnit.value,
        location: inputLocation.value,
      };

      if (currentMode === "area") {
        if (!inputArea.value) {
          showError("Please enter a plot area.");
          return;
        }
        payload.area = inputArea.value;
        if (inputRatio.value) payload.ratio = inputRatio.value;
      } else {
        if (!inputLength.value || !inputBreadth.value) {
          showError("Please enter both plot length and breadth.");
          return;
        }
        payload.length = inputLength.value;
        payload.breadth = inputBreadth.value;
        if (inputAreaCheck.value) payload.area = inputAreaCheck.value;
      }

      setLoading(true);

      fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (response) {
          return response.json().then(function (body) {
            return { ok: response.ok, body: body };
          });
        })
        .then(function (result) {
          setLoading(false);
          if (!result.ok || !result.body.success) {
            showError(result.body.error || "Could not generate a prediction.");
            return;
          }
          renderResult(result.body.data);
        })
        .catch(function () {
          setLoading(false);
          showError("Could not reach the prediction service. Please try again.");
        });
    });

    // ---------------------------------------------------------------
    // Initial state
    // ---------------------------------------------------------------
    setMode("area");
    if (inputArea.value) updateLiveReadout();
    if (window.ChartsApp) {
      window.ChartsApp.renderSizeVsPrice("sizeVsPriceChart", inputLocation.value, null);
    }
  });
})();
