BEGIN;
--
-- Alter field category on resources
--
ALTER TABLE `config_center_resources` MODIFY `category` integer NOT NULL;

COMMIT;
