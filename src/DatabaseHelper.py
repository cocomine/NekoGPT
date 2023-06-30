import logging
import sqlite3


def database_helper(db: sqlite3.Connection, bot_name: str):
    cursor = db.cursor()

    try:
        cursor.execute("SELECT value FROM setting WHERE `key` = 'version'") # check database version sql
    except sqlite3.OperationalError:
        # Initialize database
        logging.info(f"{bot_name} Initializing database...")

        cursor.execute(
            "create table Guild(Guild_ID char(20) not null primary key, replyAt tinyint(1) default 1 not null)")
        cursor.execute(
            "create table DM(User char(20) not null primary key, conversation char(36) not null, replying tinyint(1) default 0 not null)")
        cursor.execute("""create table ReplyAt(
            Guild_ID     char(20)             not null,
            user         char(20)             not null,
            conversation char(36)             null,
            replying     tinyint(1) default 0 not null,
            primary key (Guild_ID, user),
            constraint ReplyAt_Guild_Guild_ID_fk
                foreign key (Guild_ID) references Guild (Guild_ID)
                    on update cascade on delete cascade
        )""")
        cursor.execute("""create table ReplyThis(
            Guild_ID     char(20)             not null,
            channel_ID   char(20)             not null,
            conversation char(36)             null,
            replying     tinyint(1) default 0 not null,
            primary key (Guild_ID, channel_ID),
            constraint ReplyThis_Guild_Guild_ID_fk
                foreign key (Guild_ID) references Guild (Guild_ID)
                    on update cascade on delete cascade
        )""")
        cursor.execute("CREATE TABLE `setting` (`key` TEXT NOT NULL, `value` TEXT NOT NULL, PRIMARY KEY(`key`))")
        cursor.execute("INSERT INTO setting (`key`, `value`) VALUES ('version', '0.1')")
        db.commit()

        logging.info(f"{bot_name} Database initialized.")

    # check database version
    version = cursor.fetchone()
    if version is not None:
        if version[0] == "0.1":
            logging.info(f"{bot_name} Database is up to date.")
            return

    # recheck update
    database_helper(db, bot_name)
