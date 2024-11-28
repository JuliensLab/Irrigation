// scripts/dataManager.js

// Global Variables
let sensorData = [];
let containerDataArray = [];
let organizedData = {};
let currentSource = "short"; // Default data source
let refreshTimeout; // To store the timeout ID
let latest_datetime_utc = null;

// Helper Function: Convert UTC to Local Time
function convertUTCToLocal(utcDateTime) {
  const date = new Date(utcDateTime + " UTC");
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// Helper Function: Calculate Time Ago
function timeAgo(latest_datetime) {
  const now = new Date();
  const latestDate = new Date(latest_datetime + " UTC");
  const diffMs = now - latestDate;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return `${diffSeconds}s ago`;
  } else if (diffMinutes < 60) {
    const seconds = diffSeconds % 60;
    return `${diffMinutes}m${seconds}s ago`;
  } else if (diffHours < 24) {
    const minutes = diffMinutes % 60;
    return `${diffHours}h${minutes}m ago`;
  } else {
    return `>1d ago`;
  }
}

// Function: Update Datetime Display
function updateTime() {
  if (latest_datetime_utc)
    document.getElementById("datetime").innerHTML = `${convertUTCToLocal(latest_datetime_utc)} | ${timeAgo(latest_datetime_utc)}`;
}

// Initialize Time Update Interval
setInterval(updateTime, 1000);

// Function: Organize Container Data by container_id
function organizeContainerData() {
  organizedData = {}; // Reset organizedData

  containerDataArray.forEach((item) => {
    const { container_id, ...rest } = item;
    if (!organizedData[container_id]) {
      organizedData[container_id] = [];
    }
    // Initialize pump_ml_cumul with pump_ml_added
    rest.pump_ml_cumul = rest.pump_ml_added;
    organizedData[container_id].push(rest);
  });

  // Sort each container's data by sensor_data_id
  for (const containerId in organizedData) {
    organizedData[containerId].sort((a, b) => a.sensor_data_id - b.sensor_data_id);
  }

  // Convert cumulative to added ml
  for (const containerId in organizedData) {
    const array = organizedData[containerId];
    if (array.length > 0) {
      array[0].pump_ml_added = null; // First entry has no previous data to subtract
      for (let i = 1; i < array.length; i++) {
        array[i].pump_ml_added = array[i].pump_ml_cumul - array[i - 1].pump_ml_cumul;
      }
    }
  }
}

// Function: Update Container Charts via chartManager.js
function processContainerDataAndUpdateCharts() {
  organizeContainerData();

  // Update Container Charts via chartManager.js
  updateContainerCharts(organizedData, sensorData);
}

// Function: Update Sensor Charts via chartManager.js
function processSensorData() {
  if (sensorData.length === 0) return;

  sensorData.sort((a, b) => a.id - b.id);
  latest_datetime_utc = sensorData[sensorData.length - 1].date_time;

  sensorData.forEach((data, index) => {
    sensorData[index].date_time = convertUTCToLocal(data.date_time);
  });

  const cpuTemps = sensorData.map((sensor) => sensor.cpu_temp);
  const roomTempsSHT40 = sensorData.map((sensor) => sensor.room_temp_SHT40);
  const roomTempsBMP280 = sensorData.map((sensor) => sensor.room_temp_BMP280);
  const roomHumiditySHT40 = sensorData.map((sensor) => sensor.room_humidity_SHT40);
  const roomPressureBMP280 = sensorData.map((sensor) => sensor.room_pressure_BMP280);
  const labels = sensorData.map((sensor) => sensor.date_time.slice(11)); // Extract time portion

  // Update Sensor Charts via chartManager.js
  updateSensorCharts({
    cpuTemps,
    roomTempsSHT40,
    roomTempsBMP280,
    roomHumiditySHT40,
    roomPressureBMP280,
    labels,
  });
}

// Function: Process All Data and Update Charts
function processDataAndUpdateCharts() {
  processSensorData();
  processContainerDataAndUpdateCharts();
}

