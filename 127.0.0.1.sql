-- phpMyAdmin SQL Dump
-- version 3.5.0
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: May 29, 2012 at 03:43 PM
-- Server version: 5.6.4-m7-log
-- PHP Version: 5.3.9

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `client`
--
CREATE DATABASE `client` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `client`;



--
-- Table structure for table `recv_message`
--

CREATE TABLE IF NOT EXISTS `recv_message` (
  `rid` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(255) NOT NULL,
  `message` varchar(255) NOT NULL,
  `dateline` int(11) NOT NULL,
  PRIMARY KEY (`rid`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=81 ;

-- --------------------------------------------------------

--
-- Table structure for table `send_history`
--

CREATE TABLE IF NOT EXISTS `send_history` (
  `sid` int(11) NOT NULL AUTO_INCREMENT,
  `sqid` int(11) NOT NULL,
  `phone` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `sendtime` int(11) NOT NULL,
  `recvtime` int(11) NOT NULL DEFAULT '0',
  `msgid` varchar(255) NOT NULL,
  `pid` int(11) NOT NULL,
  `status` tinyint(5) NOT NULL DEFAULT '0',
  PRIMARY KEY (`sid`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=5442 ;

-- --------------------------------------------------------

--
-- Table structure for table `send_pool`
--

CREATE TABLE IF NOT EXISTS `send_pool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `uid` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `dateline` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=4201 ;

-- --------------------------------------------------------

--
-- Table structure for table `send_pool_back`
--

CREATE TABLE IF NOT EXISTS `send_pool_back` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone` varchar(255) NOT NULL,
  `message` varchar(255) NOT NULL,
  `username` varchar(255) NOT NULL,
  `uid` varchar(11) NOT NULL,
  `dateline` varchar(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=2237 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
