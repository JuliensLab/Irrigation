<?php
// api_receive_short_term_data.php

// Set headers to allow CORS and accept JSON
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");

// includes
$config = include('api_config.php');
include('check_ip.php');
include('log.php');

// Create database connection
$conn = new mysqli($config['host'], $config['username'], $config['password'], $config['db_name']);

// Check connection
if ($conn->connect_error) {
    log_message("Database connection failed: " . $conn->connect_error);
    die(json_encode(["status" => "error", "message" => "Database connection failed: " . $conn->connect_error]));
}

// Get the client's IP address
$client_ip = $_SERVER['REMOTE_ADDR'];

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
    $received_api_key = isset($data['api_key']) ? $data['api_key'] : '';
    if ($received_api_key !== $config['api_key']) {
        log_message("Unauthorized access attempt with API key: $received_api_key");
        http_response_code(403);
        echo json_encode(["status" => "error", "message" => "Unauthorized"]);
        exit;
    }

    // Validate incoming data
    $required_fields = ['date_time', 'cpu_temp', 'room_temp_SHT40', 'room_temp_BMP280', 'room_humidity_SHT40', 'room_pressure_BMP280', 'containers'];
    $missing_fields = [];
    foreach ($required_fields as $field) {
        if (!isset($data[$field])) {
            $missing_fields[] = $field;
        }
    }
    if (!empty($missing_fields)) {
        log_message("Invalid data received. Missing fields: " . implode(", ", $missing_fields));
        http_response_code(400);
        echo json_encode(["status" => "error", "message" => "Invalid data. Missing fields: " . implode(", ", $missing_fields)]);
        exit;
    }

    // Begin transaction to ensure data consistency
    $conn->begin_transaction();

    try {
        // Prepare SQL statement for short-term sensor data
        $stmtShortTerm = $conn->prepare("INSERT INTO short_term_sensor_data (date_time, cpu_temp, room_temp_SHT40, room_temp_BMP280, room_humidity_SHT40, room_pressure_BMP280) VALUES (?, ?, ?, ?, ?, ?)");
        if (!$stmtShortTerm) {
            throw new Exception("Prepare failed for short_term_sensor_data: " . $conn->error);
        }
        $stmtShortTerm->bind_param("sddddd", $datetime, $cpuTempC, $roomTempC_SHT40, $roomTempC_BMP280, $roomHumiditySHT40, $roomPressureBMP280);

        // Insert data into short-term sensor data table
        $datetime = $data['date_time'];
        $cpuTempC = floatval($data['cpu_temp']);
        $roomTempC_SHT40 = floatval($data['room_temp_SHT40']);
        $roomTempC_BMP280 = floatval($data['room_temp_BMP280']);
        $roomHumiditySHT40 = floatval($data['room_humidity_SHT40']);
        $roomPressureBMP280 = floatval($data['room_pressure_BMP280']);

        if (!$stmtShortTerm->execute()) {
            throw new Exception("Database insert failed for short-term sensor data: " . $stmtShortTerm->error);
        }

        // Get the last inserted ID for short-term data
        $shortTermSensorDataId = $conn->insert_id;

        // Prepare SQL statement for short-term container data
        $stmtContainerShortTerm = $conn->prepare("INSERT INTO short_term_container_data (sensor_data_id, container_id, humidity_raw, humidity_pct, pump_ml_added) VALUES (?, ?, ?, ?, ?)");
        if (!$stmtContainerShortTerm) {
            throw new Exception("Prepare failed for short_term_container_data: " . $conn->error);
        }
        $stmtContainerShortTerm->bind_param("isddi", $shortTermSensorDataId, $container_id, $humidity_raw, $humidity_pct, $pump_ml_added);

        // Iterate over containers and insert data into short-term container data table
        foreach ($data['containers'] as $container) {
            // Validate container data
            $container_required_fields = ['container_id', 'humidity_raw', 'humidity_pct', 'pump_ml_added'];
            foreach ($container_required_fields as $c_field) {
                if (!isset($container[$c_field])) {
                    throw new Exception("Invalid container data. Missing field: " . $c_field);
                }
            }

            // Get values from the container data
            $container_id = $container['container_id'];
            $humidity_raw = floatval($container['humidity_raw']);
            $humidity_pct = floatval($container['humidity_pct']);
            $pump_ml_added = intval($container['pump_ml_added']); // Cast to integer

            // Execute statement for container data
            if (!$stmtContainerShortTerm->execute()) {
                throw new Exception("Database insert failed for container ID $container_id: " . $stmtContainerShortTerm->error);
            }
        }

        // Close short-term statements
        $stmtShortTerm->close();
        $stmtContainerShortTerm->close();

        /**
         * -------- Long-Term Data Aggregation --------
         */

        // 1. Parse the date_time to get the start of the hour
        $dt = new DateTime($datetime);
        $dt->setTime($dt->format('H'), 0, 0);
        $hour_start = $dt->format('Y-m-d H:i:s');

        // 2. Define the end of the hour
        $dt_end = clone $dt;
        $dt_end->modify('+1 hour');
        $hour_end = $dt_end->format('Y-m-d H:i:s');

        /**
         * 3. Calculate average sensor data for the hour
         */
        $stmtAvgSensors = $conn->prepare("
            SELECT
                AVG(cpu_temp) AS avg_cpu_temp,
                AVG(room_temp_SHT40) AS avg_room_temp_SHT40,
                AVG(room_temp_BMP280) AS avg_room_temp_BMP280,
                AVG(room_humidity_SHT40) AS avg_room_humidity_SHT40,
                AVG(room_pressure_BMP280) AS avg_room_pressure_BMP280
            FROM short_term_sensor_data
            WHERE date_time >= ? AND date_time < ?
        ");
        if (!$stmtAvgSensors) {
            throw new Exception("Prepare failed for averaging sensors: " . $conn->error);
        }
        $stmtAvgSensors->bind_param("ss", $hour_start, $hour_end);

        if (!$stmtAvgSensors->execute()) {
            throw new Exception("Execution failed for averaging sensors: " . $stmtAvgSensors->error);
        }

        $resultAvgSensors = $stmtAvgSensors->get_result();
        if ($resultAvgSensors->num_rows === 0) {
            throw new Exception("No short-term sensor data found for the specified hour.");
        }
        $avgSensors = $resultAvgSensors->fetch_assoc();
        $stmtAvgSensors->close();

        /**
         * 4. Insert or Update long_term_sensor_data
         */
        // Check if an entry for this hour already exists
        $stmtCheckLongTermSensor = $conn->prepare("SELECT id FROM long_term_sensor_data WHERE date_time = ?");
        if (!$stmtCheckLongTermSensor) {
            throw new Exception("Prepare failed for checking long_term_sensor_data: " . $conn->error);
        }
        $stmtCheckLongTermSensor->bind_param("s", $hour_start);
        if (!$stmtCheckLongTermSensor->execute()) {
            throw new Exception("Execution failed for checking long_term_sensor_data: " . $stmtCheckLongTermSensor->error);
        }
        $resultCheckLongTermSensor = $stmtCheckLongTermSensor->get_result();

        if ($resultCheckLongTermSensor->num_rows > 0) {
            // Entry exists, perform update
            $longTermSensorId = $resultCheckLongTermSensor->fetch_assoc()['id'];
            $stmtUpdateLongTermSensor = $conn->prepare("
                UPDATE long_term_sensor_data
                SET cpu_temp = ?, room_temp_SHT40 = ?, room_temp_BMP280 = ?, room_humidity_SHT40 = ?, room_pressure_BMP280 = ?
                WHERE id = ?
            ");
            if (!$stmtUpdateLongTermSensor) {
                throw new Exception("Prepare failed for updating long_term_sensor_data: " . $conn->error);
            }
            $stmtUpdateLongTermSensor->bind_param(
                "dddddi",
                $avgSensors['avg_cpu_temp'],
                $avgSensors['avg_room_temp_SHT40'],
                $avgSensors['avg_room_temp_BMP280'],
                $avgSensors['avg_room_humidity_SHT40'],
                $avgSensors['avg_room_pressure_BMP280'],
                $longTermSensorId
            );
            if (!$stmtUpdateLongTermSensor->execute()) {
                throw new Exception("Execution failed for updating long_term_sensor_data: " . $stmtUpdateLongTermSensor->error);
            }
            $stmtUpdateLongTermSensor->close();
        } else {
            // Entry does not exist, perform insert
            $stmtInsertLongTermSensor = $conn->prepare("
                INSERT INTO long_term_sensor_data (date_time, cpu_temp, room_temp_SHT40, room_temp_BMP280, room_humidity_SHT40, room_pressure_BMP280)
                VALUES (?, ?, ?, ?, ?, ?)
            ");
            if (!$stmtInsertLongTermSensor) {
                throw new Exception("Prepare failed for inserting into long_term_sensor_data: " . $conn->error);
            }
            $stmtInsertLongTermSensor->bind_param(
                "sddddd",
                $hour_start,
                $avgSensors['avg_cpu_temp'],
                $avgSensors['avg_room_temp_SHT40'],
                $avgSensors['avg_room_temp_BMP280'],
                $avgSensors['avg_room_humidity_SHT40'],
                $avgSensors['avg_room_pressure_BMP280']
            );
            if (!$stmtInsertLongTermSensor->execute()) {
                throw new Exception("Execution failed for inserting into long_term_sensor_data: " . $stmtInsertLongTermSensor->error);
            }
            $longTermSensorId = $conn->insert_id;
            $stmtInsertLongTermSensor->close();
        }
        $stmtCheckLongTermSensor->close();

        /**
         * 5. Retrieve all short_term_sensor_data IDs for the specified hour
         */
        $stmtGetShortTermIds = $conn->prepare("
            SELECT id FROM short_term_sensor_data
            WHERE date_time >= ? AND date_time < ?
        ");
        if (!$stmtGetShortTermIds) {
            throw new Exception("Prepare failed for retrieving short_term_sensor_data IDs: " . $conn->error);
        }
        $stmtGetShortTermIds->bind_param("ss", $hour_start, $hour_end);
        if (!$stmtGetShortTermIds->execute()) {
            throw new Exception("Execution failed for retrieving short_term_sensor_data IDs: " . $stmtGetShortTermIds->error);
        }
        $resultShortTermIds = $stmtGetShortTermIds->get_result();
        $shortTermIds = [];
        while ($row = $resultShortTermIds->fetch_assoc()) {
            $shortTermIds[] = $row['id'];
        }
        $stmtGetShortTermIds->close();

        if (empty($shortTermIds)) {
            throw new Exception("No short-term sensor data IDs found for the specified hour.");
        }

        // Prepare a comma-separated list of IDs for SQL IN clause
        $shortTermIdsPlaceholders = implode(',', array_fill(0, count($shortTermIds), '?'));
        $shortTermIdsTypes = str_repeat('i', count($shortTermIds));

        /**
         * 6. Calculate averages for container data
         */
        // Prepare the SQL statement to retrieve container averages and latest pump_ml_added
        $sqlContainer = "
            SELECT
                sc.container_id,
                AVG(sc.humidity_raw) AS avg_humidity_raw,
                AVG(sc.humidity_pct) AS avg_humidity_pct,
                sc_latest.pump_ml_added
            FROM short_term_container_data sc
            INNER JOIN (
                SELECT sc1.container_id, sc1.pump_ml_added
                FROM short_term_container_data sc1
                INNER JOIN short_term_sensor_data sss1 ON sc1.sensor_data_id = sss1.id
                WHERE sss1.date_time >= ? AND sss1.date_time < ?
                ORDER BY sc1.container_id, sc1.id DESC
            ) sc_latest ON sc.container_id = sc_latest.container_id
            INNER JOIN short_term_sensor_data sss ON sc.sensor_data_id = sss.id
            WHERE sc.sensor_data_id IN (" . $shortTermIdsPlaceholders . ")
            AND sss.date_time >= ? AND sss.date_time < ?
            GROUP BY sc.container_id
        ";

        $stmtContainer = $conn->prepare($sqlContainer);
        if (!$stmtContainer) {
            throw new Exception("Prepare failed for retrieving container data: " . $conn->error);
        }

        // Bind parameters
        $bindTypes = 'ss' . $shortTermIdsTypes . 'ss';
        $bindParams = array_merge([$hour_start, $hour_end], $shortTermIds, [$hour_start, $hour_end]);

        // Use references for bind_param
        $bindParamsRefs = [];
        foreach ($bindParams as $key => $value) {
            $bindParamsRefs[$key] = &$bindParams[$key];
        }

        // Call bind_param dynamically
        call_user_func_array([$stmtContainer, 'bind_param'], array_merge([$bindTypes], $bindParamsRefs));

        if (!$stmtContainer->execute()) {
            throw new Exception("Execution failed for retrieving container data: " . $stmtContainer->error);
        }

        $resultContainer = $stmtContainer->get_result();
        if ($resultContainer->num_rows === 0) {
            throw new Exception("No container data found for the specified hour.");
        }

        /**
         * 7. Insert or Update long_term_container_data
         */
        while ($row = $resultContainer->fetch_assoc()) {
            $container_id = $row['container_id'];
            $avg_humidity_raw = floatval($row['avg_humidity_raw']);
            $avg_humidity_pct = floatval($row['avg_humidity_pct']);
            $pump_ml_added = intval($row['pump_ml_added']);

            // Check if an entry for this sensor_data_id and container_id exists
            $stmtCheckLongTermContainer = $conn->prepare("
                SELECT id FROM long_term_container_data
                WHERE sensor_data_id = ? AND container_id = ?
            ");
            if (!$stmtCheckLongTermContainer) {
                throw new Exception("Prepare failed for checking long_term_container_data: " . $conn->error);
            }
            $stmtCheckLongTermContainer->bind_param("is", $longTermSensorId, $container_id);
            if (!$stmtCheckLongTermContainer->execute()) {
                throw new Exception("Execution failed for checking long_term_container_data: " . $stmtCheckLongTermContainer->error);
            }
            $resultCheckLongTermContainer = $stmtCheckLongTermContainer->get_result();

            if ($resultCheckLongTermContainer->num_rows > 0) {
                // Entry exists, perform update
                $longTermContainerId = $resultCheckLongTermContainer->fetch_assoc()['id'];
                $stmtUpdateLongTermContainer = $conn->prepare("
                    UPDATE long_term_container_data
                    SET humidity_raw = ?, humidity_pct = ?, pump_ml_added = ?
                    WHERE id = ?
                ");
                if (!$stmtUpdateLongTermContainer) {
                    throw new Exception("Prepare failed for updating long_term_container_data: " . $conn->error);
                }
                $stmtUpdateLongTermContainer->bind_param(
                    "ddii",
                    $avg_humidity_raw,
                    $avg_humidity_pct,
                    $pump_ml_added,
                    $longTermContainerId
                );
                if (!$stmtUpdateLongTermContainer->execute()) {
                    throw new Exception("Execution failed for updating long_term_container_data: " . $stmtUpdateLongTermContainer->error);
                }
                $stmtUpdateLongTermContainer->close();
            } else {
                // Entry does not exist, perform insert
                $stmtInsertLongTermContainer = $conn->prepare("
                    INSERT INTO long_term_container_data (sensor_data_id, container_id, humidity_raw, humidity_pct, pump_ml_added)
                    VALUES (?, ?, ?, ?, ?)
                ");
                if (!$stmtInsertLongTermContainer) {
                    throw new Exception("Prepare failed for inserting into long_term_container_data: " . $conn->error);
                }
                $stmtInsertLongTermContainer->bind_param(
                    "isdii",
                    $longTermSensorId,
                    $container_id,
                    $avg_humidity_raw,
                    $avg_humidity_pct,
                    $pump_ml_added
                );
                if (!$stmtInsertLongTermContainer->execute()) {
                    throw new Exception("Execution failed for inserting into long_term_container_data: " . $stmtInsertLongTermContainer->error);
                }
                $stmtInsertLongTermContainer->close();
            }
            $stmtCheckLongTermContainer->close();
        }
        $stmtContainer->close();

        /**
         * Commit the transaction after successful operations
         */
        $conn->commit();

        /**
         * -------- Cleanup Short-Term Data --------
         */

        // Delete entries older than 48 hours
        $deleteShortTermQuery = "DELETE FROM short_term_sensor_data WHERE date_time < NOW() - INTERVAL 48 HOUR";
        if ($conn->query($deleteShortTermQuery)) {
            $deletedCountShortTerm = $conn->affected_rows;
            if ($deletedCountShortTerm > 0) {
                log_message("$deletedCountShortTerm entries deleted from short_term_sensor_data.");
            }
        } else {
            log_message("Database delete failed for short-term sensor data: " . $conn->error);
        }

        $deleteContainerQuery = "DELETE FROM short_term_container_data WHERE sensor_data_id NOT IN (SELECT id FROM short_term_sensor_data)";
        if ($conn->query($deleteContainerQuery)) {
            $deletedCountContainer = $conn->affected_rows;
            if ($deletedCountContainer > 0) {
                log_message("$deletedCountContainer entries deleted from short_term_container_data.");
            }
        } else {
            log_message("Database delete failed for short-term container data: " . $conn->error);
        }

        // Close connection
        $conn->close();

        // Respond with success
        log_message("Data inserted successfully for client IP: $client_ip");
        echo json_encode(["status" => "success", "message" => "Data inserted successfully"]);
    } catch (Exception $e) {
        // Rollback the transaction on error
        $conn->rollback();
        log_message("Transaction failed: " . $e->getMessage());
        http_response_code(500);
        echo json_encode(["status" => "error", "message" => "Transaction failed: " . $e->getMessage()]);
        exit;
    }
} else {
    log_message("Method not allowed: " . $_SERVER['REQUEST_METHOD']);
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Method not allowed"]);
}
