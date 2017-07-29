BEGIN;
--
-- Create model Resources
--
CREATE TABLE `config_center_resources` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(128) NOT NULL, `category` varchar(16) NOT NULL, `comment` varchar(256) NOT NULL);
--
-- Create model ResTypes
--
CREATE TABLE `config_center_restypes` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(32) NOT NULL);
--
-- Create model SVCResources
--
CREATE TABLE `config_center_svcresources` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `res_id` integer NOT NULL, `svc_id` integer NOT NULL);
--
-- Add field type to resources
--
ALTER TABLE `config_center_resources` ADD COLUMN `type_id` integer NOT NULL;
ALTER TABLE `config_center_resources` ALTER COLUMN `type_id` DROP DEFAULT;
ALTER TABLE `config_center_svcresources` ADD CONSTRAINT `config_center_svcr_res_id_34001e34_fk_config_center_resources_id` FOREIGN KEY (`res_id`) REFERENCES `config_center_resources` (`id`);
ALTER TABLE `config_center_svcresources` ADD CONSTRAINT `config_center_svcresources_svc_id_2a8df2bc_fk_asset_gogroup_id` FOREIGN KEY (`svc_id`) REFERENCES `asset_gogroup` (`id`);
CREATE INDEX `config_center_resources_94757cae` ON `config_center_resources` (`type_id`);
ALTER TABLE `config_center_resources` ADD CONSTRAINT `config_center_reso_type_id_7c82abd5_fk_config_center_restypes_id` FOREIGN KEY (`type_id`) REFERENCES `config_center_restypes` (`id`);

COMMIT;
