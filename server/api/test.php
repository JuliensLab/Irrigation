<?php
// test.php

// Get the client's IP address
$client_ip = $_SERVER['REMOTE_ADDR'];

// Call the function to check if the client's IP is allowed
include('check_ip.php');
$is_allowed = is_ip_allowed($client_ip);

// Return the appropriate response
if ($is_allowed) {
    // Return a JSON response with "Hello World"
    header('Content-Type: application/json');
    echo json_encode(['message' => 'Hello World', 'client_ip' => $client_ip]);
} else {
    // Return a 403 Forbidden response if the IP is not allowed
    http_response_code(403);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Forbidden: Your IP is not allowed.', 'client_ip' => $client_ip]);
}