// Function: Fetch Data from API and Refresh Charts
const refreshMs = 30000;
function refreshData() {
  if (refreshTimeout) clearTimeout(refreshTimeout);

  const apiUrl = `https://irrigationmars.com/api/get_data.php?source=${currentSource}`;

  fetch(apiUrl)
    .then((response) => response.json())
    .then((data) => {
      sensorData = data.sensorData;
      containerDataArray = data.containerData;
      currentSource = data.source; // Update current source based on response

      const scrollPosition = window.scrollY;

      // Process and Update Charts
      processDataAndUpdateCharts();

      // Schedule Next Refresh
      refreshTimeout = setTimeout(refreshData, refreshMs);
    })
    .catch((error) => {
      console.error("Error fetching data:", error);
      // Schedule Next Refresh Even if There's an Error
      refreshTimeout = setTimeout(refreshData, refreshMs);
    });
}

// Function: Show or Hide Container Humidity Charts
function toggleHumidityCharts(display) {
  for (let chartId in containerCharts) {
    if (chartId.startsWith("humidityChart_")) {
      const chart = document.getElementById(chartId);
      if (display) chart.classList.remove("hidden");
      else chart.classList.add("hidden");
    }
  }
}

// Function: Show or Hide Container Pump mL Charts
function togglePumpCharts(display) {
  for (let chartId in containerCharts) {
    if (chartId.startsWith("pumpMlChart_")) {
      const chart = document.getElementById(chartId);
      if (display) chart.classList.remove("hidden");
      else chart.classList.add("hidden");
    }
  }
}

// Function: Initialize Data Manager and Set Up Event Listeners
function initDataManager() {
  // Event Listener: Data Source Toggle
  const dataSourceToggle = document.getElementsByName("dataSource");
  dataSourceToggle.forEach((radio) => {
    radio.addEventListener("change", function () {
      if (this.checked) {
        currentSource = this.value;
        refreshData(); // Fetch new data based on selected source
      }
    });
  });

  // Event Listener: Humidity Toggle
  const humidityToggle = document.getElementById("humidityToggle");
  humidityToggle.addEventListener("change", function () {
    // Update Container Charts based on Humidity Toggle
    updateContainerCharts(organizedData, sensorData);
  });

  // Event Listener: Cumulative ML Toggle
  const cumulativeMlToggle = document.getElementById("cumulativeMlToggle");
  cumulativeMlToggle.addEventListener("change", function () {
    // Update Container Charts based on Cumulative ML Toggle
    updateContainerCharts(organizedData, sensorData);
  });

  // Event Listener: Display Humidity Chart Toggle
  const displayHumidityChartToggle = document.getElementById("displayHumidityChart");
  displayHumidityChartToggle.addEventListener("change", function () {
    const isChecked = this.checked;
    toggleHumidityCharts(isChecked);
    localStorage.setItem("displayHumidityChart", isChecked);
  });

  // Event Listener: Display Pump Chart Toggle
  const displayPumpChartToggle = document.getElementById("displayPumpChart");
  displayPumpChartToggle.addEventListener("change", function () {
    const isChecked = this.checked;
    togglePumpCharts(isChecked);
    localStorage.setItem("displayPumpChart", isChecked);
  });

  // Load Checkbox States from Local Storage
  const storedDisplayHumidityChart = localStorage.getItem("displayHumidityChart");
  const storedDisplayPumpChart = localStorage.getItem("displayPumpChart");

  if (storedDisplayHumidityChart !== null) {
    displayHumidityChartToggle.checked = storedDisplayHumidityChart === "true";
    toggleHumidityCharts(displayHumidityChartToggle.checked);
  }

  if (storedDisplayPumpChart !== null) {
    displayPumpChartToggle.checked = storedDisplayPumpChart === "true";
    togglePumpCharts(displayPumpChartToggle.checked);
  }

  // Initial Data Fetch
  refreshData();
}

// Initialize Data Manager on DOM Content Loaded
document.addEventListener("DOMContentLoaded", initDataManager);
