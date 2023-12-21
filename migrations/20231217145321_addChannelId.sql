alter table Token_message
    drop primary key,
    add message_channel bigint unsigned not null,
    add primary key (tmpc_voice_channel, message, message_channel);
