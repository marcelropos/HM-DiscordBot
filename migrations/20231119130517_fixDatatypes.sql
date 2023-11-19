START TRANSACTION;

alter table Alumni_roles
    drop foreign key Alumni_roles_ibfk_1;
alter table Study_groups
    drop foreign key Study_groups_ibfk_1;
alter table Subject
    drop foreign key Subject_ibfk_1;
alter table Tmpc
    drop foreign key Tmpc_ibfk_1;
alter table Tmpc_join_channel
    drop foreign key Tmpc_join_channel_ibfk_1;
alter table Token_message
    drop foreign key Token_message_ibfk_1;
alter table Study_subject_link
    drop foreign key Study_subject_link_ibfk_1,
    drop foreign key Study_subject_link_ibfk_2,
    drop foreign key Study_subject_link_ibfk_3;

alter table Guild
    modify guild_id BIGINT UNSIGNED not null,
    modify ghost_warn_deadline INT UNSIGNED not null,
    modify ghost_kick_deadline INT UNSIGNED not null,
    modify debug_channel BIGINT UNSIGNED not null,
    modify bot_channel BIGINT UNSIGNED not null,
    modify help_channel BIGINT UNSIGNED not null,
    modify logger_pipe_channel BIGINT UNSIGNED null,
    modify study_group_category BIGINT UNSIGNED not null,
    modify subject_group_category BIGINT UNSIGNED not null,
    modify studenty_role BIGINT UNSIGNED not null,
    modify tmp_studenty_role BIGINT UNSIGNED null,
    modify moderator_role BIGINT UNSIGNED not null,
    modify newsletter_role BIGINT UNSIGNED not null,
    modify nsfw_role BIGINT UNSIGNED not null,
    modify study_role_separator_role BIGINT UNSIGNED not null,
    modify subject_role_separator_role BIGINT UNSIGNED not null,
    modify friend_role BIGINT UNSIGNED not null,
    modify alumni_role BIGINT UNSIGNED not null,
    modify alumni_role_separator_role BIGINT UNSIGNED not null;

alter table Alumni_roles
    modify role BIGINT UNSIGNED not null,
    modify guild_id BIGINT UNSIGNED not null,
    add constraint Alumni_roles_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Semester_study_groups
    modify role BIGINT UNSIGNED not null,
    modify text_channel BIGINT UNSIGNED not null;

alter table Study_groups
    modify guild_id BIGINT UNSIGNED not null,
    add constraint Study_groups_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Subject
    modify guild_id BIGINT UNSIGNED not null,
    modify role BIGINT UNSIGNED not null,
    modify text_channel BIGINT UNSIGNED not null,
    add constraint Subject_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Study_subject_link
    modify guild_id BIGINT UNSIGNED not null,
    modify study_group_role BIGINT UNSIGNED not null,
    modify subject_role BIGINT UNSIGNED not null,
    add constraint Study_subject_link_ibfk_1
        foreign key (study_group_role) references Semester_study_groups (role)
            on update cascade on delete cascade,
    add constraint Study_subject_link_ibfk_2
        foreign key (subject_role) references Subject (role)
            on update cascade on delete cascade,
    add constraint Study_subject_link_ibfk_3
        foreign key (guild_id) references Subject (guild_id)
            on delete cascade;

alter table Tmpc
    modify voice_channel BIGINT UNSIGNED not null,
    modify text_channel BIGINT UNSIGNED not null,
    modify guild_id BIGINT UNSIGNED not null,
    modify owner BIGINT UNSIGNED not null,
    add constraint Tmpc_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Tmpc_join_channel
    modify voice_channel BIGINT UNSIGNED not null,
    modify guild_id BIGINT UNSIGNED not null,
    add constraint Tmpc_join_channel_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Token_message
    modify tmpc_voice_channel BIGINT UNSIGNED not null,
    modify message BIGINT UNSIGNED not null,
    add constraint Token_message_ibfk_1
        foreign key (tmpc_voice_channel) references Tmpc (voice_channel)
            on delete cascade;

ROLLBACK;