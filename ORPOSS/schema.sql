-- ============================================================
--  ORPOSS Database Schema
--  Run this in phpMyAdmin or via: mysql -u root ORPOSS < schema.sql
-- ============================================================

USE `ORPOSS`;

-- ── Order Items (Product Catalog) ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `order_items` (
  `id`         INT           NOT NULL AUTO_INCREMENT,
  `name`       VARCHAR(100)  NOT NULL,
  `price`      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `stock`      INT           NOT NULL DEFAULT 0,
  `image_url`  VARCHAR(500)  DEFAULT NULL,
  `cost`       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `category`   VARCHAR(100)  DEFAULT 'All',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Safe column additions for existing databases
ALTER TABLE `order_items` ADD COLUMN IF NOT EXISTS `cost`     DECIMAL(10,2) NOT NULL DEFAULT 0.00;
ALTER TABLE `order_items` ADD COLUMN IF NOT EXISTS `category` VARCHAR(100)  DEFAULT 'All';

INSERT INTO `order_items` (`name`, `price`, `stock`, `cost`, `category`) VALUES
('Burger',      55.00, 50, 30.00, 'Main'),
('Fries',       35.00, 50, 20.00, 'Sides'),
('Chicken',     99.00, 50, 60.00, 'Main'),
('Soda',        25.00, 50, 15.00, 'Drinks'),
('Hotdog',      40.00, 50, 25.00, 'Main'),
('Ice Cream',   35.00, 50, 20.00, 'Dessert'),
('Extra Gravy', 15.00, 50, 10.00, 'Sides'),
('Extra Rice',  20.00, 50, 12.00, 'Sides')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- ── Orders ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `orders` (
  `id`           INT          NOT NULL AUTO_INCREMENT,
  `invoice_no`   VARCHAR(20)  NOT NULL UNIQUE,
  `order_type`   ENUM('Dine-In','Take-Out') NOT NULL DEFAULT 'Dine-In',
  `payment_mode` ENUM('counter','kiosk')    NOT NULL DEFAULT 'counter',
  `total`        DECIMAL(10,2) NOT NULL,
  `cash`         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `change_amt`   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `status`       ENUM('preparing','serving','claimed','cancelled') NOT NULL DEFAULT 'preparing',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `serving_at`   DATETIME     DEFAULT NULL,
  `claimed_at`   DATETIME     DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_status`  (`status`),
  INDEX `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Order Lines ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `order_lines` (
  `id`         INT           NOT NULL AUTO_INCREMENT,
  `invoice_no` VARCHAR(20)   NOT NULL,
  `name`       VARCHAR(100)  NOT NULL,
  `qty`        INT           NOT NULL,
  `price`      DECIMAL(10,2) NOT NULL,
  `product_id` INT           DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_invoice` (`invoice_no`),
  FOREIGN KEY (`invoice_no`) REFERENCES `orders`(`invoice_no`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
