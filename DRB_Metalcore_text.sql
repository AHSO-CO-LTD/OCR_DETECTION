CREATE DATABASE IF NOT EXISTS `drb_text`
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `drb_text`;
-- Bảng current_session
DROP TABLE IF EXISTS `current_session`;
CREATE TABLE `current_session` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `UserName` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `Token` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ExpiresAt` DATETIME DEFAULT NULL,
  `ResultTime` INT DEFAULT 1,
  `SleepTime` INT DEFAULT 10,
  `ZoomFactor` DECIMAL(3,2) DEFAULT '0.4',
  `OffsetX` INT DEFAULT 300,
  `OffsetY` INT DEFAULT 1400,
  `ImageWidth` INT DEFAULT 2500,
  `ImageHeight` INT DEFAULT 1000,
  `PLCIP` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT "192.168.3.250",
  `PLCProtocol` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT "TCP",
  `PLCPort` INT DEFAULT 502,
  `ROIx1` INT DEFAULT 760,
  `ROIx2` INT DEFAULT 1250,
  `ROIx3` INT DEFAULT 1730,
  `ROIx4` INT DEFAULT 2220,
  `ROIx5` INT DEFAULT 2710,
  `ROIy1` INT DEFAULT 1180,
  `ROIy2` INT DEFAULT 1180,
  `ROIy3` INT DEFAULT 1180,
  `ROIy4` INT DEFAULT 1180,
  `ROIy5` INT DEFAULT 1180,
  `CreatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Dữ liệu mẫu
INSERT INTO `current_session` (`ID`) VALUES (1);

USE `drb_text`;
-- Bảng product
DROP TABLE IF EXISTS `product`;
CREATE TABLE `product` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `ProductName` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DefaultNumber` INT DEFAULT 160,
  `Exposure` INT DEFAULT 3500,
  `ThresholdAccept` DECIMAL(2,1) DEFAULT 0.5,
  `ThresholdMns` DECIMAL(2,1) DEFAULT 0.5,
  `CreatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  UNIQUE KEY (`ProductName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

USE `drb_text`;
-- Bảng users
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `UserID` INT NOT NULL AUTO_INCREMENT,
  `UserName` VARCHAR(64) COLLATE utf8mb4_0900_as_cs NOT NULL,
  `FullName` VARCHAR(64) NOT NULL,
  `Department` VARCHAR(64) DEFAULT NULL,
  `No_id` VARCHAR(64) DEFAULT NULL,
  `PasswordHash` VARCHAR(128) COLLATE utf8mb4_0900_as_cs NOT NULL,
  `Role` VARCHAR(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Operator',
  `Active` ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
  `Attempt` INT NOT NULL DEFAULT 0,
  `LastLoginAt` DATETIME DEFAULT NULL,
  `CreatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`UserID`),
  UNIQUE KEY (`UserName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;
-- Dữ liệu mẫu
-- Mật khẩu mặc định: admin=Admin@DRB2024! | operator1=Oper@DRB2024!
-- ĐỔI NGAY SAU KHI DEPLOY — đây chỉ là hash khởi tạo
INSERT INTO `users` (`UserID`, `UserName`, `FullName`, `PasswordHash`, `Role`)
VALUES (1, 'admin', 'Administrator', '$2b$12$Dw0WDeWobgPMemGV7YNjcODIdj68.DllUukKw/ChXviHS2R0Fnnxm', 'Administrator'),
       (2, 'operator1', 'Operator 1',  '$2b$12$gT77U2cq.P8ao571CnKLnOoqKXe/zThM1gxik1wqzi44oz4qFPAOa', 'Operator');

USE `drb_text`;
-- Bảng loginaudit — ghi lại các sự kiện login (21CFR Part 11)
DROP TABLE IF EXISTS `loginaudit`;
CREATE TABLE `loginaudit` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `UserID` INT DEFAULT NULL,
  `UserName` VARCHAR(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `EventType` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `IPAddress` VARCHAR(45) DEFAULT NULL,
  `CreatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  INDEX (`UserName`),
  INDEX (`CreatedAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

USE `drb_text`;
-- Bảng auditlog — ghi lại các thay đổi hệ thống (21CFR Part 11)
DROP TABLE IF EXISTS `auditlog`;
CREATE TABLE `auditlog` (
  `ID` BIGINT NOT NULL AUTO_INCREMENT,
  `UserName` VARCHAR(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Action` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `Details` TEXT,
  `CreatedAt` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  INDEX (`UserName`),
  INDEX (`CreatedAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;