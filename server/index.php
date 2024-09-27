<?php
// index.php

// // Enable error reporting
// error_reporting(E_ALL);
// ini_set('display_errors', 1);

// // Set headers to allow CORS and accept HTML
// header("Access-Control-Allow-Origin: *");
// header("Content-Type: text/html; charset=UTF-8");

// // Includes
// $config = include('api/api_config.php');
// include('log.php');

// // Create database connection
// $conn = new mysqli($config['host'], $config['username'], $config['password'], $config['db_name']);

// // Check connection
// if ($conn->connect_error) {
//     log_message("Database connection failed: " . $conn->connect_error);
//     die("Database connection failed: " . $conn->connect_error);
// }

// // Fetch short-term sensor data
// $sensorDataQuery = "SELECT * FROM short_term_sensor_data ORDER BY date_time DESC LIMIT 100";
// $sensorDataResult = $conn->query($sensorDataQuery);

// if ($sensorDataResult === false) {
//     log_message("Query failed for sensor data: " . $conn->error);
// }

// // Prepare sensor data
// $sensorData = [];
// $sensorIds = [];
// if ($sensorDataResult->num_rows > 0) {
//     while ($row = $sensorDataResult->fetch_assoc()) {
//         $sensorData[] = $row;
//         $sensorIds[] = $row['id']; // Assuming 'id' is the primary key for sensor data
//     }
// } else {
//     log_message("No entries found in short-term sensor data.");
// }

// // If there are sensor IDs, fetch short-term container data
// $containerData = [];
// if (!empty($sensorIds)) {
//     $sensorIdList = implode(',', array_map('intval', $sensorIds)); // Sanitize IDs for the query
//     $containerDataQuery = "SELECT * FROM short_term_container_data WHERE short_term_sensor_data_id IN ($sensorIdList)";
//     $containerDataResult = $conn->query($containerDataQuery);

//     if ($containerDataResult === false) {
//         log_message("Query failed for container data: " . $conn->error);
//     }

//     if ($containerDataResult->num_rows > 0) {
//         while ($row = $containerDataResult->fetch_assoc()) {
//             $containerData[] = $row;
//         }
//     } else {
//         log_message("No entries found in short-term container data.");
//     }
// }

// // Close the connection
// $conn->close();


?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Dashboard</title>
    <link rel="icon" type="image/png" href="favico.png">
    <link rel="stylesheet" href="css/styles.css?v=1.0.2">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="scripts/chartGenerator.js?v=1.0.5"></script>
    <script>
        // Function to fetch the latest data and update charts
        function refreshData() {
            fetch('https://irrigationmars.com/api/get_data.php')
                .then(response => response.json())
                .then(data => {
                    const sensorData = data.sensorData;
                    const containerDataArray = data.containerData;

                    // Update the sensor charts
                    updateSensorCharts(sensorData);

                    // Update the container charts
                    updateContainerCharts(containerDataArray, sensorData);
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                });
        }
        // Refresh the data every 5 seconds
        setInterval(refreshData, 5000);
    </script>
</head>

