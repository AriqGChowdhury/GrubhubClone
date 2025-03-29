import requests
import os
from flask import Flask, render_template, url_for, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text, create_engine
import bcrypt
from sqlalchemy.dialects import mysql
from geopy.geocoders import Nominatim
import base64
import jsonify
from flask import jsonify
from datetime import datetime, timedelta
import time
import urllib.parse
import smtplib
from restaurant_data import mcdonalds, tacoBell, wendys, burger_king, jets
import socket
from dotenv import load_dotenv
from sqlalchemy.orm.attributes import flag_modified
load_dotenv()


app = Flask(__name__)

secret_key = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"] = secret_key
app.config['SERVER_NAME'] = '127.0.0.1:5000'

db = SQLAlchemy(app)


# login_manager = LoginManager(app)
# login_manager.login_view = 'logIn'
cart_list = []
cart_deleted = False
total = 0

class Account(db.Model):
   id = db.Column('student_id', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   email = db.Column(db.String(100))
   password = db.Column(db.String(100))
   liked_restaurants = db.Column(db.JSON)
   
   def __init__(self, name, email, password, liked_restaurants):
       self.name = name
       self.password = password
       self.email = email
       self.liked_restaurants = liked_restaurants or []



GOOGLE_KEY = "AIzaSyAk0FoCamC2uAzN-9bj8p98063UVRF3haY"
PHOTO_KEY = "AIzaSyB543_ww6kfiqV43J1znUaufVZEL3BR9CM"
ALL_RESTAURANTS = ["McDonald's", "Wendys", "Burger King", "Taco Bell", "Jet's Pizza"]
with app.app_context():
    
    all_restaurant_info = {
        'McDonalds': mcdonalds,
        'McDonalds_Header': url_for('static', filename='mcdonalds_images/mcdonalds_header.webp'),
        "Taco Bell": tacoBell,
        "Taco Bell_Header": url_for('static', filename='tacoBell_images/taco_bell_header.webp'),
        "Wendys": wendys,
        "Burger King": burger_king,
        "Burger King_Header":url_for('static', filename='burgerking_images/burger_king_header.avif'),

        "Jets Pizza": jets
    }
    
    RESTAURANT_IMAGES = {
        "McDonald's": url_for('static', filename='restaurant_images/online_ordering_mcdonaldsImage.jpg', _external=True) ,
        "Wendys": url_for('static', filename='restaurant_images/online_ordering_wendysImage.png', _external=True),
        "Burger King": url_for('static', filename='restaurant_images/online_ordering_burgerKingImage.jpg', _external=True),
        "Jets Pizza": url_for('static', filename='restaurant_images/online_ordering_jetsPizza.png', _external=True),
        "Taco Bell": url_for('static', filename='restaurant_images/online_ordering_Taco BellImage.jpg', _external=True)
    }

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        user = request.form.get('email')
        session['user'] = user
        return render_template('index.html', user=user)
    if "user" in session:
        user = session['user']
        return render_template('index.html', user=user)
    return render_template('index.html')


@app.route('/results', methods=["GET", "POST"])
def results():
    if request.method == 'POST':
        location = Nominatim(user_agent="GrubHubClone").geocode(request.form['address-input']) 
        current_time = datetime.now().strftime('%I:%M %p')
        long = location.longitude
        lat = location.latitude
        embedUrl = f"https://www.google.com/maps/embed/v1/view?key={GOOGLE_KEY}&center={lat},{long}&zoom=10"
        global restaurantsAround
        restaurantsAround = list_of_restaurants(lat, long)
        
        # pictureUrl = requests.get("https://maps.googleapis.com/maps/api/place/photo")
        
        # tempLen1 = len(restaurantsAround['places']) - 1
        restaurants2 = []
        for i in range(len(restaurantsAround['places'])):
            if restaurantsAround['places'][i]['displayName']['text'] in ALL_RESTAURANTS:
                restaurants2.append(restaurantsAround['places'][i])
        tempLen1 = 0
        for i in range(0, len(restaurantsAround['places'])):
            if "regularOpeningHours" in restaurantsAround['places'][i]:
                if restaurantsAround['places'][i]['regularOpeningHours']['openNow'] != False and restaurantsAround['places'][i]['displayName']['text'] in RESTAURANT_IMAGES:
                    tempLen1 += 1
        
        
    #return restaurants2
    if "user" in session:
        user = session['user']
        return render_template('split.html', restaurants=restaurants2, length=len(restaurants2), tempLen=tempLen1, photoList=RESTAURANT_IMAGES, GOOGLE_KEY=GOOGLE_KEY, lat=lat, long=long, current_time=current_time, available_restaurants=ALL_RESTAURANTS, user=user)

    return render_template('split.html', restaurants=restaurants2, length=len(restaurants2), tempLen=tempLen1, photoList=RESTAURANT_IMAGES, GOOGLE_KEY=GOOGLE_KEY, lat=lat, long=long, current_time=current_time, available_restaurants=ALL_RESTAURANTS)


@app.route('/receive_cart', methods=['GET'])
def receive_data():
    data = request.args.get('data')
    itemList = ""
    global cart_list
    for i in range(len(data)):
        if data[i] == "$":
            itemList += ","
        if data[i] != ",":
            itemList += data[i]
        else:
            if itemList != "":
                cart_list.append(itemList)
                itemList = ""
    return jsonify(result=data)


@app.route('/foodOptionList', methods=['GET', 'POST'])   
def foodOptionList():
    button_texts = request.args.get('button_text')
    restaurants = []
    for i in range(len(restaurantsAround['places'])):
        if restaurantsAround['places'][i]['displayName']['text'] in ALL_RESTAURANTS:
            restaurants.append(restaurantsAround['places'][i])
    photoList = RESTAURANT_IMAGES
    
    
    return jsonify({'button': button_texts, "restaurants":restaurants, "photoList":photoList, "all_restaurants":ALL_RESTAURANTS})
    
    #return f'{button_texts}'
    

@app.route('/login')
def preLogIn():
    invalid = request.args.get('invalid') == 'True'
    return render_template('logIn.html', invalid=invalid)

@app.route('/cart')
def cart():
    if "user" in session:
        
        user = session['user']
        global cart_list
        global cart_deleted
        global total
        for i in range(len(cart_list)):
            if "$" in cart_list[i]:
                cart_list[i] = cart_list[i].replace("$",  "")
                cart_list[i] = cart_list[i].replace(",", "")
                totalCart = cart_list[i].replace("Large", "")
                totalCart= float(totalCart)
                total += totalCart
                

        if cart_deleted == True:
            cart_list.clear()
            cart_deleted = False
        
        return render_template("cart.html", user=user,cartItems=cart_list, total=total, cart_deleted=cart_deleted)
    return render_template("login.html")


@app.route('/delete_cart')
def delete_cart():
    global cart_deleted
    global total
    total = 0
    cart_deleted = True
    
    return jsonify(result=cart_deleted)

@app.route("/checkOut/<items>/<total>")
def checkOut(items, total):
    return f'<h3 style="text-align: center;">Order has been successfully placed!</h3>'



@app.route('/profile')
def profile():
    if "user" in session:
        user = session['user']
        return render_template('profile.html', user=user)
    return redirect(url_for('preLogIn'))

@app.route('/liked', methods=["GET", "POST"])
def liked():
    if "user" in session:
        user = session['user']
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        if result:
            acc = result['Account']
            return render_template('liked.html', user=user, restaurants=acc.liked_restaurants)
        else:
            print("No account")
    return redirect(url_for('preLogIn'))

@app.route('/addToLiked', methods=['GET', 'POST'])
def addToLiked():
    if request.method == 'POST':
        if "user" in session:
            user = session['user']
            email = session['email']
            data = request.args.get('data')
            result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
            if result:
                print(result)
                account = result['Account']
                if account.liked_restaurants is not None and account.liked_restaurants != []:
                    if data in account.liked_restaurants:
                        return "already in liked"
                    temp_list = []
                    for items in account.liked_restaurants:
                        temp_list.append(items)
                    account.liked_restaurants = []
                    account.liked_restaurants = temp_list
                    account.liked_restaurants.append(data)
                    db.session.commit()
                if account.liked_restaurants is None or account.liked_restaurants == []:
                    account.liked_restaurants = [] 
                    account.liked_restaurants.append(data)
                    
                    db.session.commit()
                    return "success"
    return "fail"

@app.route('/unlike', methods=['POST'])
def unlike():
    if "user" in session:
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        if result:
            acc = result['Account']
            data = request.args.get('data')
            acc.liked_restaurants.remove(data)
            flag_modified(acc, "liked_restaurants") 
            print(db.session.dirty)
            db.session.commit()
            return "success"
    return "fail"


@app.route('/changeAccount')
def changeAccount():
    if "user" in session:
        user = session['user']
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        
        if result:
            account = result['Account']
        return render_template('changeAccount.html', name=account.name, user=user, email=account.email)
    return redirect(url_for('preLogIn'))

@app.route('/restaurantSubmission', methods=["GET", 'POST'])
def restaurantSubmission():
    if request.method == 'GET':
        return render_template('submission.html')
    if request.method == "POST" and "user" in session:
        user = session['user']
        email = session['email']
        resName = request.form['resName']
        resLocation = request.form['resLocation']
        resCity = request.form['resCity']
        resState = request.form['resState']
        resNumber = request.form['resNumber']
        resZip = request.form['resZip']
        smtp_pass = os.getenv("SMTP_PASS")
        host = "smtp-relay.brevo.com"
        port = 587
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login("88eab7001@smtp-brevo.com", smtp_pass)
        FROM = email
        TO = "ariqq922@gmail.com"
        MSG = f"""
            Subject: Restaurant Submission\n\n 
            Name:{resName}
            Location:{resLocation}\n
            City: {resCity}
            State: {resState}\n
            Number: {resNumber}
            Zip: {resZip}
        """
        server.sendmail(FROM, TO, MSG)
        server.quit()
        return render_template('profile.html', user=user)
    


@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop("user", None)
        session.pop('email', None)
        return redirect(url_for('preLogIn'))
    else:
        return redirect(url_for('home'))
    
@app.route('/signUp')
def signUp():
    emailinUse = request.args.get('emailinUse') == 'True' 
    
    return render_template('signUp.html', emailinUse=emailinUse)

def hashed_pass(user_pass):
    salt = bcrypt.gensalt()
    hash_pass = bcrypt.hashpw(user_pass.encode('utf-8'), salt=salt)
    return hash_pass

@app.route('/verify', methods=['GET', 'POST'])
def verifySignUp():
    if "user" in session:
        session.pop("user", None)
        session.pop('email', None)
        session['user'] = request.form.get('fName') + " " + request.form.get('lName')
    
    check_if_registered = Account.query.filter_by(email=request.form.get('email')).first()
    if check_if_registered: 
        return redirect(url_for('signUp', emailinUse='True'))
    user = request.form.get('fName') + " " + request.form.get('lName')
    user_email = request.form.get('email')
    user_pass = hashed_pass(request.form.get('password'))
    if request.form.get('checkbox') == "on":
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=30)
    else:
        session.permanent = False
    session['user'] = user
    session['email'] = user_email
    new_user = Account(email=user_email, name=user, password=user_pass, liked_restaurants=None)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('home', user=user))

