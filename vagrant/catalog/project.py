import os
import datetime
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from werkzeug import secure_filename

app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Initiate login state with the first request


@app.before_first_request
def state():
    login_session['state'] = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))


# There is no place like home!
@app.route('/')
def index():
    items = session.query(Item).order_by(Item.name.asc())
    return render_template('index.html', items=items, title="Home", categories_menu=categories_menu())

# JSON endpoint for the whole catalog grouped by category!


@app.route('/api/all.json')
def api_all():
    categories = session.query(Category).all()
    cats = []
    for c in categories:
        items = session.query(Item).filter_by(category_id=c.id).all()
        itms = []
        for i in items:
            itms.append({
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'price': i.price,
                'picture': make_external(url_for('static', filename='img/' + i.picture))
            })
        cats.append({'Category': {
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'Items': itms,
        }})
    response = make_response(json.dumps(cats), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


# View items which belongs to a certain category


@app.route('/categories/view/<int:id>')
def category_view(id):
    category = session.query(Category).filter_by(id=id).one()
    items = session.query(Item).filter_by(
        category_id=id).order_by(Item.name.asc())
    return render_template('category_view.html', category=category, items=items, categories_menu=categories_menu())

# Edit category form


@app.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
def category_edit(id):
    category = session.query(Category).filter_by(id=id).one()
    # Check to see if user is logged in and if this is his/her own record
    if 'username' not in login_session or getUserID(login_session.get('email')) != category.user_id:
        flash("You are not authorized to access that location")
        return redirect(request.referrer)
    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            category.description = request.form['description']
            session.commit()
            flash('Category saved! %s' % category.name)
            return redirect(url_for('category_new'))
    else:
        return render_template('category_edit.html', title="Edit: " + category.name, category=category, categories_menu=categories_menu(True))

# A page to manage and add new categories


@app.route('/categories/manage', methods=['GET', 'POST'])
def category_new():
    # Check to see if user is logged
    if 'username' not in login_session:
        flash("You are not authorized to access that location")
        return redirect(request.referrer)
    if request.method == 'POST':
        if request.form['name']:
            new_category = Category(
                name=request.form['name'], description=request.form['description'], user_id=getUserID(login_session.get('email')))
            session.add(new_category)
            flash('Category added!')
            session.commit()
            return redirect(url_for('category_new'))
    else:
        return render_template('category_new.html', title="New Category", categories_menu=categories_menu(True))

# Remove a category


@app.route('/categories/remove/<int:id>/', methods=['GET', 'POST'])
def category_remove(id):
    category = session.query(
        Category).filter_by(id=id).one()
    # Check to see if user is logged in and if this is his/her own record
    if 'username' not in login_session or getUserID(login_session.get('email')) != category.user_id:
        flash("You are not authorized to access that location")
        return redirect(request.referrer)
    if request.method == 'POST':
        session.delete(category)
        flash('Category removed!')
        session.commit()
        return redirect(url_for('category_new'))
    else:
        return render_template('category_remove.html', title="Please confirm..", category=category)

# Search the catalog


@app.route('/search/<string:q>')
def search(q):
    result = session.query(Item).filter(
        Item.name.like("%" + q + "%")).order_by(Item.name.asc())
    return render_template('search.html', result=result, q=q, title='Search result: "' + str(q) + '"', categories_menu=categories_menu())

# View item details


@app.route('/items/view/<int:id>')
def items_view(id):
    item = session.query(Item).filter_by(id=id).one()
    return render_template('items_view.html', item=item, title=item.name, categories_menu=categories_menu())

# Add new item


@app.route('/items/new', methods=['GET', 'POST'])
def items_new():
    # Only logged in users can add items
    if 'username' not in login_session:
        flash("You are not authorized to access that location")
        return redirect(request.referrer)
    if request.method == "GET":
        return render_template('items_new.html', title="New Item", categories_menu=categories_menu(True), categories_list=categories_menu())
    else:
        logged_in_user = getUserID(login_session.get('email'))
        if request.form['name']:
            # If image is selected upload it then save DB record
            image = request.files['image']
            if image:
                try:
                    image.save('static/img/' + secure_filename(image.filename))
                except Exception, e:
                    flash(e)
                    redirect(url_for('items_new'))

            if image:
                new_item = Item(name=request.form['name'], description=request.form[
                    'description'], price=request.form['price'], category_id=request.form['category'], user_id=logged_in_user, picture=secure_filename(image.filename))
            else:
                new_item = Item(name=request.form['name'], description=request.form[
                                'description'], price=request.form['price'], category_id=request.form['category'], user_id=logged_in_user)
            session.add(new_item)
            flash(
                "Do you have any idea about the shit storm is about to hit us?! kiddin! Item saved!")
            session.commit()
        return redirect(url_for('category_new'))

# Edit item


@app.route('/items/edit/<int:id>', methods=['GET', 'POST'])
def items_edit(id):
    item = session.query(Item).filter_by(id=id).one()
    # Check to see if user is logged in and if this is his/her own record
    if 'username' not in login_session or getUserID(login_session.get('email')) != item.user_id:
        flash("You are not authorized to access that location")
        return redirect(request.referrer)

    if request.method == "GET":
        return render_template('items_edit.html', item=item, title='Edit Item: "' + item.name + '"', categories_menu=categories_menu(True), categories_list=categories_menu())
    else:
        if request.form['name']:
            # If user updated the image remove the old one
            if request.files['image']:
                # Remove image from filesystem before the database opernation
                try:
                    os.remove('static/img/' + item.picture)
                except:
                    pass
                image = request.files['image']
                try:
                    image.save('static/img/' + secure_filename(image.filename))
                    item.picture = secure_filename(image.filename)
                except Exception, e:
                    pass
            item.name = request.form['name']
            item.description = request.form['description']
            item.price = request.form['price']
            session.commit()
            flash("Item saved!")
        return redirect(url_for('items_edit', id=id))

# Remove item with confirmation page


@app.route('/items/remove/<int:id>', methods=['GET', 'POST'])
def items_remove(id):
    item = session.query(
        Item).filter_by(id=id).one()
    # Check to see if user is logged in and if this is his/her own record
    if 'username' not in login_session or getUserID(login_session.get('email')) != item.user_id:
        flash("You are not authorized to access that location")
        return redirect(request.referrer)

    if request.method == 'POST':
        # Remove image from filesystem before the database opernation
        try:
            os.remove('static/img/' + item.picture)
        except:
            pass
        session.delete(item)
        flash('Item removed!')
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('items_remove.html', title="Please confirm..", item=item)


def categories_menu(private=False):
    ''' Gets all the categories to be displayed in menus
    '''
    if private:
        user_id = getUserID(login_session.get('email'))
        return session.query(Category).filter_by(user_id=user_id).order_by(Category.name.asc())
    else:
        return session.query(Category).order_by(Category.name.asc())

# Google login


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one and put user id in
    # the session
    userID = getUserID(login_session['email'])
    if userID == None:
        new_user_id = createUser(login_session)
        login_session['userID'] = new_user_id
    else:
        login_session['userID'] = userID

    #flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    response = make_response(json.dumps(
        'Success! Logged in as %s' % login_session['username']), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['userID']
        return True
    else:
        # For whatever reason, the given token was invalid.
        return False

