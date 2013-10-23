/*
 Navicat Premium Data Transfer

 Source Server         : lskobe
 Source Server Type    : MySQL
 Source Server Version : 50610
 Source Host           : localhost
 Source Database       : gitarchive

 Target Server Type    : MySQL
 Target Server Version : 50610
 File Encoding         : utf-8

 Date: 10/23/2013 22:47:11 PM
*/

SET NAMES utf8;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
--  Table structure for `Actor`
-- ----------------------------
DROP TABLE IF EXISTS `Actor`;
CREATE TABLE `Actor` (
  `_id` int(11) NOT NULL,
  `location` varchar(100) NOT NULL,
  `login` varchar(80) NOT NULL,
  `email` varchar(80) NOT NULL,
  `type` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `blog` varchar(100) DEFAULT NULL,
  `regular_location` int(11) NOT NULL,
  PRIMARY KEY (`_id`),
  KEY `location` (`regular_location`),
  CONSTRAINT `location` FOREIGN KEY (`regular_location`) REFERENCES `Location` (`_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `Event`
-- ----------------------------
DROP TABLE IF EXISTS `Event`;
CREATE TABLE `Event` (
  `_id` int(11) NOT NULL,
  `url` varchar(150) NOT NULL,
  `type` varchar(20) NOT NULL,
  `created_at` time NOT NULL,
  `actor` int(11) NOT NULL,
  `repo` int(11) NOT NULL,
  PRIMARY KEY (`_id`),
  KEY `actor` (`actor`),
  KEY `repo` (`repo`),
  CONSTRAINT `actor` FOREIGN KEY (`actor`) REFERENCES `Actor` (`_id`),
  CONSTRAINT `repo` FOREIGN KEY (`repo`) REFERENCES `Repo` (`_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `Location`
-- ----------------------------
DROP TABLE IF EXISTS `Location`;
CREATE TABLE `Location` (
  `_id` int(11) NOT NULL AUTO_INCREMENT,
  `country` varchar(80) NOT NULL,
  `name` varchar(80) NOT NULL,
  `lat` float NOT NULL,
  `lng` float NOT NULL,
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
--  Table structure for `Repo`
-- ----------------------------
DROP TABLE IF EXISTS `Repo`;
CREATE TABLE `Repo` (
  `_id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL,
  `owner` varchar(150) NOT NULL,
  `language` varchar(50) NOT NULL,
  `url` varchar(150) NOT NULL,
  `description` text NOT NULL,
  `forks` int(11) NOT NULL,
  `stars` int(11) NOT NULL,
  `create_at` time NOT NULL,
  `push_at` time NOT NULL,
  `id` varchar(100) NOT NULL,
  `watchers` int(11) NOT NULL,
  `private` varchar(20) NOT NULL,
  PRIMARY KEY (`_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

