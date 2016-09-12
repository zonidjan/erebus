DROP TABLE IF EXISTS trivia_questions;
CREATE TABLE trivia_questions (
	qid int unsigned not null auto_increment,
	question varchar(300) not null,
	answer varchar(300) not null,
	deleted bool not null default 0,
	addtime timestamp not null default CURRENT_TIMESTAMP,
	modtime timestamp not null,
	timesasked int unsigned not null,
	asktime timestamp not null on update CURRENT_TIMESTAMP,
	author int unsigned not null,
	primary key (qid)
);
-- count = SELECT COUNT(questions) FROM questions
-- index = random (0,count]
-- while row_is_empty:
--     row = SELECT question, answer FROM questions WHERE qid = index AND deleted = 0

DROP TABLE IF EXISTS trivia_channels;
CREATE TABLE trivia_channels (
	channel varchar(100) not null,
	isteam bool default 0,
	primary key (channel)
);

DROP TABLE IF EXISTS trivia_games;
CREATE TABLE trivia_games (
	gid int unsigned not null auto_increment,
	startdate timestamp not null default CURRENT_TIMESTAMP,
	enddate timestamp not null,
	channel int unsigned not null,
	maxscore int unsigned not null,
	active bool not null default 1,
	primary key (gid)
);

DROP TABLE IF EXISTS trivia_scores;
CREATE TABLE trivia_scores (
	gid int unsigned not null,
	pid int unsigned not null,
	score int unsigned,
	primary key (gid, pid)
);

DROP TABLE IF EXISTS trivia_players;
CREATE TABLE trivia_players (
	pid int unsigned not null auto_increment,
	nick varchar(30) not null,
	password char(70),
	salt varchar(10),
	auth varchar(30) not null,
	wins int unsigned not null,
	podiums int unsigned not null,
	highstreak int unsigned not null,
	primary key (pid),
	unique key (nick)
);

DROP TABLE IF EXISTS trivia_teams;
CREATE TABLE trivia_teams (
	tid int unsigned not null auto_increment,
	teamname varchar(20) not null,
	channel int unsigned not null,
	primary key (tid)
);

DROP TABLE IF EXISTS trivia_team_players;
CREATE TABLE trivia_team_players (
	tid int unsigned not null,
	pid int unsigned not null,
	captain bool not null,
	primary key (tid, pid)
);
