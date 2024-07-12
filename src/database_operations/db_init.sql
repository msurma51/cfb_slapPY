DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS roster;

CREATE TABLE teams (
    team_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    team_name VARCHAR (100) NOT NULL,
    nickname VARCHAR (50) NOT NULL,
    city VARCHAR (50) NOT NULL,
    state VARCHAR (2) NOT NULL,
    conference VARCHAR (50),
    region INTEGER,
    division INTEGER,
    official_url VARCHAR (250),
    d3_url VARCHAR (250),
    stadium_name VARCHAR (100),
    stadium_capacity INTEGER,
    surface VARCHAR (10),
    enrollment INTEGER,
    color_1 VARCHAR (20),
    color_2 VARCHAR (20),
    color_3 VARCHAR (20),
    coach_name VARCHAR (100),
    coach_alma_mater VARCHAR (100)
);

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
                    