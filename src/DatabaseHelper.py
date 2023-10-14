import logging
import sqlite3


def database_helper(db: sqlite3.Connection, bot_name: str):
    """
    Check database version and update if needed.
    :param db: database connection
    :param bot_name: bot name
    """
    cursor = db.cursor()

    try:
        cursor.execute("SELECT value FROM setting WHERE `key` = 'version'") # check database version sql
    except sqlite3.OperationalError:
        # Initialize database
        logging.info(f"{bot_name} Initializing database...")

        cursor.execute(
            "create table Guild(Guild_ID char(20) not null primary key, replyAt tinyint(1) default 1 not null)")
        cursor.execute(
            "create table DM(User char(20) not null primary key, conversation char(36) not null)")
        cursor.execute("""create table ReplyAt(
            Guild_ID     char(20)             not null,
            user         char(20)             not null,
            conversation char(36)             null,
            primary key (Guild_ID, user),
            constraint ReplyAt_Guild_Guild_ID_fk
                foreign key (Guild_ID) references Guild (Guild_ID)
                    on update cascade on delete cascade
        )""")
        cursor.execute("""create table ReplyThis(
            Guild_ID     char(20)             not null,
            channel_ID   char(20)             not null,
            conversation char(36)             null,
            primary key (Guild_ID, channel_ID),
            constraint ReplyThis_Guild_Guild_ID_fk
                foreign key (Guild_ID) references Guild (Guild_ID)
                    on update cascade on delete cascade
        )""")
        cursor.execute("CREATE TABLE `setting` (`key` TEXT NOT NULL, `value` TEXT NOT NULL, PRIMARY KEY(`key`))")
        cursor.execute("INSERT INTO setting (`key`, `value`) VALUES ('version', '0.4')")
        db.commit()

        logging.info(f"{bot_name} Database initialized.")

    # check database version
    version = cursor.fetchone()
    if version is not None:
        if version[0] == "0.1":
            logging.info(f"{bot_name} Database is updating to v0.2...")
            update_0_2(db)
        if version[0] == "0.2":
            logging.info(f"{bot_name} Database is updating to v0.3...")
            update_0_3(db)
        if version[0] == "0.3":
            logging.info(f"{bot_name} Database is updating to v0.4...")
            update_0_4(db)
        if version[0] == "0.4":
            logging.info(f"{bot_name} Database is up to date.")
            return

    # recheck update
    database_helper(db, bot_name)


def update_0_2(db: sqlite3.Connection):
    """
    Update database from v0.1 to v0.2
    :param db: Database connection
    """
    cursor = db.cursor()

    cursor.execute("""create table ReplyAt_dg_tmp(
        Guild_ID     char(20) not null,
        user         char(20) not null,
        conversation char(36),
        primary key (Guild_ID, user),
        constraint ReplyAt_Guild_Guild_ID_fk
            foreign key (Guild_ID) references Guild (Guild_ID)
                on update cascade on delete cascade
    )""")
    cursor.execute("""insert into ReplyAt_dg_tmp(Guild_ID, user, conversation)
        select Guild_ID, user, conversation
        from ReplyAt
    """)
    cursor.execute("drop table ReplyAt;")
    cursor.execute("alter table ReplyAt_dg_tmp rename to ReplyAt")
    cursor.execute("update setting set value = '0.2' where `key` = 'version'")
    db.commit()


def update_0_3(db: sqlite3.Connection):
    """
    Update database from v0.2 to v0.3
    :param db: Database connection
    """
    cursor = db.cursor()

    cursor.execute("""create table ReplyThis_dg_tmp(
        Guild_ID     char(20) not null,
        channel_ID   char(20) not null,
        conversation char(36),
        primary key (Guild_ID, channel_ID),
        constraint ReplyThis_Guild_Guild_ID_fk
            foreign key (Guild_ID) references Guild (Guild_ID)
                on update cascade on delete cascade
    )""")
    cursor.execute("""insert into ReplyThis_dg_tmp(Guild_ID, channel_ID, conversation)
        select Guild_ID, channel_ID, conversation
        from ReplyThis;
    """)
    cursor.execute("drop table ReplyThis;")
    cursor.execute("alter table ReplyThis_dg_tmp rename to ReplyThis")
    cursor.execute("update setting set value = '0.3' where `key` = 'version'")
    db.commit()

def update_0_4(db: sqlite3.Connection):
    """
    Update database from v0.3 to v0.4
    :param db: Database connection
    """
    cursor = db.cursor()

    cursor.execute("""create table DM_dg_tmp(
        User         char(20) not null primary key,
        conversation char(36) not null
)""")
    cursor.execute("""insert into DM_dg_tmp(User, conversation)
        select User, conversation
        from DM""")
    cursor.execute("drop table DM")
    cursor.execute("alter table DM_dg_tmp rename to DM")
    cursor.execute("update setting set value = '0.4' where `key` = 'version'")
    db.commit()