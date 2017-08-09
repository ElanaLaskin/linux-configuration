from flask import Flask, render_template, url_for, request, redirect, jsonify, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import logging

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/Catalog/Catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "RestaurantMenuApp"

engine = create_engine('postgresql://catalog:zxcv@localhost/restaurantmenu')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# I got the gconnect method from Abhishek Ghosh, a Udacity instructor

# Create anti-forgery state token
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
        response = make_response(json.dumps('Invalid state parameter!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/Catalog/Catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        credentials = credentials.to_json()
        credentials = json.loads(credentials)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials['access_token']
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # print result

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended app_user.
    gplus_id = credentials['id_token']['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's app_user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current app_user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get app_user info
    app_userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials['access_token'], 'alt': 'json'}
    answer = requests.get(app_userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['app_username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    app_user_id = getUserID(login_session['email'])

    if not app_user_id:
        app_user_id = createUser(login_session)
    login_session['app_user_id'] = app_user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['app_username']
    output += '!<br> Email :'
    output += login_session['email']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;
                border-radius: 150px;-webkit-border-radius: 150px;
                -moz-border-radius: 150px;"> '''
    return output


# Most of the code below I got from the Udacity repo
# User Helper Functions

def createUser(login_session):
    newUser = User(name=login_session['app_username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    app_user = session.query(User).filter_by(email=login_session['email']).one()
    return app_user.id


def getUserInfo(app_user_id):
    app_user = session.query(User).filter_by(id=app_user_id).one()
    return app_user


def getUserID(email):
    try:
        app_user = session.query(User).filter_by(email=email).one()
        return app_user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print login_session['app_username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current app_user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token'] 
        del login_session['gplus_id']
        del login_session['app_username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
    
        response = make_response(json.dumps('Failed to revoke token for given app_user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response




# Making an API endpoint (get request)
@app.route('/restaurants/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurant=[restaurant.serialize for restaurant in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant=restaurant).all()
    return jsonify(MenuItems=[item.serialize for item in items])


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_item_id>/JSON')
def menuItem(restaurant_id, menu_item_id):
    item = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_item_id).one()
    return jsonify(MenuItem=item.serialize)


@app.route('/')
@app.route('/restaurant')
def showRestaurants():
    restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
    logging.warning(login_session)
    if 'app_username' not in login_session:
        return render_template('publicrestaurants.html', restaurants=restaurants)
    else:
        return render_template('restaurants.html', restaurants=restaurants)



@app.route('/restaurant/new', methods=['GET', 'POST'])
def newRestaurant():
    if 'app_username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        restaurantName = request.form['restaurant']

        try:
            thisRestaurantAlreadyExists = session.query(
            Restaurant).filter_by(name=restaurantName).one()
        
            flash('This Restaurant Already Exists')
            return redirect(url_for('showRestaurants'))

        except:
            new_restaurant = Restaurant(
                name = restaurantName, 
                app_user_id = login_session['app_user_id']
            )
            session.add(new_restaurant)
            session.commit()
            flash('New Restaurant Created')
            return redirect(url_for('showRestaurants'))
    else:
        return render_template('new-restaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    restaurantToEdit = session.query(
        Restaurant).filter_by(id=restaurant_id).one()

    if 'app_username' not in login_session:
        return redirect('/login')

    if restaurantToEdit.app_user_id != login_session['app_user_id']:
        flash('You are not authorized to edit this restaurant')
        return redirect(url_for('showRestaurants'))

    if request.method == 'POST':

        restaurantName = request.form['restaurant']

        try:
            thisRestaurantAlreadyExists = session.query(
            Restaurant).filter_by(name=restaurantName).one()
        
            flash('This Restaurant Already Exists')
            return redirect(url_for('showRestaurants'))

        except:
            restaurantToEdit.name = restaurantName
            session.add(restaurantToEdit)
            session.commit()

            flash('%s Successfully Edited' % restaurantToEdit.name)
            return redirect(url_for('showRestaurants', restaurant_id=restaurant_id))
    else:
        return render_template('edit-restaurant.html', restaurant=restaurantToEdit)



@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if 'app_username' not in login_session:
        return redirect('/login')
    
    restaurantToDelete = session.query(Restaurant).filter_by(id=restaurant_id).one()
    
    if restaurantToDelete.app_user_id != login_session['app_user_id']:
        flash('You are not authorized to delete this restaurant')
        return redirect(url_for('showRestaurants'))

    if request.method == 'POST':
        session.delete(restaurantToDelete)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('delete-restaurant.html', restaurant=restaurantToDelete)


@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    restaurantToShowMenu = session.query(Restaurant).filter_by(id=restaurant_id).one()
    creator = getUserInfo(restaurantToShowMenu.app_user_id)
    menuItems = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()

    if 'app_username' not in login_session or creator.id != login_session['app_user_id']:
        return render_template('publicmenu.html', items=menuItems, restaurant=restaurantToShowMenu, creator=creator)
    else:
        return render_template('menu.html', items=menuItems, restaurant=restaurantToShowMenu, restaurant_id=restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if 'app_username' not in login_session:
        return redirect('/login')
    
    restaurantToShowMenu = session.query(Restaurant).filter_by(id=restaurant_id).one()
    
    if restaurantToShowMenu.app_user_id != login_session['app_user_id']:
        flash('You are not authorized to add a menu item')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    
    if request.method == 'POST':

        itemName = request.form['item']

        try:
            thisItemAlreadyExists = session.query(
            MenuItem).filter_by(name=itemName).one()
        
            flash('This Item Already Exists')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))

        except:
            new_item = MenuItem(name = request.form['item'], price=request.form['price'], description=request.form['description'], restaurant_id=restaurant_id)
            session.add(new_item)
            session.commit()
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('new-menu-item.html', restaurant=restaurantToShowMenu)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_item_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_item_id):
    if 'app_username' not in login_session:
        return redirect('/login')

    menuItemToEdit = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_item_id).one()
    parentRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()

    if parentRestaurant.app_user_id != login_session['app_user_id']:
        flash('You are not authorized to edit this menu item')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))

    if request.method == 'POST':

        itemName = request.form['item']

        try:
            thisItemAlreadyExists = session.query(
            MenuItem).filter_by(name=itemName).one()
        
            flash('This Item Already Exists')
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))

        except:

            menuItemToEdit.name = request.form['item']
            session.commit()
            return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('edit-menu-item.html', item=menuItemToEdit)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_item_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_item_id):
    if 'app_username' not in login_session:
        return redirect('/login')

    menuItemToDelete = session.query(MenuItem).filter_by(restaurant_id=restaurant_id, id=menu_item_id).one()
    parentRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()

    if parentRestaurant.app_user_id != login_session['app_user_id']:
        flash('You are not authorized to delete this menu item')
        return redirect(url_for('showRestaurants'))

    if request.method == 'POST':
        session.delete(menuItemToDelete)
        session.commit()
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('delete-menu-item.html', item=menuItemToDelete)


if __name__ == '__main__':
    app.secret_key = 'secret'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
    
