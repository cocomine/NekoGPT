create table ReplyAt
(
    Guild_ID     char(20)             not null,
    user         char(20)             not null,
    conversation char(36)             null,
    replying     tinyint(1) default 0 not null,
    primary key (Guild_ID, user),
    constraint ReplyAt_Guild_Guild_ID_fk
        foreign key (Guild_ID) references Guild (Guild_ID)
            on update cascade on delete cascade
)
    engine = InnoDB;

