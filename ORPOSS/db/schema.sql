-- ============================================================
--  ORPOSS Database Schema
--  Run this in phpMyAdmin or via: mysql -u root ORPOSS < schema.sql
-- ============================================================

-- ── Database ──────────────────────────────────────────────────────────────────
-- Using the ORPOSS database created in Aiven console.
-- If it doesn't exist yet, create it in Aiven first, then run this file.
USE `ORPOSS`;

-- ── Order Items (Product Catalog) ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `order_items` (
  `id`         INT(11)       NOT NULL AUTO_INCREMENT,
  `name`       VARCHAR(100)  NOT NULL,
  `price`      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `stock`      INT(11)       NOT NULL DEFAULT 0,
  `image_url`  VARCHAR(500)  DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `order_items` (`name`, `price`, `stock`) VALUES
('Burger',      55.00, 50),
('Fries',       35.00, 50),
('Chicken',     99.00, 50),
('Soda',        25.00, 50),
('Hotdog',      40.00, 50),
('Ice Cream',   35.00, 50),
('Extra Gravy', 15.00, 50),
('Extra Rice',  20.00, 50)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- ── Orders ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `orders` (
  `id`           INT(11)      NOT NULL AUTO_INCREMENT,
  `invoice_no`   VARCHAR(20)  NOT NULL UNIQUE,
  `order_type`   ENUM('Dine-In','Take-Out') NOT NULL DEFAULT 'Dine-In',
  `payment_mode` ENUM('counter','kiosk')    NOT NULL DEFAULT 'counter',
  `total`        DECIMAL(10,2) NOT NULL,
  `cash`         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `change_amt`   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `status`       ENUM('preparing','serving','claimed') NOT NULL DEFAULT 'preparing',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `serving_at`   DATETIME     DEFAULT NULL,
  `claimed_at`   DATETIME     DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Order Lines (Per-order breakdown) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `order_lines` (
  `id`         INT(11)       NOT NULL AUTO_INCREMENT,
  `invoice_no` VARCHAR(20)   NOT NULL,
  `name`       VARCHAR(100)  NOT NULL,
  `qty`        INT(11)       NOT NULL,
  `price`      DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_invoice` (`invoice_no`),
  FOREIGN KEY (`invoice_no`) REFERENCES `orders`(`invoice_no`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
