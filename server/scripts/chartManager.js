// scripts/chartManager.js

// Object to store Chart instances
const sensorCharts = {};
const containerCharts = {};

// Function: Update Sensor Charts
function updateSensorCharts(sensorDataObject) {
  const { cpuTemps, roomTempsSHT40, roomTempsBMP280, roomHumiditySHT40, roomPressureBMP280, labels } = sensorDataObject;

  // Define datasets
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

  const humidityData = [
    {
      label: "Room Humidity % (SHT40)",
      data: roomHumiditySHT40,
      borderColor: "rgba(255, 206, 86, 1)", // Yellow
      backgroundColor: "rgba(255, 206, 86, 0.2)",
    },
  ];

  const pressureData = [
    {
      label: "Room Pressure hPa (BMP280)",
      data: roomPressureBMP280,
      borderColor: "rgba(52, 235, 192, 1)", // Purple
      backgroundColor: "rgba(52, 235, 192, 0.2)",
    },
  ];

  // Define chart configurations
  const chartsConfig = [
    {
      containerId: "sensor-charts",
      chartId: "temperatureChart",
      datasets: temperatureData,
      labels: labels,
      chartTitle: "Temperature °C",
      type: "line",
      yLabel: "Temperature °C",
      minY: 0,
      maxY: null,
    },
    {
      containerId: "sensor-charts",
      chartId: "humidityChart",
      datasets: humidityData,
      labels: labels,
      chartTitle: "Humidity %",
      type: "line",
      yLabel: "Humidity %",
      minY: 30,
      maxY: 50,
    },
    {
      containerId: "sensor-charts",
      chartId: "pressureChart",
      datasets: pressureData,
      labels: labels,
      chartTitle: "Pressure hPa",
      type: "line",
      yLabel: "Pressure hPa",
      minY: 980,
      maxY: 1040,
    },
  ];

  chartsConfig.forEach((config) => {
    const { containerId, chartId, datasets, labels, chartTitle, type, minY, maxY } = config;
    const container = document.getElementById(containerId);

    // If chart already exists, update its data
    if (sensorCharts[chartId]) {
      sensorCharts[chartId].data.labels = labels;
      sensorCharts[chartId].data.datasets = datasets;
      sensorCharts[chartId].options.scales.y.title.text = chartTitle;
      if (minY !== null) {
        sensorCharts[chartId].options.scales.y.suggestedMin = minY;
      }
      if (maxY !== null) {
        sensorCharts[chartId].options.scales.y.suggestedMax = maxY;
      }
      sensorCharts[chartId].update();
    } else {
      // Create a new canvas element if it doesn't exist
      let canvas = document.getElementById(chartId);
      if (!canvas) {
        canvas = document.createElement("canvas");
        canvas.id = chartId;
        canvas.classList.add("sensor-chart");
        const div = document.createElement("div");
        div.id = `sensor-chart-${chartId}`;
        div.classList.add("chart-container");
        div.appendChild(canvas);
        container.appendChild(div);
      }

      // Initialize new Chart instance
      sensorCharts[chartId] = new Chart(canvas.getContext("2d"), {
        type: type,
        data: {
          labels: labels,
          datasets: datasets,
        },
        options: {
          responsive: true,
          //   plugins: {
          //     title: {
          //       display: true,
          //       text: chartTitle,
          //     },
          //   },
          scales: {
            y: {
              beginAtZero: minY === null,
              //   title: {
              //     display: true,
              //     text: chartTitle,
              //   },
              suggestedMin: minY !== null ? minY : undefined,
              suggestedMax: maxY !== null ? maxY : undefined,
            },
          },
          animation: {
            duration: 0, // Disable animations for faster updates
          },
        },
      });
    }
  });
}

