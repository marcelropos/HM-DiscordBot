#[cfg(test)]
mod tests {
    use std::ops::Add;
    use std::sync::Once;
    use std::time::Duration;

    use poise::serenity_prelude::{ChannelId, GuildId, MessageId, RoleId, UserId};
    use serial_test::serial;
    use sqlx::{MySql, Pool};
    use sqlx::types::time::{Date, PrimitiveDateTime, Time};
    use time::Month;

    use crate::mysql_lib::*;

    static INIT: Once = Once::new();

    async fn get_connection_pool() -> Pool<MySql> {
        INIT.call_once(|| {
            env::init();
            tracing_subscriber::fmt::init();
        });
        let pool = get_connection(1)
            .await
            .expect("Database could not be connected to");
        migrate_database(&pool)
            .await
            .expect("Database migration could not be done");
        pool
    }

    async fn create_guild_in_database(pool: &Pool<MySql>) -> DatabaseGuild {
        let guild = DatabaseGuild {
            guild_id: GuildId::new(1),
            ghost_warning_deadline: 2,
            ghost_kick_deadline: 3,
            ghost_time_to_check: Time::from_hms(8, 0, 0).unwrap(),
            ghost_enabled: true,
            debug_channel: ChannelId::new(4),
            bot_channel: ChannelId::new(5),
            help_channel: ChannelId::new(6),
            study_group_category: ChannelId::new(7),
            subject_group_category: ChannelId::new(8),
            studenty_role: RoleId::new(9),
            tmp_studenty_role: Some(RoleId::new(18)),
            moderator_role: RoleId::new(10),
            newsletter_role: RoleId::new(11),
            nsfw_role: RoleId::new(12),
            study_role_separator_role: RoleId::new(13),
            subject_role_separator_role: RoleId::new(14),
            friend_role: RoleId::new(15),
            tmpc_keep_time: 12,
            alumni_role: RoleId::new(16),
            alumni_role_separator_role: RoleId::new(17),
            logger_pipe_channel: None,
        };
        let result = insert_guild(pool, guild)
            .await
            .expect("Query was not successful");
        assert!(result, "Could not insert into Database");
        guild
    }

    async fn delete_guild_test(pool: &Pool<MySql>, guild_id: GuildId) {
        let result = delete_guild(pool, guild_id)
            .await
            .expect("Query was not successful");
        assert!(result, "Guild could not be deleted");
    }

