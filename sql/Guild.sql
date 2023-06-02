create table Guild
(
    Guild_ID char(20)             not null
        primary key,
    replyAt  tinyint(1) default 1 not null
)
    engine = InnoDB;

