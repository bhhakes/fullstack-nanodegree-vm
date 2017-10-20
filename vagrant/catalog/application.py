# application.py
from models import Base, User, Category, Item
from flask import Flask, jsonify, request, redirect,\
                  url_for, abort, g, render_template, make_response, flash
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from flask_httpauth import HTTPBasicAuth
import requests
import httplib2
import json

# import session query data
from flask import session as login_session
import random
import string

auth = HTTPBasicAuth()

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# login page
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)



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
        return response

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

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                        json.dumps('Current user is already connected.'),
                        200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;\
                  height: 300px;\
                  border-radius: 150px;\
                  -webkit-border-radius: 150px;\
                  -moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# disconnect - revoke a current user's token and reset their login session
@app.route('/gdisconnect')
def gdisconnect():
    if 'username' not in login_session:
        return redirect('/login')
    access_token = login_session['access_token']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
                        json.dumps('Current user not connected.'),
                        401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash("you have now successfully logged out")
        return redirect('/index')
    else:
        response = make_response(json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


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


# user account page
@app.route('/account')
def showAccount():
    if 'username' not in login_session:
        return redirect('/index')
    # account view page
    user = login_session
    return render_template('accountDetail.html', user=user)


# main public frontpage
@app.route('/index')
def showIndex():
    # frontpage for users not signed up
    return render_template('index.html')


# main catalog page, show all categories
@app.route('/')
@app.route('/catalog')
def getCatalog():
    if 'username' not in login_session:
        return redirect('/index')
    # else:
    #    user_id = getUserID(login_session['email'])
    #    print user_id
    user = login_session
    user_id = login_session['user_id']
    category = session.query(Category).filter_by(user_id=user_id).all()

    # return "This page will show all my categories"
    return render_template('catalog.html', category=category, user=user)


# view all items within a specific category
@app.route('/<category>/items')
def getCategoryItems(category):
    if 'username' not in login_session:
        return redirect('/index')
    user = login_session
    user_id = login_session['user_id']
    category = session.query(Category).filter_by(name=category,
                                                 user_id=user_id).all()

    for c in category:
        items = session.query(Item).filter_by(category_name=c.name,
                                              user_id=user_id).all()
        # return "This page will show all items in one category"
        return render_template('category.html', category=category,
                               items=items, user=user)


# add new category
@app.route('/catalog/new', methods=['GET', 'POST'])
def createNewCategory():
    if 'username' not in login_session:
        return redirect('/index')
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("New Golf Course category created!")
        return redirect(url_for('getCatalog'))
    else:
        user = login_session
        return render_template('newCategory.html', user=user)


# edit a given cateogry
@app.route('/<category>/<cat_id>/edit', methods=['GET', 'POST'])
def editCategory(category, cat_id):
    if 'username' not in login_session:
        return redirect('/index')
    if request.method == 'POST':
        categoryToEdit = session.query(Category).filter_by(
                                        id=cat_id,
                                        user_id=login_session['user_id']).one()

        # change the name of the category
        categoryToEdit.name = request.form['name']
        session.add(categoryToEdit)
        session.commit()

        # update the items table to reflect the new name
        orphItems = session.query(Item).filter_by(
                                category_name=category,
                                user_id=login_session['user_id']).all()
        for o in orphItems:
            o.category_name = request.form['name']
            session.add(o)
            session.commit()
        flash("Updated \"" + category +
              "\" golf course category to \"" + categoryToEdit.name + "\"")
        return redirect(url_for('getCatalog'))
    else:
        user = login_session
        return render_template('editCategory.html',
                               category=category, cat_id=cat_id, user=user)


# delete a given cateogry including the items within it
@app.route('/<category>/<cat_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category, cat_id):
    if 'username' not in login_session:
        return redirect('/index')
    if request.method == 'POST':
        categoryToDelete = session.query(Category).filter_by(
                                    id=cat_id,
                                    user_id=login_session['user_id']).one()
        session.delete(categoryToDelete)
        session.commit()
        orphItems = session.query(Item).filter_by(
                                    category_name=category,
                                    user_id=login_session['user_id']).all()

        for o in orphItems:
            session.delete(o)
            session.commit()
        flash("Deleted \"" + category +
              "\" golf course category and any associated golf courses.")
        return redirect(url_for('getCatalog'))
    else:
        user = login_session
        return render_template('deleteCategory.html',
                               category=category, cat_id=cat_id, user=user)


# view a given item in detail
@app.route('/<category>/<item>/<item_id>/')
def getItemDetail(category, item, item_id):
    if 'username' not in login_session:
        return redirect('/index')
    specificItem = session.query(Item).filter_by(
                                    id=item_id,
                                    user_id=login_session['user_id']).one()
    description = specificItem.description
    user = login_session
    return render_template('categoryItem.html',
                           category=category, item=item,
                           item_id=item_id, description=description,
                           user=user)


# create a new item
@app.route('/<category>/newitem', methods=['GET', 'POST'])
def createItem(category):
    if 'username' not in login_session:
        return redirect('/index')
    if request.method == 'POST':
        newItem = Item(title=request.form['name'],
                       description=request.form['description'],
                       category_name=category,
                       user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        user = login_session
        flash("Created \"" + newItem.title + "\".")
        return redirect(url_for('getCategoryItems',
                                category=category, user=user))
    else:
        user = login_session
        return render_template('newCategoryItem.html',
                               category=category, user=user)


# edit a given item
@app.route('/<category>/<item>/<item_id>/edit', methods=['GET', 'POST'])
def editItem(category, item, item_id):
    if 'username' not in login_session:
        return redirect('/index')
    if request.method == 'POST':
        itemToEdit = session.query(Item).filter_by(
                                id=item_id,
                                user_id=login_session['user_id']).one()

        # change the name & description of the course in the db
        itemToEdit.title = request.form['title']
        itemToEdit.description = request.form['description']
        session.add(itemToEdit)
        session.commit()
        user = login_session
        flash("Updated \"" + item + "\" to \"" + itemToEdit.title + "\".")
        return redirect(url_for('getCategoryItems',
                                category=category, user=user))
    else:
        user = login_session
        return render_template('editCategoryItem.html', category=category,
                               item=item, item_id=item_id, user=user)


# delete a given item
@app.route('/<category>/<item>/<item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category, item, item_id):
    if 'username' not in login_session:
        return redirect('/index')
    if request.method == 'POST':
        itemToDelete = session.query(Item).filter_by(
                                id=item_id,
                                user_id=login_session['user_id']).one()
        session.delete(itemToDelete)
        session.commit()
        flash("Deleted \"" + item + "\".")
        user = login_session
        return redirect(url_for('getCategoryItems',
                                category=category, user=user))
    else:
        user = login_session
        return render_template('deleteCategoryItem.html', category=category,
                               item=item, item_id=item_id, user=user)


# JSON endpoint for a given category
@app.route('/<category>/JSON')
def getCategoryJSON(category):
    if 'username' not in login_session:
        return redirect('/index')
    category = session.query(Category).filter_by(
                                name=category,
                                user_id=login_session['user_id']).all()
    for c in category:
        items = session.query(Item).filter_by(
                                category_name=c.name,
                                user_id=login_session['user_id']).all()
    return jsonify(Courses=[i.serialize for i in items])


# JSON endpoint for a given item
@app.route('/<category>/<item>/JSON')
def getItemJSON(category, item):
    if 'username' not in login_session:
        return redirect('/index')
    specificItem = session.query(Item).filter_by(
                                title=item,
                                user_id=login_session['user_id']).one()
    return jsonify(Course=[specificItem.serialize])


# start server
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
