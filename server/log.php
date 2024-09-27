<?php

// Logging function
function log_message(...$messages)
{
    $log_file = '/home/u478317206/domains/irrigationmars.com/public_html/api/logfile.log'; // Use the absolute path
    $timestamp = date("Y-m-d H:i:s");
    $formatted_messages = [];

    foreach ($messages as $message) {
        // Check if the message is an array
        if (is_array($message)) {
            // Convert arrays to a string (JSON format for clarity)
            $formatted_messages[] = json_encode($message);
        } else {
            // Otherwise, just convert the message to string
            $formatted_messages[] = (string)$message;
        }
    }

    // Combine formatted messages into a single string, separated by spaces
    $combined_message = implode(" ", $formatted_messages);

    if (file_put_contents($log_file, "[$timestamp] $combined_message" . PHP_EOL, FILE_APPEND) === false) {
        echo "Failed to write to log file.";
    }
}