# Facebook login


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly
    # logout, let's strip out the information before the equals sign in our
    # token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['userID'] = user_id

    print "done!"
    response = make_response(json.dumps(
        'Success! Logged in as %s' % login_session['username']), 200)
    response.headers['Content-Type'] = 'application/json'
    return response

# Facebook disconnect


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['provider']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['facebook_id']
    del login_session['userID']
    return True

# Universal logout function


@app.route('/logout')
def logout():
    logged_out = False
    if login_session['provider'] == 'google':
        if gdisconnect():
            logged_out = True
    if login_session['provider'] == 'facebook':
        if fbdisconnect():
            logged_out = True

    if logged_out:
        flash("Logged out successfully!")
    else:
        flash("Error trying to logged you out!")
    return redirect(url_for('index'))


def make_external(url):
    '''Generates a full URL
    '''
    return urljoin(request.url_root, url)

# Atom RSS feed route


@app.route('/recent.atom')
def recent_feed():
    feed = AtomFeed('Recent Articles',
                    feed_url=request.url, url=request.url_root)
    items = session.query(Item).limit(15).all()

    for item in items:
        feed.add(item.name, unicode(item.description),
                 content_type='html',
                 url=make_external(url_for('items_view', id=item.id)),
                 updated=datetime.date.today(),  # Simulating a real publishing date
                 published=datetime.date.today())
    return feed.get_response()

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'KJBHJ768ggs87HGFGD566rs56'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
