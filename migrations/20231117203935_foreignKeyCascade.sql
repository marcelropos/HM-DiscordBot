alter table Alumni_roles
    drop foreign key Alumni_roles_ibfk_1;

alter table Alumni_roles
    add constraint Alumni_roles_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Study_groups
    drop foreign key Study_groups_ibfk_1;

alter table Study_groups
    add constraint Study_groups_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Subject
    drop foreign key Subject_ibfk_1;

alter table Subject
    add constraint Subject_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Tmpc
    drop foreign key Tmpc_ibfk_1;

alter table Tmpc
    add constraint Tmpc_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Tmpc_join_channel
    drop foreign key Tmpc_join_channel_ibfk_1;

alter table Tmpc_join_channel
    add constraint Tmpc_join_channel_ibfk_1
        foreign key (guild_id) references Guild (guild_id)
            on delete cascade;

alter table Token_message
    drop foreign key Token_message_ibfk_1;

alter table Token_message
    add constraint Token_message_ibfk_1
        foreign key (tmpc_voice_channel) references Tmpc (voice_channel)
            on delete cascade;

alter table Semester_study_groups
    drop foreign key Semester_study_groups_ibfk_1;

alter table Semester_study_groups
    add constraint Semester_study_groups_ibfk_1
        foreign key (study_group_id) references Study_groups (id)
            on delete cascade;

alter table Study_subject_link
    drop foreign key Study_subject_link_ibfk_1;

alter table Study_subject_link
    add constraint Study_subject_link_ibfk_1
        foreign key (study_group_role) references Semester_study_groups (role)
            on update cascade on delete cascade;

alter table Study_subject_link
    drop foreign key Study_subject_link_ibfk_2;

alter table Study_subject_link
    add constraint Study_subject_link_ibfk_2
        foreign key (subject_role) references Subject (role)
            on update cascade on delete cascade;

alter table Study_subject_link
    drop foreign key Study_subject_link_ibfk_3;

alter table Study_subject_link
    add constraint Study_subject_link_ibfk_3
        foreign key (guild_id) references Subject (guild_id)
            on delete cascade;