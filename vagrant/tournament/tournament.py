#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

from database_adapter import DB


def deleteMatches():
    """Remove all the match records from the database."""

    DB().execute("DELETE FROM matches", True)


def deletePlayers():
    """Remove all the player records from the database."""

    DB().execute("DELETE FROM players", True)


def countPlayers():
    """Returns the number of players currently registered."""

    conn = DB().execute("SELECT count(*) FROM players")
    cursor = conn['cursor'].fetchone()
    conn['conn'].close()
    return cursor[0]


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """

    db = DB()
    cur = db.cursor()
    query = cur.mogrify("INSERT INTO players (name) values (%s)", (name,))
    db.execute(query, True)


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """

    conn = DB().execute("select * from players_standings")
    cursor = conn['cursor'].fetchall()
    conn['conn'].close()
    return cursor


# I had to add a third argument to report which match is it!
def reportMatch(winner, loser, match_id):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """

    db = DB()
    cur = db.cursor()
    query = cur.mogrify("INSERT INTO matches (winner, loser) values (%s, %s)",
                        (winner, loser))
    db.execute(query, True)


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """

    conn = DB().execute("select * from next_round")
    cursor = conn['cursor'].fetchall()
    conn['conn'].close()
    return cursor
