CREATE DATABASE micro_pa;

CREATE TABLE `micro_pa`.`to_do_list` (
  `EVENT_NUMBER` INT NOT NULL AUTO_INCREMENT,
  `EVENT_DATETIME` DATETIME NOT NULL,
  `EVENT_NAME` VARCHAR(255) NOT NULL,
  `EVENT_COMPLETED` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`EVENT_NUMBER`)
);
