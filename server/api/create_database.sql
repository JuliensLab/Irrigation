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
    sensor_data_id INT NOT NULL,
    container_id VARCHAR(3) NOT NULL,
    humidity_tgt FLOAT NOT NULL,
    humidity_raw FLOAT NOT NULL,
    humidity_pct FLOAT NOT NULL,
    pump_ml_added INT NOT NULL,
    FOREIGN KEY (sensor_data_id) REFERENCES short_term_sensor_data(id) ON DELETE CASCADE
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
    sensor_data_id INT NOT NULL,
    container_id VARCHAR(3) NOT NULL,
    humidity_tgt FLOAT NOT NULL,
    humidity_raw FLOAT NOT NULL,
    humidity_pct FLOAT NOT NULL,
    pump_ml_added INT NOT NULL,
    FOREIGN KEY (sensor_data_id) REFERENCES long_term_sensor_data(id) ON DELETE CASCADE
);

-- Create indexes for efficient lookup
-- short_term_sensor_data
CREATE INDEX idx_short_term_sensor_date_time ON short_term_sensor_data(date_time);

-- short_term_container_data
CREATE INDEX idx_short_term_container_sensor_id ON short_term_container_data(short_term_sensor_data_id);
CREATE INDEX idx_short_term_container_container_id ON short_term_container_data(container_id);
CREATE INDEX idx_short_term_container_sensor_container ON short_term_container_data(short_term_sensor_data_id, container_id);

-- long_term_sensor_data
CREATE INDEX idx_long_term_sensor_date_time ON long_term_sensor_data(date_time);

-- long_term_container_data
CREATE INDEX idx_long_term_container_sensor_id ON long_term_container_data(long_term_sensor_data_id);
CREATE INDEX idx_long_term_container_container_id ON long_term_container_data(container_id);
CREATE INDEX idx_long_term_container_sensor_container ON long_term_container_data(long_term_sensor_data_id, container_id);

-- verification 
SHOW INDEX FROM short_term_sensor_data;
SHOW INDEX FROM short_term_container_data;
SHOW INDEX FROM long_term_sensor_data;
SHOW INDEX FROM long_term_container_data;

-- regular maintenance
OPTIMIZE TABLE short_term_sensor_data;
OPTIMIZE TABLE short_term_container_data;
OPTIMIZE TABLE long_term_sensor_data;
OPTIMIZE TABLE long_term_container_data;

-- Use EXPLAIN to Validate Index Usage
EXPLAIN SELECT
    AVG(cpu_temp) AS avg_cpu_temp,
    AVG(room_temp_SHT40) AS avg_room_temp_SHT40,
    AVG(room_temp_BMP280) AS avg_room_temp_BMP280,
    AVG(room_humidity_SHT40) AS avg_room_humidity_SHT40,
    AVG(room_pressure_BMP280) AS avg_room_pressure_BMP280
FROM short_term_sensor_data
WHERE date_time >= '2024-04-01 00:00:00' AND date_time < '2024-04-01 01:00:00';