<body>

    <h1>Monitoring Dashboard</h1>

    <h2>Container Charts</h2>
    <label><input type="checkbox" id="humidityToggle" checked>Humidity as %</label>
    <div id="container-charts"></div>

    <h2>Sensor Charts</h2>
    <div id="sensor-charts"></div>




    <script>
        function updateSensorCharts(sensorData) {

            // Extract data for temperatures, humidity, and pressure// Sort sensorData by 'id'
            const sortedSensorData = sensorData.sort((a, b) => a.id - b.id);
            const cpuTemps = sensorData.map(sensor => sensor.cpu_temp);
            const roomTempsSHT40 = sensorData.map(sensor => sensor.room_temp_SHT40);
            const roomTempsBMP280 = sensorData.map(sensor => sensor.room_temp_BMP280);
            const roomHumiditySHT40 = sensorData.map(sensor => sensor.room_humidity_SHT40);
            const roomPressureBMP280 = sensorData.map(sensor => sensor.room_pressure_BMP280);
            const labels = sensorData.map(sensor => sensor.date_time.slice(11)); // Extract time from 'YYYY-MM-DD HH:MM:SS'


            // Create a dataset for the temperatures
            const temperatureData = [{
                    label: 'CPU Temperature',
                    data: cpuTemps,
                    borderColor: 'rgba(255, 99, 132, 1)', // Red
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                },
                {
                    label: 'Room Temp (SHT40)',
                    data: roomTempsSHT40,
                    borderColor: 'rgba(54, 162, 235, 1)', // Blue
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                },
                {
                    label: 'Room Temp (BMP280)',
                    data: roomTempsBMP280,
                    borderColor: 'rgba(75, 192, 192, 1)', // Teal
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                },
            ];

            // Create charts for humidity and pressure
            const humidityData = [{
                label: 'Room Humidity (SHT40)',
                data: roomHumiditySHT40,
                borderColor: 'rgba(255, 206, 86, 1)', // Yellow
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
            }, ];

            const pressureData = [{
                label: 'Room Pressure (BMP280)',
                data: roomPressureBMP280,
                borderColor: 'rgba(153, 102, 255, 1)', // Purple
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
            }, ];

            // Create the temperature chart container
            const sensorChartsContainer = document.getElementById('sensor-charts');
            sensorChartsContainer.innerHTML = ''

            // Create temperature chart
            const tempChartContainer = document.createElement('div');
            tempChartContainer.classList.add('chart-container');
            tempChartContainer.appendChild(generateChart(temperatureData, labels, 'Temperature Readings', 'line'));
            sensorChartsContainer.appendChild(tempChartContainer);

            // Create humidity chart container
            const humidityChartContainer = document.createElement('div');
            humidityChartContainer.classList.add('chart-container');
            humidityChartContainer.appendChild(generateChart(humidityData, labels, 'Humidity Readings', 'line'));
            sensorChartsContainer.appendChild(humidityChartContainer);

            // Create pressure chart container
            const pressureChartContainer = document.createElement('div');
            pressureChartContainer.classList.add('chart-container');
            pressureChartContainer.appendChild(generateChart(pressureData, labels, 'Pressure Readings', 'line'));
            sensorChartsContainer.appendChild(pressureChartContainer);
        }
    </script>



    <script>
        function updateContainerCharts(containerDataArray, sensorData) {

            // Step 1: Organize data by container_id
            const organizedData = {};

            containerDataArray.forEach(item => {
                const {
                    container_id,
                    ...rest
                } = item; // Destructure to separate container_id

                // Initialize array for the container_id if it doesn't exist
                if (!organizedData[container_id]) {
                    organizedData[container_id] = [];
                }

                // Push the remaining data into the appropriate array
                organizedData[container_id].push(rest);
            });

            // Step 2: Sort each array by short_term_sensor_data_id
            for (const containerId in organizedData) {
                organizedData[containerId].sort((a, b) => {
                    return a.short_term_sensor_data_id.localeCompare(b.short_term_sensor_data_id);
                });
            }

            const containerChartsContainer = document.getElementById('container-charts');
            containerChartsContainer.innerHTML = ''
            const humidityToggle = document.getElementById('humidityToggle');

            // Function to generate and display charts based on the toggle state
            // Function to generate and display charts based on the toggle state
            function displayCharts() {
                // Clear existing charts
                containerChartsContainer.innerHTML = '';

                for (let [container_id, container_array] of Object.entries(organizedData)) {
                    // Create a container for the chart
                    const chartContainer = document.createElement('div');
                    chartContainer.classList.add('chart-container'); // Keep this to apply styles

                    // Get the latest humidity % value if toggled for percentage display
                    const latestHumidity = container_array[container_array.length - 1].humidity_pct // Latest humidity %

                    // Create a title for each container with the latest humidity value
                    const title = document.createElement('h3');
                    title.innerText = `${container_id} - Soil humidity: ${(parseFloat(latestHumidity) * 100).toFixed(1)}%`;
                    chartContainer.appendChild(title);

                    // Get humidity data based on toggle state
                    const humidityData = humidityToggle.checked ?
                        container_array.map(container => container.humidity_pct) :
                        container_array.map(container => container.humidity_raw);

                    const pumpMLAddedData = container_array.map(container => container.pump_ml_added);

                    // Prepare containerLabels with time portion of date_time from sensorData
                    const containerLabels = container_array.map(container => {
                        const matchingSensor = sensorData.find(sensor => sensor.id === container.short_term_sensor_data_id);
                        return matchingSensor ? matchingSensor.date_time.slice(11) : null; // Extract time portion or return null if not found
                    }).filter(dateTime => dateTime !== null); // Filter out any null values if no matching sensor was found

                    // Create humidity chart based on the selected data type
                    const humidityChart = {
                        label: humidityToggle.checked ? 'Humidity %' : 'Humidity Raw',
                        data: humidityData,
                        borderColor: humidityToggle.checked ? 'rgba(255, 206, 86, 1)' : 'rgba(75, 192, 192, 1)',
                        backgroundColor: humidityToggle.checked ? 'rgba(255, 206, 86, 0.2)' : 'rgba(75, 192, 192, 0.2)',
                    };

                    // Create and append the humidity chart
                    chartContainer.appendChild(generateChart([humidityChart], containerLabels, humidityToggle.checked ? 'Humidity %' : 'Humidity Raw', 'line'));

                    // Create and append the Pump ML Added chart with default options
                    chartContainer.appendChild(generateChart([{
                        label: 'Pump ml Added',
                        data: pumpMLAddedData,
                        borderColor: 'rgba(153, 102, 255, 1)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    }], containerLabels, 'Pump ml Added', 'line'));

                    // Append the chart container to the main charts container
                    containerChartsContainer.appendChild(chartContainer);
                }
            }


            // Initial display of charts
            displayCharts();

            // Event listener for the toggle
            humidityToggle.addEventListener('change', displayCharts);
        }

        // Initial data fetch
        refreshData();
    </script>

</body>

</html>