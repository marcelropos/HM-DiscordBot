CREATE TABLE `Guild` (
  `guild_id` int PRIMARY KEY,
  `ghost_warn_deadline` int NOT NULL,
  `ghost_kick_deadline` int NOT NULL,
  `ghost_time_to_check` TIME NOT NULL,
  `ghost_enabled` bool NOT NULL,
  `debug_channel` int NOT NULL,
  `bot_channel` int NOT NULL,
  `help_channel` int NOT NULL,
  `logger_pipe_channel` int,
  `study_group_category` int NOT NULL,
  `subject_group_category` int NOT NULL,
  `studenty_role` int NOT NULL,
  `tmp_studenty_role` int,
  `moderator_role` int NOT NULL,
  `newsletter_role` int NOT NULL,
  `nsfw_role` int NOT NULL,
  `study_role_separator_role` int NOT NULL,
  `subject_role_separator_role` int NOT NULL,
  `friend_role` int NOT NULL,
  `tmpc_keep_time` TIME NOT NULL,
  `alumni_role` int NOT NULL,
  `alumni_role_separator_role` int NOT NULL
);

CREATE TABLE `Alumni_roles` (
  `role` int,
  `guild_id` int NOT NULL,
  PRIMARY KEY (`role`, `guild_id`)
);

CREATE TABLE `Study_groups` (
  `id` int AUTO_INCREMENT,
  `guild_id` int NOT NULL,
  `name` tinytext NOT NULL,
  `color` int NOT NULL,
  `active` bool NOT NULL DEFAULT True,
  PRIMARY KEY (`id`, `guild_id`)
);

CREATE TABLE `Semester_study_groups` (
  `role` int,
  `study_group_id` int NOT NULL,
  `semester` int NOT NULL,
  `text_channel` int UNIQUE NOT NULL,
  PRIMARY KEY (`role`, `study_group_id`)
);

CREATE TABLE `Subject` (
  `role` int,
  `guild_id` int NOT NULL,
  `name` tinytext NOT NULL,
  `text_channel` int UNIQUE NOT NULL,
  PRIMARY KEY (`role`, `guild_id`)
);

CREATE TABLE `Study_subject_link` (
  `study_group_role` int,
  `subject_role` int,
  `guild_id` int,
  PRIMARY KEY (`study_group_role`, `subject_role`, `guild_id`)
);

CREATE TABLE `Tmpc_join_channel` (
  `voice_channel` int,
  `guild_id` int,
  `persist` bool NOT NULL,
  PRIMARY KEY (`voice_channel`, `guild_id`)
);

CREATE TABLE `Tmpc` (
  `voice_channel` int,
  `text_channel` int NOT NULL,
  `guild_id` int NOT NULL,
  `owner` int NOT NULL,
  `persist` bool NOT NULL,
  `token` int NOT NULL,
  `keep` bool NOT NULL DEFAULT False,
  `deleteAt` DATETIME,
  PRIMARY KEY (`voice_channel`, `guild_id`)
);

CREATE TABLE `Token_message` (
  `tmpc_voice_channel` int,
  `message` int,
  PRIMARY KEY (`tmpc_voice_channel`, `message`)
);

CREATE TABLE `Main_log_pip_channel` (
  `id` int PRIMARY KEY
);

CREATE UNIQUE INDEX `Study_groups_index_0` ON `Study_groups` (`guild_id`, `name`);

CREATE UNIQUE INDEX `Semester_study_groups_index_1` ON `Semester_study_groups` (`study_group_id`, `semester`);

CREATE UNIQUE INDEX `Subject_index_2` ON `Subject` (`guild_id`, `name`);

CREATE UNIQUE INDEX `Tmpc_index_3` ON `Tmpc` (`text_channel`, `guild_id`);

ALTER TABLE `Alumni_roles` ADD FOREIGN KEY (`guild_id`) REFERENCES `Guild` (`guild_id`);

ALTER TABLE `Study_groups` ADD FOREIGN KEY (`guild_id`) REFERENCES `Guild` (`guild_id`);

ALTER TABLE `Semester_study_groups` ADD FOREIGN KEY (`study_group_id`) REFERENCES `Study_groups` (`id`);

ALTER TABLE `Subject` ADD FOREIGN KEY (`guild_id`) REFERENCES `Guild` (`guild_id`);

ALTER TABLE `Study_subject_link` ADD FOREIGN KEY (`study_group_role`) REFERENCES `Semester_study_groups` (`role`);

ALTER TABLE `Study_subject_link` ADD FOREIGN KEY (`subject_role`) REFERENCES `Subject` (`role`);

ALTER TABLE `Study_subject_link` ADD FOREIGN KEY (`guild_id`) REFERENCES `Subject` (`guild_id`);

ALTER TABLE `Tmpc_join_channel` ADD FOREIGN KEY (`guild_id`) REFERENCES `Guild` (`guild_id`);

ALTER TABLE `Tmpc` ADD FOREIGN KEY (`guild_id`) REFERENCES `Guild` (`guild_id`);

ALTER TABLE `Token_message` ADD FOREIGN KEY (`tmpc_voice_channel`) REFERENCES `Tmpc` (`voice_channel`);
