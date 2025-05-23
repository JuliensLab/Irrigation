<?php
// get_data.php

// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Set headers to allow CORS and return JSON
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");

// Includes
$config = include('api_config.php');
include('log.php');

// Create database connection
$conn = new mysqli($config['host'], $config['username'], $config['password'], $config['db_name']);


// Determine the data source ('short' or 'long'), default to 'short'
$source = isset($_GET['source']) && strtolower($_GET['source']) === 'long' ? 'long' : 'short';


// Check connection
if ($conn->connect_error) {
    log_message("Database connection failed: " . $conn->connect_error);
    die(json_encode(["error" => "Database connection failed: " . $conn->connect_error]));
}

// Fetch sensor data
$sensorDataQuery = "SELECT * FROM {$source}_term_sensor_data ORDER BY date_time DESC LIMIT 10000";
$sensorDataResult = $conn->query($sensorDataQuery);

$sensorData = [];
$sensorIds = [];
if ($sensorDataResult->num_rows > 0) {
    while ($row = $sensorDataResult->fetch_assoc()) {
        $sensorData[] = $row;
        $sensorIds[] = $row['id'];
    }
}

// Fetch container data if there are sensor IDs
$containerData = [];
if (!empty($sensorIds)) {
    $sensorIdList = implode(',', array_map('intval', $sensorIds));
    $containerDataQuery = "SELECT * FROM {$source}_term_container_data WHERE sensor_data_id IN ($sensorIdList)";
    $containerDataResult = $conn->query($containerDataQuery);

    if ($containerDataResult->num_rows > 0) {
        while ($row = $containerDataResult->fetch_assoc()) {
            $containerData[] = $row;
        }
    }
}

// Return the data as JSON
echo json_encode([
    'source' => $source,
    'sensorData' => $sensorData,
    'containerData' => $containerData
]);

// Close the connection
$conn->close();
