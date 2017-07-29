BEGIN;
--
-- Alter field category on resources
--
ALTER TABLE `config_center_resources` MODIFY `category` varchar(16) NOT NULL;

COMMIT;
