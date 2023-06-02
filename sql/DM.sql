create table DM
(
    User         char(20)             not null
        primary key,
    conversation char(36)             not null,
    replying     tinyint(1) default 0 not null
)
    engine = InnoDB;

