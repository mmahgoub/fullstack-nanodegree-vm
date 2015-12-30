-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

--====--====--====--====--====--====--====--====--====--====--====--====--====

-- Drop statements to insure clean run

DROP VIEW IF EXISTS next_round;

DROP VIEW IF EXISTS losers_pairs;

DROP VIEW IF EXISTS winners_pairs;

DROP VIEW IF EXISTS bottom_losers;

DROP VIEW IF EXISTS top_losers;

DROP VIEW IF EXISTS losers_count;

DROP VIEW IF EXISTS losers;

DROP VIEW IF EXISTS bottom_winners;

DROP VIEW IF EXISTS top_winners;

DROP VIEW IF EXISTS winners_count;

DROP VIEW IF EXISTS winners;

DROP VIEW IF EXISTS players_standings;

DROP TABLE IF EXISTS players;

DROP TABLE IF EXISTS matches;

-- Create players table

CREATE TABLE players (
	id serial PRIMARY KEY,
	name varchar(255)
);

-- Create matches table

CREATE TABLE matches (
	id serial PRIMARY KEY,
	tournament_id integer,
	winner integer NOT NULL,
	loser integer NOT NULL
);


-- View to display all players standings

CREATE VIEW players_standings as (
	select 
		players.id as id, 
		players.name as name, 
		COALESCE(count(w.winner), 0) as wins, 
		count(w.winner) + count(l.loser) as matches 
	from players 
	left join matches as w on players.id = w.winner 
	left join matches as l on players.id = l.loser 
	group by players.id
	order by wins
);


-- View to display only winners

CREATE VIEW winners as (
	select  
		id, 
		name 
	from players_standings
	order by wins desc
	limit (select count(*)/2 from players)
);


-- View to report winners count

CREATE VIEW winners_count as (
	select  
		count(id) as count
	from winners
);


-- View to display top winners

CREATE VIEW top_winners as (
	select  
		id,
		name
	from winners
	limit (select count/2 from winners_count)
);


-- View to display winners at the bottom of the list

CREATE VIEW bottom_winners as (
	select  
		id,
		name 
	from winners
	where id not in (select id from top_winners)
);


-- View to display losers list

CREATE VIEW losers as (
	select  
		id, 
		name 
	from players_standings
	order by wins asc
	limit (select count(*)/2 from players)
);


-- View to report losers count

CREATE VIEW losers_count as (
	select  
		count(id) as count
	from losers
);


-- View to display winners at the top of the list

CREATE VIEW top_losers as (
	select  
		id,
		name
	from losers
	limit (select count/2 from losers_count)
);


-- View to display losers at the bottom of the list

CREATE VIEW bottom_losers as (
	select  
		id,
		name 
	from losers
	where id not in (select id from top_losers)
);


-- View to display winners pairs

CREATE VIEW winners_pairs as (
	select  
		top_winners.id as id1,
		top_winners.name as name1,
		bottom_winners.id as id2,
		bottom_winners.name as name2
	from top_winners
	left join bottom_winners on top_winners.id <> bottom_winners.id
);


-- View to display losers pairs

CREATE VIEW losers_pairs as (
	select  
		top_losers.id as id1,
		top_losers.name as name1,
		bottom_losers.id as id2,
		bottom_losers.name as name2
	from top_losers
	left join bottom_losers on top_losers.id <> bottom_losers.id
);


-- NEXT ROUND IS ON!!

CREATE VIEW next_round as (
	select
	 *
	from winners_pairs
	union
	select
	 *
	from losers_pairs
);
