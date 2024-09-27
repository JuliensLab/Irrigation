<?php
// index.php

// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Set headers to allow CORS and accept HTML
header("Access-Control-Allow-Origin: *");
header("Content-Type: text/html; charset=UTF-8");

// Includes
$config = include('api/api_config.php');
include('log.php');


// Create database connection
$conn = new mysqli($config['host'], $config['username'], $config['password'], $config['db_name']);

// Check connection
if ($conn->connect_error) {
    log_message("Database connection failed: " . $conn->connect_error);
    die("Database connection failed: " . $conn->connect_error);
}

// Fetch short-term sensor data
$sensorDataQuery = "SELECT * FROM short_term_sensor_data ORDER BY date_time DESC LIMIT 10";
$sensorDataResult = $conn->query($sensorDataQuery);

if ($sensorDataResult === false) {
    log_message("Query failed for sensor data: " . $conn->error);
}

// Prepare sensor data
$sensorData = [];
$sensorIds = [];
if ($sensorDataResult->num_rows > 0) {
    while ($row = $sensorDataResult->fetch_assoc()) {
        $sensorData[] = $row;
        $sensorIds[] = $row['id']; // Assuming 'id' is the primary key for sensor data
    }
} else {
    log_message("No entries found in short-term sensor data.");
}

// If there are sensor IDs, fetch short-term container data
$containerData = [];
if (!empty($sensorIds)) {
    $sensorIdList = implode(',', array_map('intval', $sensorIds)); // Sanitize IDs for the query
    $containerDataQuery = "SELECT * FROM short_term_container_data WHERE short_term_sensor_data_id IN ($sensorIdList)";
    $containerDataResult = $conn->query($containerDataQuery);

    if ($containerDataResult === false) {
        log_message("Query failed for container data: " . $conn->error);
    }

    if ($containerDataResult->num_rows > 0) {
        while ($row = $containerDataResult->fetch_assoc()) {
            $containerData[] = $row;
        }
    } else {
        log_message("No entries found in short-term container data.");
    }
}

// Close the connection
$conn->close();

// Output HTML
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Dashboard</title>
    <link rel="icon" type="image/png" href="favico.png">
    <link rel="stylesheet" href="css/styles.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script> <!-- Link to Chart.js -->
    <script src="scripts/chartGenerator.js"></script> <!-- Link to the chart generator script -->

</head>

<body>

    <h1>Monitoring Dashboard</h1>

    <h2>Short-Term Sensor Data</h2>
    <table>
        <tr>
            <th>Date & Time</th>
            <th>CPU Temperature (°C)</th>
            <th>Room Temp (SHT40) (°C)</th>
            <th>Room Temp (BMP280) (°C)</th>
            <th>Room Humidity (SHT40) (%)</th>
            <th>Room Pressure (BMP280) (hPa)</th>
        </tr>
        <?php foreach ($sensorData as $sensor): ?>
            <tr>
                <td><?php echo htmlspecialchars($sensor['date_time']); ?></td>
                <td><?php echo htmlspecialchars($sensor['cpu_temp']); ?></td>
                <td><?php echo htmlspecialchars($sensor['room_temp_SHT40']); ?></td>
                <td><?php echo htmlspecialchars($sensor['room_temp_BMP280']); ?></td>
                <td><?php echo htmlspecialchars($sensor['room_humidity_SHT40']); ?></td>
                <td><?php echo htmlspecialchars($sensor['room_pressure_BMP280']); ?></td>
            </tr>
        <?php endforeach; ?>
    </table>

    <h2>Short-Term Container Data</h2>
    <table>
        <tr>
            <th>Container ID</th>
            <th>Humidity Raw</th>
            <th>Humidity %</th>
            <th>Pump ML Added</th>
        </tr>
        <?php foreach ($containerData as $container): ?>
            <tr>
                <td><?php echo htmlspecialchars($container['container_id']); ?></td>
                <td><?php echo htmlspecialchars($container['humidity_raw']); ?></td>
                <td><?php echo htmlspecialchars($container['humidity_pct']); ?></td>
                <td><?php echo htmlspecialchars($container['pump_ml_added']); ?></td>
            </tr>
        <?php endforeach; ?>
    </table>

</body>

</html>