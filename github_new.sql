/*
Navicat MySQL Data Transfer

Source Server         : kali
Source Server Version : 50505
Source Host           : 192.168.138.132:3306
Source Database       : github

Target Server Type    : MYSQL
Target Server Version : 50505
File Encoding         : 65001

Date: 2019-08-14 16:39:43
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for Data_False
-- ----------------------------
DROP TABLE IF EXISTS `Data_False`;
CREATE TABLE `Data_False` (
  `n_task` varchar(255) DEFAULT NULL,
  `n_task_type` varchar(255) DEFAULT NULL,
  `n_system` varchar(255) DEFAULT NULL,
  `n_keyword` varchar(255) DEFAULT NULL,
  `n_writer` varchar(255) DEFAULT NULL,
  `n_project` varchar(255) DEFAULT NULL,
  `n_url` varchar(255) DEFAULT NULL,
  `n_value` varchar(9999) DEFAULT NULL,
  `n_time` varchar(255) DEFAULT NULL,
  `n_type` varchar(255) DEFAULT NULL,
  `n_remarks` varchar(2550) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of Data_False
-- ----------------------------

-- ----------------------------
-- Table structure for Data_True
-- ----------------------------
DROP TABLE IF EXISTS `Data_True`;
CREATE TABLE `Data_True` (
  `n_task` varchar(255) DEFAULT NULL,
  `n_task_type` varchar(255) DEFAULT NULL,
  `n_system` varchar(255) DEFAULT NULL,
  `n_keyword` varchar(255) DEFAULT NULL,
  `n_writer` varchar(255) DEFAULT NULL,
  `n_project` varchar(255) DEFAULT NULL,
  `n_url` varchar(255) DEFAULT NULL,
  `n_value` varchar(9999) DEFAULT NULL,
  `n_time` varchar(255) DEFAULT NULL,
  `n_type` varchar(255) DEFAULT NULL,
  `n_remarks` varchar(2550) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of Data_True
-- ----------------------------

-- ----------------------------
-- Table structure for Data_Wait
-- ----------------------------
DROP TABLE IF EXISTS `Data_Wait`;
CREATE TABLE `Data_Wait` (
  `n_task` varchar(255) DEFAULT NULL,
  `n_task_type` varchar(255) DEFAULT NULL,
  `n_system` varchar(255) DEFAULT NULL,
  `n_keyword` varchar(255) DEFAULT NULL,
  `n_writer` varchar(255) DEFAULT NULL,
  `n_project` varchar(255) DEFAULT NULL,
  `n_url` varchar(255) DEFAULT NULL,
  `n_value` varchar(9999) DEFAULT NULL,
  `n_time` varchar(255) DEFAULT NULL,
  `n_type` varchar(255) DEFAULT NULL,
  `n_remarks` varchar(2550) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of Data_Wait
-- ----------------------------

-- ----------------------------
-- Table structure for n_config
-- ----------------------------
DROP TABLE IF EXISTS `n_config`;
CREATE TABLE `n_config` (
  `n_task` varchar(255) DEFAULT NULL,
  `n_task_type` varchar(255) DEFAULT NULL,
  `n_keyword` varchar(255) DEFAULT NULL,
  `n_mode` varchar(255) DEFAULT NULL,
  `n_extension` varchar(255) DEFAULT NULL,
  `n_secondkeyword` varchar(255) DEFAULT NULL,
  `n_choose` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of n_config
-- ----------------------------
INSERT INTO `n_config` VALUES ('苏研', 'url', 'bigcloudsys.cn', 'normal-match', null, 'passw,vpn', 'closed');

-- ----------------------------
-- Table structure for n_githubtocken
-- ----------------------------
DROP TABLE IF EXISTS `n_githubtocken`;
CREATE TABLE `n_githubtocken` (
  `n_tocken` varchar(255) DEFAULT NULL,
  `n_value` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of n_githubtocken
-- ----------------------------
INSERT INTO `n_githubtocken` VALUES ('f774d5123bfebe91e347eea51bf161340f7356b2', '可用');
INSERT INTO `n_githubtocken` VALUES ('d097bbd7f692937780cde1125f74f14e6a6dc3b7', '可用');

-- ----------------------------
-- Table structure for n_login
-- ----------------------------
DROP TABLE IF EXISTS `n_login`;
CREATE TABLE `n_login` (
  `login_user` varchar(255) DEFAULT NULL,
  `login_passwd` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of n_login
-- ----------------------------
INSERT INTO `n_login` VALUES ('admin', 'admin');
