-- Short-Term Main Sensor Data Table
CREATE TABLE short_term_sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_time DATETIME NOT NULL,
    cpu_temp FLOAT NOT NULL,
    room_temp_SHT40 FLOAT NOT NULL,
    room_temp_BMP280 FLOAT NOT NULL,
    room_humidity_SHT40 FLOAT NOT NULL,
    room_pressure_BMP280 FLOAT NOT NULL
);

-- Short-Term Container-Specific Data Table
CREATE TABLE short_term_container_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    short_term_sensor_data_id INT NOT NULL,
    container_id VARCHAR(3) NOT NULL,
    humidity_raw FLOAT NOT NULL,
    humidity_pct FLOAT NOT NULL,
    pump_ml_added INT NOT NULL,
    FOREIGN KEY (short_term_sensor_data_id) REFERENCES short_term_sensor_data(id) ON DELETE CASCADE
);

-- Long-Term Main Sensor Data Table
CREATE TABLE long_term_sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_time DATETIME NOT NULL,
    cpu_temp FLOAT NOT NULL,
    room_temp_SHT40 FLOAT NOT NULL,
    room_temp_BMP280 FLOAT NOT NULL,
    room_humidity_SHT40 FLOAT NOT NULL,
    room_pressure_BMP280 FLOAT NOT NULL
);

-- Long-Term Container-Specific Data Table
CREATE TABLE long_term_container_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    long_term_sensor_data_id INT NOT NULL,
    container_id VARCHAR(3) NOT NULL,
    humidity_raw FLOAT NOT NULL,
    humidity_pct FLOAT NOT NULL,
    pump_ml_added INT NOT NULL,
    FOREIGN KEY (long_term_sensor_data_id) REFERENCES long_term_sensor_data(id) ON DELETE CASCADE
);
