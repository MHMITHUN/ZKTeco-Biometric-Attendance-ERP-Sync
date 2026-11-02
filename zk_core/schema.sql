-- ============================================================================
-- Enterprise Biometric Attendance & HRMS MySQL Schema
-- Author: MD. Mahamudul Hasan (IT Officer)
-- Repository: ZKTeco-Biometric-Attendance-ERP-Sync
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `hrms_biometric_db`
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `hrms_biometric_db`;

-- 1. Master Employees Table
CREATE TABLE IF NOT EXISTS `employees` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `emp_code` VARCHAR(20) NOT NULL UNIQUE,
    `full_name` VARCHAR(100) NOT NULL,
    `department` VARCHAR(60) NOT NULL,
    `designation` VARCHAR(60) NOT NULL,
    `shift_schedule` ENUM('GENERAL', 'SHIFT_A', 'SHIFT_B', 'NIGHT') DEFAULT 'GENERAL',
    `card_rfid` VARCHAR(30) NULL,
    `biometric_enrolled` TINYINT(1) DEFAULT 1,
    `status` ENUM('ACTIVE', 'ON_LEAVE', 'RESIGNED') DEFAULT 'ACTIVE',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_emp_code` (`emp_code`),
    INDEX `idx_department` (`department`)
) ENGINE=InnoDB;

-- 2. ZKTeco Terminal Devices Register
CREATE TABLE IF NOT EXISTS `zk_terminals` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `device_code` VARCHAR(30) NOT NULL UNIQUE,
    `device_name` VARCHAR(100) NOT NULL,
    `ip_address` VARCHAR(45) NOT NULL,
    `port` INT UNSIGNED DEFAULT 4370,
    `terminal_type` ENUM('FACE_RECOGNITION', 'FINGERPRINT', 'MULTI_MODAL') DEFAULT 'MULTI_MODAL',
    `zone_location` VARCHAR(100) NOT NULL,
    `firmware_version` VARCHAR(50) NULL,
    `last_heartbeat` DATETIME NULL,
    `is_online` TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- 3. Raw Biometric Attendance Punches (High Volume Ingestion)
CREATE TABLE IF NOT EXISTS `attendance_punches` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `emp_code` VARCHAR(20) NOT NULL,
    `device_code` VARCHAR(30) NOT NULL,
    `punch_timestamp` DATETIME NOT NULL,
    `punch_type` ENUM('CHECK_IN', 'CHECK_OUT', 'BREAK_OUT', 'BREAK_IN', 'AUTO') DEFAULT 'AUTO',
    `verify_mode` ENUM('FACE', 'FINGERPRINT', 'PASSWORD', 'CARD') NOT NULL,
    `match_score` DECIMAL(5,2) DEFAULT 98.50,
    `raw_terminal_sn` VARCHAR(50) NULL,
    `synced_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_punch_emp` FOREIGN KEY (`emp_code`) REFERENCES `employees` (`emp_code`) ON DELETE CASCADE,
    INDEX `idx_emp_time` (`emp_code`, `punch_timestamp`),
    INDEX `idx_punch_date` (`punch_timestamp`)
) ENGINE=InnoDB;

-- 4. Daily Shift Reconciled Summary (Automated Aggregation)
CREATE TABLE IF NOT EXISTS `daily_shift_summary` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `shift_date` DATE NOT NULL,
    `emp_code` VARCHAR(20) NOT NULL,
    `first_in` DATETIME NULL,
    `last_out` DATETIME NULL,
    `total_duration_minutes` INT UNSIGNED DEFAULT 0,
    `is_late` TINYINT(1) DEFAULT 0,
    `late_minutes` INT UNSIGNED DEFAULT 0,
    `overtime_minutes` INT UNSIGNED DEFAULT 0,
    `attendance_status` ENUM('PRESENT', 'LATE', 'HALF_DAY', 'ABSENT', 'LEAVE') DEFAULT 'PRESENT',
    `audit_compliance_locked` TINYINT(1) DEFAULT 0,
    UNIQUE KEY `uk_emp_date` (`shift_date`, `emp_code`),
    INDEX `idx_date_status` (`shift_date`, `attendance_status`)
) ENGINE=InnoDB;

-- Sample Seed Data
INSERT INTO `employees` (`emp_code`, `full_name`, `department`, `designation`) VALUES
('EMP-1042', 'Md. Rafiqul Islam', 'Sewing Production (Line 2)', 'Sewing Line Operator'),
('EMP-0881', 'Nazma Begum', 'Quality Assurance (QA-03)', 'QA Inspector'),
('EMP-0315', 'Tanvir Hossain', 'Merchandising & Planning', 'Merchandiser'),
('EMP-1190', 'Farhana Akter', 'Cutting Section', 'Pattern Master'),
('EMP-1508', 'Md. Mahamudul Hasan', 'IT & Systems Operations', 'IT Officer')
ON DUPLICATE KEY UPDATE `full_name`=`full_name`;
