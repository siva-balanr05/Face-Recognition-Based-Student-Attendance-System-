-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS attendancereg;

-- Use the database
USE attendancereg;

-- Create the students table
CREATE TABLE IF NOT EXISTS students (
    reg_no VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Create the attendance table
CREATE TABLE IF NOT EXISTS attendance (
    reg_no VARCHAR(255),
    name VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reg_no, timestamp)
);

select * from attendance;
select * from students;