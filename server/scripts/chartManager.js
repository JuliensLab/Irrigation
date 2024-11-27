// scripts/chartManager.js

// Function: Update Sensor Charts
function updateSensorCharts(sensorDataObject) {
  const { cpuTemps, roomTempsSHT40, roomTempsBMP280, roomHumiditySHT40, roomPressureBMP280, labels } = sensorDataObject;

  // Temperature Data
  const temperatureData = [
    {
      label: "CPU °C",
      data: cpuTemps,
      borderColor: "rgba(255, 99, 132, 1)", // Red
      backgroundColor: "rgba(255, 99, 132, 0.2)",
    },
    {
      label: "Room Temp °C (SHT40)",
      data: roomTempsSHT40,
      borderColor: "rgba(54, 162, 235, 1)", // Blue
      backgroundColor: "rgba(54, 162, 235, 0.2)",
    },
    {
      label: "Room Temp °C (BMP280)",
      data: roomTempsBMP280,
      borderColor: "rgba(75, 192, 192, 1)", // Teal
      backgroundColor: "rgba(75, 192, 192, 0.2)",
    },
  ];

  // Humidity Data
  const humidityData = [
    {
      label: "Room Humidity % (SHT40)",
      data: roomHumiditySHT40,
      borderColor: "rgba(255, 206, 86, 1)", // Yellow
      backgroundColor: "rgba(255, 206, 86, 0.2)",
    },
  ];

  // Pressure Data
  const pressureData = [
    {
      label: "Room Pressure hPa (BMP280)",
      data: roomPressureBMP280,
      borderColor: "rgba(52, 235, 192, 1)", // Purple
      backgroundColor: "rgba(52, 235, 192, 0.2)",
    },
  ];

  // Get Sensor Charts Container
  const sensorChartsContainer = document.getElementById("sensor-charts");
  sensorChartsContainer.innerHTML = ""; // Clear existing charts

  // Create Temperature Chart
  const tempChartContainer = document.createElement("div");
  tempChartContainer.classList.add("chart-container");
  tempChartContainer.appendChild(generateChart(temperatureData, labels, "Temperature °C", "line", 0, null));
  sensorChartsContainer.appendChild(tempChartContainer);

  // Create Humidity Chart
  const humidityChartContainer = document.createElement("div");
  humidityChartContainer.classList.add("chart-container");
  humidityChartContainer.appendChild(generateChart(humidityData, labels, "Humidity %", "line", 30, 50));
  sensorChartsContainer.appendChild(humidityChartContainer);

  // Create Pressure Chart
  const pressureChartContainer = document.createElement("div");
  pressureChartContainer.classList.add("chart-container");
  pressureChartContainer.appendChild(generateChart(pressureData, labels, "Pressure hPa", "line", 980, 1040));
  sensorChartsContainer.appendChild(pressureChartContainer);
}

// Function: Update Container Charts
function updateContainerCharts(organizedData, sensorData) {
  const containerChartsContainer = document.getElementById("container-charts");
  const humidityToggle = document.getElementById("humidityToggle");
  const cumulativeMlToggle = document.getElementById("cumulativeMlToggle");

  // Clear Existing Charts
  containerChartsContainer.innerHTML = "";

  for (let [container_id, container_array] of Object.entries(organizedData)) {
    // Create Chart Container
    const chartContainer = document.createElement("div");
    chartContainer.classList.add("chart-container");

    // Get Latest Humidity Percentage
    const latestHumidity = container_array[container_array.length - 1].humidity_pct;

    // Create Title with Latest Humidity
    const title = document.createElement("h3");
    title.innerText = `${container_id} - Soil humidity: ${(parseFloat(latestHumidity) * 100).toFixed(1)}%`;
    chartContainer.appendChild(title);

    // Determine Humidity Data Based on Toggle
    const humidityData = humidityToggle.checked
      ? container_array.map((container) => container.humidity_pct * 100)
      : container_array.map((container) => container.humidity_raw);

    const pumpMlData = cumulativeMlToggle.checked
      ? container_array.map((container) => container.pump_ml_cumul)
      : container_array.map((container) => container.pump_ml_added);

    // Prepare Labels by Matching sensor_data_id with sensorData
    const containerLabels = container_array
      .map((container) => {
        const matchingSensor = sensorData.find((sensor) => sensor.id === container.sensor_data_id);
        return matchingSensor ? matchingSensor.date_time.slice(11) : null; // Extract time portion
      })
      .filter((dateTime) => dateTime !== null); // Remove nulls

    // Create Humidity Chart Data
    const humidityChart = {
      label: humidityToggle.checked ? "Humidity %" : "Humidity Raw",
      data: humidityData,
      borderColor: humidityToggle.checked ? "rgba(255, 206, 86, 1)" : "rgba(75, 192, 192, 1)",
      backgroundColor: humidityToggle.checked ? "rgba(255, 206, 86, 0.2)" : "rgba(75, 192, 192, 0.2)",
    };

    // Create Pump ml Data Chart
    const pumpMlChart = {
      label: cumulativeMlToggle.checked ? "Pump ml cumulative" : "Pump ml added",
      data: pumpMlData,
      borderColor: cumulativeMlToggle.checked ? "rgba(153, 102, 255, 1)" : "rgba(255, 159, 64, 1)",
      backgroundColor: cumulativeMlToggle.checked ? "rgba(153, 102, 255, 0.2)" : "rgba(255, 159, 64, 0.2)",
    };

    // Create and Append Humidity Chart
    chartContainer.appendChild(
      generateChart(
        [humidityChart],
        containerLabels,
        humidityToggle.checked ? "Humidity %" : "Humidity Raw",
        "line",
        0,
        humidityToggle.checked ? 100 : null
      )
    );

    // Create and Append Pump ml Chart
    chartContainer.appendChild(
      generateChart(
        [pumpMlChart],
        containerLabels,
        cumulativeMlToggle.checked ? "Pump ml cumulative" : "Pump ml added",
        "line",
        0,
        cumulativeMlToggle.checked ? null : 10 // Assuming 1000 as a reasonable max for pump_ml_added
      )
    );

    // Append Chart Container to Main Container
    containerChartsContainer.appendChild(chartContainer);
  }
}
