DROP TABLE IF EXISTS roster;

CREATE TABLE roster (
    player_id   INTEGER NOT NULL UNIQUE,
    season      INTEGER NOT NULL,
    full_name  VARCHAR (50) NOT NULL,
    experience  VARCHAR (25) NOT NULL,
    position    VARCHAR (10) NOT NULL,
    height      INTEGER,
    weight      INTEGER,
    hometown    VARCHAR (50),
    high_school VARCHAR (50),
    CONSTRAINT roster_pk PRIMARY KEY (player_id, season)
);
                    