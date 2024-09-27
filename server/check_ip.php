<?php
// check_ip.php

function is_ip_allowed($client_ip)
{
    // Include the configuration file
    $config = include('api_config.php');
    $trusted_ip = $config['trusted_ip']; // Get the trusted IP from the config

    // Check if the trusted IP is a complete IP or a prefix
    if (filter_var($trusted_ip, FILTER_VALIDATE_IP)) {
        // If the trusted IP is a complete IP address, check for exact match
        return $client_ip === $trusted_ip;
    } else {
        // Handle the case where the trusted IP is a range (prefix)
        $client_ip_prefix = substr($client_ip, 0, strrpos($client_ip, '.'));
        $trusted_ip_prefix = substr($trusted_ip, 0, strrpos($trusted_ip, '.'));

        // Check if the prefixes match
        return $client_ip_prefix === $trusted_ip_prefix;
    }
}
