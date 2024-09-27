<?php
// api_receive_short_term_data.php

// Set headers to allow CORS and accept JSON
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");

// includes
$config = include('api_config.php');
include('check_ip.php');
include('log.php');

// Log an entry to test the function
log_message("Script started.");

log_message('db details:', $config['host'], $config['username'], $config['password'], $config['db_name']);

// Create database connection
$conn = new mysqli($config['host'], $config['username'], $config['password'], $config['db_name']);

// Check connection
if ($conn->connect_error) {
    log_message("Database connection failed: " . $conn->connect_error);
    die(json_encode(["status" => "error", "message" => "Database connection failed: " . $conn->connect_error]));
}

// Get the client's IP address
$client_ip = $_SERVER['REMOTE_ADDR'];
log_message("Client IP: $client_ip");


// Check if the client's IP is within the trusted range
if (!is_ip_allowed($client_ip)) {
    log_message("Unauthorized IP address: $client_ip");
    http_response_code(403);
    echo json_encode(["status" => "error", "message" => "Unauthorized IP address"]);
    exit;
}

// Get the raw POST data
$data = json_decode(file_get_contents("php://input"), true);

// Authenticate using API key
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $received_api_key = $data['api_key'];
    log_message("received key:", $received_api_key, "api_key:", $config['api_key']);
    log_message($_SERVER['HTTP_API_KEY'], $_SERVER['API_KEY']);
    if ($received_api_key !== $config['api_key']) {
        log_message("Unauthorized access attempt with API key: $received_api_key");
        http_response_code(403);
        echo json_encode(["status" => "error", "message" => "Unauthorized"]);
        exit;
    }

    // Validate incoming data
    if (!isset($data['date_time'], $data['cpu_temp'], $data['room_temp_SHT40'], $data['room_temp_BMP280'], $data['room_humidity_SHT40'], $data['room_pressure_BMP280'], $data['containers'])) {
        log_message("Invalid data received: " . json_encode($data));
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Invalid data"]);
        exit;
    }

    // Prepare SQL statement for short-term sensor data
    $stmtShortTerm = $conn->prepare("INSERT INTO short_term_sensor_data (date_time, cpu_temp, room_temp_SHT40, room_temp_BMP280, room_humidity_SHT40, room_pressure_BMP280) VALUES (?, ?, ?, ?, ?, ?)");
    $stmtShortTerm->bind_param("sddddd", $datetime, $cpuTempC, $roomTempC_SHT40, $roomTempC_BMP280, $roomHumiditySHT40, $roomPressureBMP280);

    // Insert data into short-term sensor data table
    $datetime = $data['date_time'];
    $cpuTempC = floatval($data['cpu_temp']);
    $roomTempC_SHT40 = floatval($data['room_temp_SHT40']);
    $roomTempC_BMP280 = floatval($data['room_temp_BMP280']);
    $roomHumiditySHT40 = floatval($data['room_humidity_SHT40']);
    $roomPressureBMP280 = floatval($data['room_pressure_BMP280']);

    if (!$stmtShortTerm->execute()) {
        log_message("Database insert failed for short-term sensor data: " . $stmtShortTerm->error);
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Database insert failed: " . $stmtShortTerm->error]);
        exit;
    }

    // Get the last inserted ID for short-term data
    $shortTermSensorDataId = $conn->insert_id;

    // Prepare SQL statement for short-term container data
    $stmtContainerShortTerm = $conn->prepare("INSERT INTO short_term_container_data (short_term_sensor_data_id, container_id, humidity_raw, humidity_pct, pump_ml_added) VALUES (?, ?, ?, ?, ?)");
    $stmtContainerShortTerm->bind_param("isddi", $shortTermSensorDataId, $container_id, $humidity_raw, $humidity_pct, $pump_ml_added);

    // Iterate over containers and insert data into short-term container data table
    foreach ($data['containers'] as $container) {
        // Get values from the container data
        $container_id = $container['container_id'];
        $humidity_raw = floatval($container['humidity_raw']);
        $humidity_pct = floatval($container['humidity_pct']);
        $pump_ml_added = intval($container['pump_ml_added']); // Cast to integer
        log_message($container);

        // Execute statement for container data
        if (!$stmtContainerShortTerm->execute()) {
            log_message("Database insert failed for container ID $container_id: " . $stmtContainerShortTerm->error);
            http_response_code(500);
            echo json_encode(["status" => "error", "message" => "Database insert failed: " . $stmtContainerShortTerm->error]);
            exit;
        }
    }

    // Close short-term statements
    $stmtShortTerm->close();
    $stmtContainerShortTerm->close();

    // Close connection
    $conn->close();

    // Respond with success
    log_message("Data inserted successfully for client IP: $client_ip");
    echo json_encode(["status" => "success", "message" => "Data inserted successfully"]);
} else {
    log_message("Method not allowed: " . $_SERVER['REQUEST_METHOD']);
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Method not allowed"]);
}