    #[tokio::test]
    #[serial]
    async fn update_guild_test() {
        let pool = get_connection_pool().await;
        let mut guild = create_guild_in_database(&pool).await;
        let result = is_guild_in_database(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert!(result, "Guild was not found in Database");
        let result = get_guild(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(guild, result, "Guild had not the information expected");
        guild = DatabaseGuild {
            guild_id: guild.guild_id,
            ghost_warning_deadline: guild.ghost_warning_deadline + 1,
            ghost_kick_deadline: guild.ghost_kick_deadline + 1,
            ghost_time_to_check: guild.ghost_time_to_check.add(Duration::from_secs(5)),
            ghost_enabled: !guild.ghost_enabled,
            debug_channel: ChannelId::new(guild.debug_channel.get() + 1),
            bot_channel: ChannelId::new(guild.bot_channel.get() + 1),
            help_channel: ChannelId::new(guild.help_channel.get() + 1),
            logger_pipe_channel: None,
            study_group_category: ChannelId::new(guild.study_group_category.get() + 1),
            subject_group_category: ChannelId::new(guild.subject_group_category.get() + 1),
            studenty_role: RoleId::new(guild.studenty_role.get() + 1),
            tmp_studenty_role: Some(RoleId::new(42)),
            moderator_role: RoleId::new(guild.moderator_role.get() + 1),
            newsletter_role: RoleId::new(guild.newsletter_role.get() + 1),
            nsfw_role: RoleId::new(guild.nsfw_role.get() + 1),
            study_role_separator_role: RoleId::new(guild.study_role_separator_role.get() + 1),
            subject_role_separator_role: RoleId::new(guild.subject_role_separator_role.get() + 1),
            friend_role: RoleId::new(guild.friend_role.get() + 1),
            tmpc_keep_time: guild.tmpc_keep_time + 5,
            alumni_role: RoleId::new(guild.alumni_role.get() + 1),
            alumni_role_separator_role: RoleId::new(guild.alumni_role_separator_role.get() + 1),
        };
        let result =
            update_guild(&pool, guild)
                .await
                .expect("Query was not successful");
        assert!(result, "Guild couldn't be updated");
        let result = get_guild(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(guild, result, "Guild had not the information expected");
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_guild_methods() {
        let pool = get_connection_pool().await;
        let mut guild = create_guild_in_database(&pool).await;
        let result = is_guild_in_database(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert!(result, "Guild was not found in Database");
        let result = get_guild(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(guild, result, "Guild had not the information expected");
        guild = DatabaseGuild {
            guild_id: guild.guild_id,
            ghost_warning_deadline: guild.ghost_warning_deadline + 1,
            ghost_kick_deadline: guild.ghost_kick_deadline + 1,
            ghost_time_to_check: guild.ghost_time_to_check.add(Duration::from_secs(5)),
            ghost_enabled: !guild.ghost_enabled,
            debug_channel: ChannelId::new(guild.debug_channel.get() + 1),
            bot_channel: ChannelId::new(guild.bot_channel.get() + 1),
            help_channel: ChannelId::new(guild.help_channel.get() + 1),
            logger_pipe_channel: Some(ChannelId::new(7)),
            study_group_category: ChannelId::new(guild.study_group_category.get() + 1),
            subject_group_category: ChannelId::new(guild.subject_group_category.get() + 1),
            studenty_role: RoleId::new(guild.studenty_role.get() + 1),
            tmp_studenty_role: Some(RoleId::new(42)),
            moderator_role: RoleId::new(guild.moderator_role.get() + 1),
            newsletter_role: RoleId::new(guild.newsletter_role.get() + 1),
            nsfw_role: RoleId::new(guild.nsfw_role.get() + 1),
            study_role_separator_role: RoleId::new(guild.study_role_separator_role.get() + 1),
            subject_role_separator_role: RoleId::new(guild.subject_role_separator_role.get() + 1),
            friend_role: RoleId::new(guild.friend_role.get() + 1),
            tmpc_keep_time: guild.tmpc_keep_time + 5,
            alumni_role: RoleId::new(guild.alumni_role.get() + 1),
            alumni_role_separator_role: RoleId::new(guild.alumni_role_separator_role.get() + 1),
        };
        let result =
            update_ghost_warning_deadline(&pool, guild.guild_id, guild.ghost_warning_deadline)
                .await
                .expect("Query was not successful");
        assert!(result, "Ghost warning deadline couldn't be updated");
        let result = update_ghost_kick_deadline(&pool, guild.guild_id, guild.ghost_kick_deadline)
            .await
            .expect("Query was not successful");
        assert!(result, "Ghost kick deadline couldn't be updated");
        let result = update_ghost_time_to_check(&pool, guild.guild_id, guild.ghost_time_to_check)
            .await
            .expect("Query was not successful");
        assert!(result, "Ghost Time to check couldn't be updated");
        let result = update_ghost_enabled(&pool, guild.guild_id, guild.ghost_enabled)
            .await
            .expect("Query was not successful");
        assert!(result, "Ghost enabled flag couldn't be updated");
        let result = update_debug_channel(&pool, guild.guild_id, guild.debug_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Debug channel couldn't be updated");
        let result = update_bot_channel(&pool, guild.guild_id, guild.bot_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Bot channel couldn't be updated");
        let result = update_help_channel(&pool, guild.guild_id, guild.help_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Help channel couldn't be updated");
        let result = update_logger_pipe_channel(&pool, guild.guild_id, guild.logger_pipe_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Logger pipe channel couldn't be updated");
        let result = update_study_group_category(&pool, guild.guild_id, guild.study_group_category)
            .await
            .expect("Query was not successful");
        assert!(result, "Study group category couldn't be updated");
        let result =
            update_subject_group_category(&pool, guild.guild_id, guild.subject_group_category)
                .await
                .expect("Query was not successful");
        assert!(result, "Subject group category couldn't be updated");
        let result = update_studenty_role(&pool, guild.guild_id, guild.studenty_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Studenty role deadline couldn't be updated");
        let result = update_tmp_studenty_role(&pool, guild.guild_id, guild.tmp_studenty_role)
            .await
            .expect("Query was not successful");
        assert!(result, "tmp studenty role couldn't be updated");
        let result = update_moderator_role(&pool, guild.guild_id, guild.moderator_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Moderator role couldn't be updated");
        let result = update_newsletter_role(&pool, guild.guild_id, guild.newsletter_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Newsletter role couldn't be updated");
        let result = update_nsfw_role(&pool, guild.guild_id, guild.nsfw_role)
            .await
            .expect("Query was not successful");
        assert!(result, "nsfw role couldn't be updated");
        let result = update_study_role_separator_role(
            &pool,
            guild.guild_id,
            guild.study_role_separator_role,
        )
        .await
        .expect("Query was not successful");
        assert!(result, "Study role separator role couldn't be updated");
        let result = update_subject_role_separator_role(
            &pool,
            guild.guild_id,
            guild.subject_role_separator_role,
        )
        .await
        .expect("Query was not successful");
        assert!(result, "Subject role separator role couldn't be updated");
        let result = update_friend_role(&pool, guild.guild_id, guild.friend_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Friend role couldn't be updated");
        let result = update_tmpc_keep_time(&pool, guild.guild_id, guild.tmpc_keep_time)
            .await
            .expect("Query was not successful");
        assert!(result, "tmpc keep time couldn't be updated");
        let result = update_alumni_role(&pool, guild.guild_id, guild.alumni_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Alumni role couldn't be updated");
        let result = update_alumni_role_separator_role(
            &pool,
            guild.guild_id,
            guild.alumni_role_separator_role,
        )
        .await
        .expect("Query was not successful");
        assert!(result, "Alumni role separator role couldn't be updated");
        let result = get_guild(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(guild, result, "Guild had not the information expected");
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_alumni_role_methods() {
        let pool = get_connection_pool().await;
        let guild = create_guild_in_database(&pool).await;
        let alumni_role = DatabaseAlumniRole {
            role: RoleId::new(5),
            guild_id: guild.guild_id,
        };
        let result = insert_alumni_role(&pool, alumni_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Alumni role couldn't be inserted");
        let alumni_role = DatabaseAlumniRole {
            role: RoleId::new(6),
            guild_id: guild.guild_id,
        };
        let result = insert_alumni_role(&pool, alumni_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Second Alumni role couldn't be inserted");
        let result = get_alumni_roles(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 2, "Don't have 2 alumni roles in Database");
        assert!(
            result.contains(&alumni_role),
            "Wanted Alumni Role is not part of the Vector"
        );
        let result = delete_alumni_role(&pool, alumni_role)
            .await
            .expect("Query was not successful");
        assert!(result, "Alumni role couldn't get deleted");

        // this also tests if a guild can be deleted while there is information linked with it as intended
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_study_group_methods() {
        let pool = get_connection_pool().await;
        let guild = create_guild_in_database(&pool).await;
        let mut study_group = DatabaseStudyGroup {
            id: None,
            guild_id: guild.guild_id,
            name: "IF".to_string(),
            color: 0xFF00AB,
            active: true,
        };
        let result = insert_study_group(&pool, study_group.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Study group couldn't be inserted");
        let mut study_group2 = DatabaseStudyGroup {
            id: None,
            guild_id: guild.guild_id,
            name: "IB".to_string(),
            color: 0xFF00AB,
            active: true,
        };
        let result = insert_study_group(&pool, study_group2.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Second Study group couldn't be inserted");
        let result = get_study_groups(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 2, "Don't have 2 Study groups in Database");
        study_group.id = result
            .iter()
            .find(|t| t.name == study_group.name)
            .map(|t| t.id)
            .unwrap_or(None);
        assert!(
            result.contains(&study_group),
            "Wanted Study Group is not part of the Vector"
        );
        study_group2.id = result
            .iter()
            .find(|t| t.name == study_group2.name)
            .map(|t| t.id)
            .unwrap_or(None);
        assert!(
            result.contains(&study_group2),
            "Wanted Study Group is not part of the Vector"
        );
        study_group.name = "DC".to_string();
        study_group.color = 0x00F00;
        study_group.active = !study_group.active;
        let result = update_study_group(&pool, study_group.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Study group couldn't be updated");
        let result = get_study_groups(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 2, "Don't have 2 Study groups in Database");
        assert!(
            result.contains(&study_group),
            "Wanted Study Group is not part of the Vector"
        );

        // Semester Study Group

        let semester_study_group = DatabaseSemesterStudyGroup {
            role: RoleId::new(1),
            study_group_id: study_group.id.unwrap(),
            semester: 1,
            text_channel: ChannelId::new(2),
        };
        let result = insert_semester_study_group(&pool, semester_study_group)
            .await
            .expect("Query was not successful");
        assert!(result, "Semester Study role couldn't get inserted");
        let semester_study_group = DatabaseSemesterStudyGroup {
            role: RoleId::new(2),
            study_group_id: study_group2.id.unwrap(),
            semester: 1,
            text_channel: ChannelId::new(3),
        };
        let result = insert_semester_study_group(&pool, semester_study_group)
            .await
            .expect("Query was not successful");
        assert!(result, "Second Semester Study role couldn't get inserted");
        let result = get_semester_study_groups_in_guild(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 2, "Don't have 2 Study groups in Database");
        assert!(
            result.contains(&semester_study_group),
            "Study group is not in Vector"
        );
        let result = get_semester_study_groups_in_study_group(&pool, study_group.id.unwrap())
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 1, "Don't have 1 Study groups in Database");
        assert!(
            !result.contains(&semester_study_group),
            "Study group is in Vector"
        );
        let result = get_semester_study_groups_in_study_group(&pool, study_group2.id.unwrap())
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 1, "Don't have 1 Study groups in Database");
        assert!(
            result.contains(&semester_study_group),
            "Study group is not in Vector"
        );

        let result = delete_semester_study_group(&pool, semester_study_group)
            .await
            .expect("Query was not successful");
        assert!(result, "Semester Study Group couldn't get deleted");

        // clean up

        let result = delete_study_group(&pool, study_group2)
            .await
            .expect("Query was not successful");
        assert!(result, "Study Group couldn't get deleted");

        // this also tests if a guild can be deleted while there is information linked with it as intended
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_subject_methods() {
        let pool = get_connection_pool().await;
        let guild = create_guild_in_database(&pool).await;
        let subject = DatabaseSubject {
            role: RoleId::new(5),
            guild_id: guild.guild_id,
            name: "SE1".to_string(),
            text_channel: ChannelId::new(4),
        };
        let result = insert_subject(&pool, subject.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Subject couldn't be inserted");
        let subject2 = DatabaseSubject {
            role: RoleId::new(6),
            guild_id: guild.guild_id,
            name: "SE2".to_string(),
            text_channel: ChannelId::new(5),
        };
        let result = insert_subject(&pool, subject2.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Second Subject couldn't be inserted");
        let result = get_subjects(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 2, "Don't have 2 Subjects in Database");
        assert!(
            result.contains(&subject),
            "Wanted Subject is not part of the Vector"
        );
        assert!(
            result.contains(&subject2),
            "Wanted Subject is not part of the Vector"
        );

        let result = delete_subject(&pool, subject)
            .await
            .expect("Query was not successful");
        assert!(result, "Study Group couldn't get deleted");

        // this also tests if a guild can be deleted while there is information linked with it as intended
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_study_subject_link_methods() {
        let pool = get_connection_pool().await;
        let guild = create_guild_in_database(&pool).await;
        let subject = DatabaseSubject {
            role: RoleId::new(5),
            guild_id: guild.guild_id,
            name: "SE1".to_string(),
            text_channel: ChannelId::new(4),
        };
        let result = insert_subject(&pool, subject.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Subject couldn't be inserted");
        let mut study_group = DatabaseStudyGroup {
            id: None,
            guild_id: guild.guild_id,
            name: "IF".to_string(),
            color: 0xFF00AB,
            active: true,
        };
        let result = insert_study_group(&pool, study_group.clone())
            .await
            .expect("Query was not successful");
        assert!(result, "Study group couldn't be inserted");
        let result = get_study_groups(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 1, "Don't have 1 Study groups in Database");
        study_group.id = result
            .iter()
            .find(|t| t.name == study_group.name)
            .map(|t| t.id)
            .unwrap_or(None);

        let semester_study_group = DatabaseSemesterStudyGroup {
            role: RoleId::new(1),
            study_group_id: study_group.id.unwrap(),
            semester: 1,
            text_channel: ChannelId::new(2),
        };
        let result = insert_semester_study_group(&pool, semester_study_group)
            .await
            .expect("Query was not successful");
        assert!(result, "Semester Study role couldn't get inserted");

        let study_subject_link = DatabaseStudySubjectLink {
            study_group_role: semester_study_group.role,
            subject_role: subject.role,
            guild_id: guild.guild_id,
        };
        let result = insert_study_subject_link(&pool, study_subject_link)
            .await
            .expect("Query was not successful");
        assert!(result, "Study-Subject Link couldn't get inserted");
        let result = get_study_subject_links_in_guild(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(
            result.len(),
            1,
            "Don't have 1 Study-Subject Link in Database"
        );
        assert!(
            result.contains(&study_subject_link),
            "Wanted Study-Subject Link is not part of the Vector"
        );
        let result = get_study_subject_links_for_subject(&pool, subject.role)
            .await
            .expect("Query was not successful");
        assert_eq!(
            result.len(),
            1,
            "Don't have 1 Study-Subject Link in Database"
        );
        assert!(
            result.contains(&study_subject_link),
            "Wanted Study-Subject Link is not part of the Vector"
        );
        let result = get_study_subject_links_for_study_group(&pool, semester_study_group.role)
            .await
            .expect("Query was not successful");
        assert_eq!(
            result.len(),
            1,
            "Don't have 1 Study-Subject Link in Database"
        );
        assert!(
            result.contains(&study_subject_link),
            "Wanted Study-Subject Link is not part of the Vector"
        );
        let result = delete_study_subject_link(&pool, study_subject_link)
            .await
            .expect("Query was not successful");
        assert!(result, "Study-Subject Link couldn't get deleted");

        // this also tests if a guild can be deleted while there is information linked with it as intended
        let result = insert_study_subject_link(&pool, study_subject_link)
            .await
            .expect("Query was not successful");
        assert!(result, "Study-Subject Link couldn't get inserted");
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_tmpc_join_channel_methods() {
        let pool = get_connection_pool().await;
        let guild = create_guild_in_database(&pool).await;
        let mut tmpc_join_channel = DatabaseTmpcJoinChannel {
            voice_channel: ChannelId::new(2),
            guild_id: guild.guild_id,
            persist: false,
        };
        let result = insert_tmpc_join_channel(&pool, tmpc_join_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc Join Channel couldn't be inserted");
        let result = get_tmpc_join_channel(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(
            result.len(),
            1,
            "Don't have 1 Tmpc Join Channel in Database"
        );
        assert!(
            result.contains(&tmpc_join_channel),
            "Wanted Tmpc Join Channel is not part of the Vector"
        );
        tmpc_join_channel.persist = !tmpc_join_channel.persist;
        let result = update_tmpc_join_channel_persist(&pool, tmpc_join_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc Join Channel couldn't be updated");
        let result = get_tmpc_join_channel(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(
            result.len(),
            1,
            "Don't have 1 Tmpc Join Channel in Database"
        );
        assert!(
            result.contains(&tmpc_join_channel),
            "Wanted Tmpc Join Channel is not part of the Vector"
        );

        let result = delete_tmpc_join_channel(&pool, tmpc_join_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc Join Channel couldn't get deleted");

        // this also tests if a guild can be deleted while there is information linked with it as intended
        let result = insert_tmpc_join_channel(&pool, tmpc_join_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc Join Channel couldn't be inserted");
        delete_guild_test(&pool, guild.guild_id).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_tmpc_methods() {
        let pool = get_connection_pool().await;
        let guild = create_guild_in_database(&pool).await;
        let mut tmpc = DatabaseTmpc {
            voice_channel: ChannelId::new(2),
            text_channel: ChannelId::new(3),
            guild_id: guild.guild_id,
            owner: UserId::new(4),
            persist: false,
            token: 0,
            keep: false,
            delete_at: None,
        };
        let result = insert_tmpc(&pool, tmpc)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc couldn't be inserted");
        let result = get_tmpc(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 1, "Don't have 1 Tmpc in Database");
        assert!(
            result.contains(&tmpc),
            "Wanted Tmpc is not part of the Vector"
        );
        tmpc.delete_at = Some(PrimitiveDateTime::new(
            Date::from_calendar_date(2023, Month::December, 1).unwrap(),
            Time::from_hms(12, 0, 0).unwrap(),
        ));
        tmpc.token = 42;
        tmpc.keep = !tmpc.keep;
        let result = update_tmpc_delete_at(&pool, tmpc)
            .await
            .expect("Query was not successful");
        assert!(result, "deleteAt couldn't be modified");
        let result = update_tmpc_token(&pool, tmpc)
            .await
            .expect("Query was not successful");
        assert!(result, "token couldn't be modified");
        let result = update_tmpc_keep(&pool, tmpc)
            .await
            .expect("Query was not successful");
        assert!(result, "keep value couldn't be modified");
        let result = get_tmpc(&pool, guild.guild_id)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 1, "Don't have 1 Tmpc in Database");
        assert!(
            result.contains(&tmpc),
            "Wanted Tmpc is not part of the Vector"
        );

        let token_message = DatabaseTokenMessage {
            tmpc_voice_channel: tmpc.voice_channel,
            message: MessageId::new(4),
            message_channel: ChannelId::new(1),
        };
        let result = insert_token_message(&pool, token_message)
            .await
            .expect("Query was not successful");
        assert!(result, "Token Message couldn't be inserted");
        let result = get_token_messages(&pool, tmpc.voice_channel)
            .await
            .expect("Query was not successful");
        assert_eq!(result.len(), 1, "Don't have 1 Token Message in Database");
        assert!(
            result.contains(&token_message),
            "Wanted Token Message is not part of the Vector"
        );
        let result = delete_token_message(&pool, token_message)
            .await
            .expect("Query was not successful");
        assert!(result, "Token Message couldn't get deleted");
        let result = insert_token_message(&pool, token_message)
            .await
            .expect("Query was not successful");
        assert!(result, "Token Message couldn't be inserted");
        let result = delete_all_token_messages(&pool, tmpc.voice_channel)
            .await
            .expect("Query was not successful");
        assert!(result, "Token Message couldn't get deleted");

        let result = insert_token_message(&pool, token_message)
            .await
            .expect("Query was not successful");
        assert!(result, "Token Message couldn't be inserted");
        let result = delete_tmpc(&pool, tmpc)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc couldn't get deleted");

        // this also tests if a guild can be deleted while there is information linked with it as intended
        let result = insert_tmpc(&pool, tmpc)
            .await
            .expect("Query was not successful");
        assert!(result, "Tmpc Join Channel couldn't be inserted");
        delete_guild_test(&pool, guild.guild_id).await;
    }
}
