-- MySQL dump 10.13  Distrib 5.1.72, for debian-linux-gnu (i486)
--
-- Host: localhost    Database: erebus
-- ------------------------------------------------------
-- Server version	5.1.72-2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bots`
--

DROP TABLE IF EXISTS `bots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bots` (
  `nick` varchar(30) NOT NULL,
  `user` varchar(10) NOT NULL DEFAULT 'erebus',
  `bind` varchar(15) DEFAULT NULL,
  `authname` varchar(30) DEFAULT NULL,
  `authpass` varchar(20) DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `connected` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`nick`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bots`
--

LOCK TABLES `bots` WRITE;
/*!40000 ALTER TABLE `bots` DISABLE KEYS */;
INSERT INTO `bots` VALUES ('Erebus','erebus',NULL,NULL,NULL,1,0);
/*!40000 ALTER TABLE `bots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chans`
--

DROP TABLE IF EXISTS `chans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `chans` (
  `chname` varchar(100) NOT NULL,
  `bot` varchar(30) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`chname`),
  KEY `bot` (`bot`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chans`
--

LOCK TABLES `chans` WRITE;
/*!40000 ALTER TABLE `chans` DISABLE KEYS */;
INSERT INTO `chans` VALUES ('#dimetest','Erebus',1);
/*!40000 ALTER TABLE `chans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chusers`
--

DROP TABLE IF EXISTS `chusers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `chusers` (
  `chan` varchar(100) NOT NULL,
  `user` varchar(30) NOT NULL,
  `level` int(11) NOT NULL,
  PRIMARY KEY (`chan`,`user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chusers`
--

LOCK TABLES `chusers` WRITE;
/*!40000 ALTER TABLE `chusers` DISABLE KEYS */;
INSERT INTO `chusers` VALUES ('#dimetest','dimecadmium',10);
/*!40000 ALTER TABLE `chusers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `auth` varchar(30) NOT NULL,
  `level` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`auth`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('DimeCadmium',100),('BiohZn',100);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-12-22 13:07:13
