# Tournament Planner

A basic PostgreSQL DB structure for a tournament planner application

## Requirements
- Python
- PostgreSQL DB 


## Run
To run first launch psql in your shell `$ psql` then you need to create a fresh database: 
```
CREATE DATABASE tournament;
```
Then connect to the database you just created using `=> \c tournament`
You can use the command \i tournament.sql to import the whole file into psql at once.

```
\i /path/to/file/tournament.sql

```
Then run `$ python tournament_test.py` and see all the test pass baby!




