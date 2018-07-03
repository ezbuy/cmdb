CREATE TABLE `project_crontab_crontabcmd` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `cmd` longtext NOT NULL, `auto_cmd` longtext NOT NULL, `frequency` varchar(16) NOT NULL, `cmd_status` integer NOT NULL, `is_valid` integer NOT NULL, `create_time` datetime(6) NULL, `update_time` datetime(6) NULL, `last_run_result` varchar(16) NULL,`last_run_time` datetime(6) NULL, `creator_id` integer NOT NULL);
 
CREATE TABLE `project_crontab_svn` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `project_name` varchar(64) NOT NULL, `username` varchar(32) NOT NULL, `password` varchar(32) NOT NULL, `repo` varchar(128) NOT NULL, `local_path` varchar(64) NOT NULL, `create_time` datetime(6) NULL, `update_time` datetime(6) NULL, `creator_id` integer NOT NULL,`salt_minion_id` integer NOT NULL, `updater_id` integer NULL);
 
ALTER TABLE `project_crontab_crontabcmd` ADD COLUMN `svn_id` integer NOT NULL;
ALTER TABLE `project_crontab_crontabcmd` ALTER COLUMN `svn_id` DROP DEFAULT;
 
ALTER TABLE `project_crontab_crontabcmd` ADD COLUMN `updater_id` integer NULL;
ALTER TABLE `project_crontab_crontabcmd` ALTER COLUMN `updater_id` DROP DEFAULT;
 
ALTER TABLE `project_crontab_crontabcmd` ADD CONSTRAINT `project_crontab_crontabcmd_creator_id_4d1261f5_fk_auth_user_id` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `project_crontab_svn` ADD CONSTRAINT `project_crontab_svn_creator_id_9694f5f8_fk_auth_user_id` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `project_crontab_svn` ADD CONSTRAINT `project_crontab_svn_salt_minion_id_5b8560d1_fk_asset_minion_id` FOREIGN KEY (`salt_minion_id`) REFERENCES `asset_minion` (`id`);
ALTER TABLE `project_crontab_svn` ADD CONSTRAINT `project_crontab_svn_updater_id_06b31142_fk_auth_user_id` FOREIGN KEY (`updater_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `project_crontab_crontabcmd_b4191281` ON `project_crontab_crontabcmd` (`svn_id`);
ALTER TABLE `project_crontab_crontabcmd` ADD CONSTRAINT `project_crontab_cronta_svn_id_19b43599_fk_project_crontab_svn_id` FOREIGN KEY (`svn_id`) REFERENCES `project_crontab_svn` (`id`);
CREATE INDEX `project_crontab_crontabcmd_9ba6c90a` ON `project_crontab_crontabcmd` (`updater_id`);
ALTER TABLE `project_crontab_crontabcmd` ADD CONSTRAINT `project_crontab_crontabcmd_updater_id_5cccc316_fk_auth_user_id` FOREIGN KEY (`updater_id`) REFERENCES `auth_user` (`id`);


CREATE TABLE `asset_cron_minion` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(32) NULL);
ALTER TABLE `asset_cron_minion` ADD COLUMN `saltminion_id` integer NOT NULL;
ALTER TABLE `asset_cron_minion` ALTER COLUMN `saltminion_id` DROP DEFAULT;
ALTER TABLE `asset_crontab_svn` ADD COLUMN `minion_hostname_id` integer NOT NULL;
ALTER TABLE `asset_crontab_svn` ALTER COLUMN `minion_hostname_id` DROP DEFAULT;
CREATE INDEX `asset_crontab_svn_30148987` ON `asset_crontab_svn` (`minion_hostname_id`);
ALTER TABLE `asset_crontab_svn` DROP FOREIGN KEY `asset_crontab_svn_hostname_id_c6ccdf3d_fk_asset_cron_minion_id`;
ALTER TABLE `asset_crontab_svn` MODIFY `hostname_id` integer NULL;
ALTER TABLE `asset_crontab_svn` ADD CONSTRAINT `asset_crontab_svn_hostname_id_c6ccdf3d_fk_asset_minion_id` FOREIGN KEY (`hostname_id`) REFERENCES `asset_minion` (`id`);