@app.route('/verifyLogin', methods=['GET', 'POST'])
def verifyLogin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        if 'user' in session:
            session.pop('user', None)
            session.pop('email', None)
        find_email = Account.query.filter_by(email=email).first()
        if find_email:
            check_pass = find_email.password
            
            if bcrypt.checkpw(password.encode('utf-8'), check_pass):
                session['user'] = find_email.name
                session['email'] = email
                if request.form.get('checkbox') == "on":
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=30)
                else:
                    session.permanent = False
                return redirect(url_for('home'))
            else:
                return redirect(url_for('preLogIn', invalid='True'))
        else:
            return redirect(url_for('preLogIn', invalid='True'))
    else:
        return redirect(url_for('preLogIn'))

#Changing password
@app.route('/checkPass', methods=['POST'])
def checkPass():
    if request.method == 'POST' and "user" in session:
        user = session['user']
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        
        if result:
            data = request.get_json()
            password = data.get("password")
            account = result['Account']
            check_pass = account.password
            if bcrypt.checkpw(password.encode('utf-8'), check_pass):
                return "True"
    return "False"

@app.route('/changePass')
def changePass():
    if "user" in session:
        user = session['user']
        return render_template('changePass.html', user=user)
    return "Failed"

@app.route('/passChange', methods=['POST'])
def passChange():

    if "user" in session:
        email = session['email']
        user = session['user']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        if result:
            data = request.get_json()
            password = data.get("password")
            account = result['Account']
            account.password = hashed_pass(password)
            db.session.commit() 
            return render_template('profile.html', user=user)
    return "Failed"

