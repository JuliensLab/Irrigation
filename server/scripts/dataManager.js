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
    organizedData[containerId].sort((a, b) => parseInt(a.sensor_data_id) - parseInt(b.sensor_data_id));
  }

  // Convert cumulative to added ml
  for (const containerId in organizedData) {
    const array = organizedData[containerId];
    if (array.length > 0) {
      array[0].pump_ml_added = null; // First entry has no previous data to subtract
      for (let i = 1; i < array.length; i++) {
        array[i].pump_ml_added = (parseFloat(array[i].pump_ml_cumul) - parseFloat(array[i - 1].pump_ml_cumul)).toString();
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

  sensorData.sort((a, b) => parseInt(a.id) - parseInt(b.id));
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
      // console.log(data);
      // Convert all IDs to strings to ensure consistency
      sensorData = data.sensorData.map((sensor) => ({
        ...sensor,
        id: sensor.id.toString(),
        date_time: sensor.date_time, // Assuming date_time is already a string
      }));
      containerDataArray = data.containerData.map((container) => ({
        ...container,
        id: container.id.toString(),
        sensor_data_id: container.sensor_data_id.toString(),
        container_id: container.container_id.toString(),
        humidity_pct: container.humidity_pct.toString(),
        humidity_raw: container.humidity_raw.toString(),
        humidity_tgt: container.humidity_tgt.toString(),
        pump_ml_added: container.pump_ml_added.toString(),
        pump_ml_cumul: container.pump_ml_cumul ? container.pump_ml_cumul.toString() : null, // Handle if pump_ml_cumul exists
      }));
      currentSource = data.source; // Update current source based on response

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

// Function to Convert Data to Excel and Trigger Download
function exportToExcel(filename, tabname) {
  if (sensorData.length === 0) {
    alert("No sensor data available to export.");
    return;
  }

  // Define headers
  const headers = ["Timestamp"];

  // Extract environmental data headers from sensorData
  const envDataKeys = Object.keys(sensorData[0]).filter((key) => key !== "id" && key !== "date_time");
  headers.push(...envDataKeys.map((key) => `Env: ${key}`));

  // Extract unique container IDs
  const containerIds = [...new Set(containerDataArray.map((item) => item.container_id))];

  // Define sensor data fields to include
  const sensorFields = ["pump_ml_added", "humidity_pct", "humidity_raw", "humidity_tgt"];

  // Extract sensor data headers based on container IDs and sensor fields
  containerIds.forEach((id) => {
    sensorFields.forEach((field) => {
      headers.push(`Sensor: ${field}_container_${id}`);
    });
  });

  // Initialize rows with headers
  const rows = [headers];

  // Create a map for container data grouped by sensor_data_id
  const containerDataMap = {};
  containerDataArray.forEach((item) => {
    const sensorId = item.sensor_data_id;
    if (!containerDataMap[sensorId]) {
      containerDataMap[sensorId] = [];
    }
    containerDataMap[sensorId].push(item);
  });

  // Iterate over sensorData to build rows
  sensorData.forEach((sensor) => {
    const row = [];
    row.push(sensor.date_time); // Timestamp

    // Add environmental data
    envDataKeys.forEach((key) => {
      row.push(sensor[key]);
    });

    // Add sensor data for each container and each sensor field
    containerIds.forEach((id) => {
      // Find all container data entries matching the current sensor's id and container_id
      const matchingContainerData = containerDataMap[sensor.id] && containerDataMap[sensor.id].filter((cd) => cd.container_id === id);

      if (matchingContainerData && matchingContainerData.length > 0) {
        // Assuming one entry per container per sensor_data_id
        const containerEntry = matchingContainerData[0];
        sensorFields.forEach((field) => {
          row.push(containerEntry[field] || null); // Push the field value or null if undefined
        });
      } else {
        // If no matching container data, push nulls for each sensor field
        sensorFields.forEach(() => {
          row.push(null);
        });
      }
    });

    rows.push(row);
  });

  // Create a worksheet
  const worksheet = XLSX.utils.aoa_to_sheet(rows);

  // Create a new workbook and append the worksheet
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, tabname);

  // Write the workbook and trigger download
  XLSX.writeFile(workbook, filename);
}

// Function to Initialize Download Button Event Listener
function initDownloadButton() {
  const downloadDataButton = document.getElementById("downloadData");

  // Initially disable the button until data is loaded
  downloadDataButton.disabled = true;

  // Event Listener Setup
  downloadDataButton.addEventListener("click", () => {
    // Determine the current source
    let filename = "Monitoring_Data.xlsx";
    let tabname = "Monitoring Data";
    let confirmMessage = "Download the data?";

    if (currentSource === "short") {
      filename = "Monitoring_Data_48hrs.xlsx";
      tabname = "Monitoring Data 48hrs";
      confirmMessage = "Download the last 48 hours of data?";
    } else if (currentSource === "long") {
      filename = "Monitoring_Data_All.xlsx";
      tabname = "Monitoring Data All";
      confirmMessage = "Download all available data?";
    }

    // Confirm action
    if (!confirm(confirmMessage)) return;

    // Export using existing data
    exportToExcel(filename, tabname);
  });

  // Enable the button once data is loaded
  const originalProcessDataAndUpdateCharts = processDataAndUpdateCharts;
  processDataAndUpdateCharts = function () {
    originalProcessDataAndUpdateCharts();
    downloadDataButton.disabled = false;
  };
}

// Function to Initialize Download Button and Other Event Listeners
function initDataManager() {
  // Initialize Download Button
  initDownloadButton();

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
