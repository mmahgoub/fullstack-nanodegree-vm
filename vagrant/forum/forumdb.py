#
# Database access functions for the web forum.
#

import time
import psycopg2
import bleach

# Database connection
DB = []

# Get posts from database.


def GetAllPosts():
    '''Get all the posts from the database, sorted with the newest first.

    Returns:
      A list of dictionaries, where each dictionary has a 'content' key
      pointing to the post content, and 'time' key pointing to the time
      it was posted.
    '''
    posts = []
    connection = psycopg2.connect("dbname=forum")
    cursor = connection.cursor()
    cursor.execute('select time, content from posts order by time desc')
    posts = [{'content': str(row[1]), 'time': str(row[0])}
             for row in cursor.fetchall()]
    connection.close()

    #posts.sort(key=lambda row: row['time'], reverse=True)

    return posts

# Add a post to the database.


def AddPost(content):
    '''Add a new post to the database.

    Args:
      content: The text content of the new post.
    '''

    content = bleach.linkify(bleach.clean(content))

    #t = time.strftime('%c', time.localtime())
    connection = psycopg2.connect("dbname=forum")
    cursor = connection.cursor()
    cursor.execute("insert into posts values (%s)", (content,))
    connection.commit()
    connection.close()
