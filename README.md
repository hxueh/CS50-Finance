# CS50 Finance in MySQL

Rewrite [CS50 Finance's](https://finance.cs50.net) background. Instead of SQLite, using MySQL. Just for fun🙃

## Requirements
[MySQL](https://www.mysql.com)

[PyMySQL](https://github.com/PyMySQL/PyMySQL)

## Start
```
$ mysql

$ CREATE DATABASE IF NOT EXIST cs50_finance

$ CREATE TABLE `users` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `username` text NOT NULL,
  `hash` text NOT NULL,
  `cash` decimal(10,2) NOT NULL DEFAULT '10000.00',
  PRIMARY KEY (`id`)
  ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
  
$ CREATE TABLE `portfolio` (
  `transit_id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` tinytext NOT NULL,
  `shares` int(10) unsigned NOT NULL,
  `time` text NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `action` tinytext NOT NULL,
  `buyer` int(10) unsigned NOT NULL,
  PRIMARY KEY (`transit_id`),
  KEY `buyer` (`buyer`),
  CONSTRAINT `portfolio_ibfk_1` FOREIGN KEY (`buyer`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
```

```
$ EXPORT FLASK_APP=application.py
$ flask run
```