@app.route("/makeChanges", methods=['POST'])
def makeChanges():
    if request.method == "POST" and "user" in session:
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        if result:
            changeName = request.form['changeName']
            changeEmail = request.form['changeEmail']
            account = result['Account']
            account.name = changeName
            account.email = changeEmail
            user = account.name
            db.session.commit()
            return render_template('profile.html', user=user)
    return redirect(url_for('preLogIn'))

@app.route('/delete', methods=['POST'])
def deleteAcc():
    if "user" in session and request.method == "POST":
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        if result:
            session.pop('user', None)
            session.pop('email', None)
            account = result['Account']
            db.session.delete(account)
            db.session.commit()
            return redirect(url_for('preLogIn'))
    return redirect(url_for('home'))
    
    
    
@app.route('/<restaurantName>/menu/<ratingVar>/<userRatingVar>/<phoneNumVar>/<locationVar>')
def restaurantMenu(restaurantName, ratingVar, userRatingVar, phoneNumVar, locationVar):
    locationVar = locationVar.split(',')[0]
    iconImgUrl = f'restaurant_images/online_ordering_{restaurantName}Image.jpg'
    liked = False
    if "user" in session:
        user = session['user']
        email = session['email']
        result = db.session.execute(db.select(Account).where(Account.email == email)).mappings().first()
        if result:
            acc = result['Account']
            if f"{restaurantName} {locationVar}" in acc.liked_restaurants:
                liked = True
                print("executed")
        return render_template('restaurantMenu.html', restaurantName=restaurantName, restaurant_info=all_restaurant_info[restaurantName]['menu_items'], ratingVar=ratingVar, userRatingVar=userRatingVar, phoneNumVar=phoneNumVar, locationVar=locationVar, header_info=all_restaurant_info[restaurantName + '_Header'], iconImgUrl=iconImgUrl, user=user, liked=liked)
    return render_template('restaurantMenu.html', restaurantName=restaurantName, restaurant_info=all_restaurant_info[restaurantName]['menu_items'], ratingVar=ratingVar, userRatingVar=userRatingVar, phoneNumVar=phoneNumVar, locationVar=locationVar, header_info=all_restaurant_info[restaurantName + '_Header'], iconImgUrl=iconImgUrl)
def list_of_restaurants(lat, long):
    paylaod = {
        "includedTypes": ["restaurant"],
        "maxResultCount": 20,
        "rankPreference": "DISTANCE",
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude":lat,
                    "longitude":long 
                },
                "radius": 30000.0
            }
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': GOOGLE_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.regularOpeningHours,places.id,places.primaryTypeDisplayName,places.rating,places.userRatingCount,places.primaryType,places.websiteUri,places.types' 
    }

    response = requests.post("https://places.googleapis.com/v1/places:searchNearby", headers=headers, json=paylaod)
    return response.json()



with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True)


