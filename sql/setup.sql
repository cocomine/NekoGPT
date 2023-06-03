create table if not exists DM
(
    User         char(20)             not null primary key,
    conversation char(36)             not null,
    replying     tinyint(1) default 0 not null
) engine = InnoDB;

create table if not exists Guild
(
    Guild_ID char(20)             not null primary key,
    replyAt  tinyint(1) default 1 not null
) engine = InnoDB;

create table if not exists ReplyAt
(
    Guild_ID     char(20)             not null,
    user         char(20)             not null,
    conversation char(36)             null,
    replying     tinyint(1) default 0 not null,
    primary key (Guild_ID, user),
    constraint ReplyAt_Guild_Guild_ID_fk
        foreign key (Guild_ID) references Guild (Guild_ID)
            on update cascade on delete cascade
) engine = InnoDB;

create table if not exists ReplyThis
(
    Guild_ID     char(20)             not null,
    channel_ID   char(20)             not null,
    conversation char(36)             null,
    replying     tinyint(1) default 0 not null,
    primary key (Guild_ID, channel_ID),
    constraint ReplyThis_Guild_Guild_ID_fk
        foreign key (Guild_ID) references Guild (Guild_ID)
            on update cascade on delete cascade
) engine = InnoDB;