// Function: Update Container Charts
function updateContainerCharts(organizedData, sensorData) {
  const humidityToggle = document.getElementById("humidityToggle");
  const cumulativeMlToggle = document.getElementById("cumulativeMlToggle");

  for (let [container_id, container_array] of Object.entries(organizedData)) {
    // Prepare chart identifiers
    const humidityChartId = `humidityChart_${container_id}`;
    const pumpMlChartId = `pumpMlChart_${container_id}`;

    // Get or create chart containers
    let chartContainer = document.getElementById(`container-chart-${container_id}`);
    if (!chartContainer) {
      chartContainer = document.createElement("div");
      chartContainer.id = `container-chart-${container_id}`;
      chartContainer.classList.add("chart-container");

      // Create and append title
      const title = document.createElement("h3");
      const latestHumidity = container_array[container_array.length - 1].humidity_pct;
      title.innerText = `${container_id} - Soil humidity: ${(parseFloat(latestHumidity) * 100).toFixed(1)}%`;
      chartContainer.appendChild(title);

      // Append to main container
      document.getElementById("container-charts").appendChild(chartContainer);
    } else {
      // Update title if it exists
      const title = chartContainer.querySelector("h3");
      if (title) {
        const latestHumidity = container_array[container_array.length - 1].humidity_pct;
        title.innerText = `${container_id} - Soil humidity: ${(parseFloat(latestHumidity) * 100).toFixed(1)}%`;
      }
    }

    // Determine Humidity Data Based on Toggle
    const humidityData = humidityToggle.checked
      ? container_array.map((container) => container.humidity_raw)
      : container_array.map((container) => container.humidity_pct * 100);

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

    // Define Humidity Chart Dataset
    const humidityDataset = {
      label: humidityToggle.checked ? "Humidity Raw" : "Humidity %",
      data: humidityData,
      borderColor: humidityToggle.checked ? "rgba(75, 192, 192, 1)" : "rgba(255, 206, 86, 1)",
      backgroundColor: humidityToggle.checked ? "rgba(75, 192, 192, 0.2)" : "rgba(255, 206, 86, 0.2)",
    };

    // Define Pump ml Dataset
    const pumpMlDataset = {
      label: cumulativeMlToggle.checked ? "Pump ml cumulative" : "Pump ml added",
      data: pumpMlData,
      borderColor: cumulativeMlToggle.checked ? "rgba(153, 102, 255, 1)" : "rgba(255, 159, 64, 1)",
      backgroundColor: cumulativeMlToggle.checked ? "rgba(153, 102, 255, 0.2)" : "rgba(255, 159, 64, 0.2)",
    };

    // Update or Create Humidity Chart
    if (containerCharts[humidityChartId]) {
      containerCharts[humidityChartId].data.labels = containerLabels;
      containerCharts[humidityChartId].data.datasets = [humidityDataset];
      containerCharts[humidityChartId].options.scales.y.title.text = humidityToggle.checked ? "Humidity Raw" : "Humidity %";
      containerCharts[humidityChartId].options.scales.y.suggestedMin = humidityToggle.checked ? 0 : 0;
      containerCharts[humidityChartId].options.scales.y.suggestedMax = humidityToggle.checked ? 1 : 100;
      containerCharts[humidityChartId].update();
    } else {
      // Create a new canvas element if it doesn't exist
      let humidityCanvas = document.getElementById(humidityChartId);
      if (!humidityCanvas) {
        humidityCanvas = document.createElement("canvas");
        humidityCanvas.id = humidityChartId;
        humidityCanvas.classList.add("container-humidity-chart");
        chartContainer.appendChild(humidityCanvas);
      }

      // Initialize new Chart instance
      containerCharts[humidityChartId] = new Chart(humidityCanvas.getContext("2d"), {
        type: "line",
        data: {
          labels: containerLabels,
          datasets: [humidityDataset],
        },
        options: {
          responsive: true,
          plugins: {
            // title: {
            //   display: true,
            //   text: humidityToggle.checked ? "Humidity Raw": "Humidity %",
            // },
          },
          scales: {
            y: {
              beginAtZero: humidityToggle.checked,
              //   title: {
              //     display: true,
              //     text: humidityToggle.checked ? "Humidity Raw":"Humidity %" ,
              //   },
              suggestedMin: humidityToggle.checked ? undefined : 0,
              suggestedMax: humidityToggle.checked ? undefined : 100,
            },
          },
          animation: {
            duration: 0, // Disable animations for faster updates
          },
        },
      });
    }

    // Update or Create Pump ML Chart
    if (containerCharts[pumpMlChartId]) {
      containerCharts[pumpMlChartId].data.labels = containerLabels;
      containerCharts[pumpMlChartId].data.datasets = [pumpMlDataset];
      containerCharts[pumpMlChartId].options.scales.y.title.text = cumulativeMlToggle.checked ? "Pump ml cumulative" : "Pump ml added";
      containerCharts[pumpMlChartId].options.scales.y.suggestedMin = 0;
      containerCharts[pumpMlChartId].options.scales.y.suggestedMax = cumulativeMlToggle.checked ? null : 10; // Adjust as needed
      containerCharts[pumpMlChartId].update();
    } else {
      // Create a new canvas element if it doesn't exist
      let pumpMlCanvas = document.getElementById(pumpMlChartId);
      if (!pumpMlCanvas) {
        pumpMlCanvas = document.createElement("canvas");
        pumpMlCanvas.id = pumpMlChartId;
        pumpMlCanvas.classList.add("container-pumpml-chart");
        chartContainer.appendChild(pumpMlCanvas);
      }

      // Initialize new Chart instance
      containerCharts[pumpMlChartId] = new Chart(pumpMlCanvas.getContext("2d"), {
        type: "line",
        data: {
          labels: containerLabels,
          datasets: [pumpMlDataset],
        },
        options: {
          responsive: true,
          plugins: {
            // title: {
            //   display: true,
            //   text: cumulativeMlToggle.checked ? "Pump ml cumulative" : "Pump ml added",
            // },
          },
          scales: {
            y: {
              beginAtZero: true,
              //   title: {
              //     display: true,
              //     text: cumulativeMlToggle.checked ? "Pump ml cumulative" : "Pump ml added",
              //   },
              suggestedMin: cumulativeMlToggle.checked ? undefined : 0,
              suggestedMax: cumulativeMlToggle.checked ? undefined : 10, // Adjust as needed
            },
          },
          animation: {
            duration: 0, // Disable animations for faster updates
          },
        },
      });
    }
  }
}
