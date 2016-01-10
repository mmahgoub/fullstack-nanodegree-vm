# Udacity Catalog

A products catalog developed using Python/Flask to demonstrate CRUD functionalities and social log in using Google and Facebook accounts.

## Features
- Search.
- Login with Google and Facebook.
- Atom RSS feeds for the recent posts `/recent.atom`.
- JSON endpoint for the whole catalog `/api/all.json`.
- Upload items pictures.
- Remove pictures from filesystem when deleting items.

## Requirements
- Python
- Flask

## Run
To run a fresh empty database you need to run:
```
$ python database_setup.py;
```
Then run the app using:
```
$ python project.py

```
Launch the app in the browser by goin to `http://localhost:5000`
