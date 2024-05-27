#app.py

from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import secrets

# import pymysql
from database import load_courses_from_db, add_user_to_db, load_course_from_db, add_application_to_db, search_courses_in_db

app = Flask(__name__)  


appConf = {
    "OAUTH2_CLIENT_ID": "950826060226-fis6v47trlbv8vqiei40rji69u3fgdo3.apps.googleusercontent.com",
    "OAUTH2_CLIENT_SECRET": "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",
    "OAUTH2_META_URL": "https://accounts.google.com/.well-known/openid-configuration",
    "FLASK_SECRET": "7da06fed-aa86-4fa8-a964-0075cc98b604",
    "FLASK_PORT": 5000
} 



app.secret_key = appConf.get('FLASK_SECRET')


oauth = OAuth(app) 

oauth.register("myApp",
               client_id=appConf.get("OAUTH2_CLIENT_ID"),
               client_secret=appConf.get("OAUTH2_CLIENT_SECRET"),
               server_metadata_url=appConf.get("OAUTH2_META_URL"),
               client_kwargs= {
                   "scope": "openid profile email"
               }
               ) 


@app.route('/')
def index():
    page = request.args.get('page', default=1, type=int)
    sort_by = request.args.get('sort_by', None)
    filters = request.args.getlist('filters')
    courses = load_courses_from_db(page=page, sort_by=sort_by, filters=filters)
    return render_template('home.html', courses=courses, page=page, sort_by=sort_by, filters=filters, 
                           session=session.get("user"), pretty=json.dumps(session.get("user"), indent=4))


# @app.route('/google-login')
# def googleLogin():
#     return oauth.myApp.authorize_redirect(redirect_uri=url_for("googleCallback", _external=True)) 


@app.route('/google-login')
def googleLogin():
    nonce = secrets.token_urlsafe()
    session['nonce'] = nonce
    return oauth.myApp.authorize_redirect(redirect_uri=url_for("googleCallback", _external=True), nonce=nonce)


 
# @app.route('/google-signin') 
# def googleCallback():
#     token = oauth.myApp.authorize_access_token()
#     session["user"] = token 
#     return redirect(url_for("index")) 


# @app.route('/google-signin') 
# def googleCallback():
#     token = oauth.myApp.authorize_access_token()
#     user_info = oauth.myApp.parse_id_token(token)
    
#     # Extract user details
#     user_id = user_info['sub']
#     user_name = user_info.get('name')
#     user_email = user_info.get('email')
    
#     # Save user details in session
#     session["user"] = {
#         "id": user_id,
#         "name": user_name,
#         "email": user_email
#     }
    
#     # Save user details in the database
#     add_user_to_db(user_id, user_name, user_email)
    
#     return redirect(url_for("index"))



@app.route('/google-signin')
def googleCallback():
    token = oauth.myApp.authorize_access_token()
    nonce = session.pop('nonce', None)
    
    if not nonce:
        return "Nonce not found in session", 400
    
    user_info = oauth.myApp.parse_id_token(token, nonce=nonce)
    
    # Extract user details
    user_id = user_info['sub']
    user_name = user_info.get('name')
    user_email = user_info.get('email')
    user_picture = user_info.get('picture')  # Extract the profile picture
    
    # Save user details in session
    session["user"] = {
        "user_id": user_id,
        "name": user_name,
        "email": user_email,
        "picture": user_picture
    }

    print(session["user"]) 
    
    # Save user details in the database
    add_user_to_db(user_id, user_name, user_email)
    
    return redirect(url_for("index"))




# @app.route('/user')
# def userDashboard():
#     return render_template('userdashboard.html') 

@app.route('/login')
def login():
    user = session.get("user") 
    print(user)
    if not user:
        return render_template('login.html', user=user) 
    return redirect(url_for('index'))



@app.route('/register')
def register():
    return render_template('signup.html') 


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index')) 


@app.route('/user')
def userDashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for('login'))
    return render_template('userdashboard.html', user=user)


@app.route('/application_dashboard.html')
def application_dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for('login'))
    return render_template('application_dashboard.html', user=user) 



@app.route('/course/<id>')
def show_course(id):
    # Extract additional parameters from the query string
    course_name = request.args.get('course')
    location = request.args.get('location')
    school = request.args.get('school')
    tuition = request.args.get('tuition')

    # Fetch the course details based on the provided parameters
    course = load_course_from_db(id, course_name, location, school, tuition) 

    if course is None:
        return render_template("notfound.html")
    else:
        return render_template('coursepage.html', course=course)



@app.route('/api/courses')
def listcourses():
    location = request.args.get('location')
    if location:
        # Filter courses by location if location is provided
        courses = [course for course in load_courses_from_db() if course['location'] == location]
    else:
        courses = load_courses_from_db()
    return jsonify(courses) 





@app.route('/course/<id>/apply', methods=['POST']) 
def apply_course(id):
    # Extract additional parameters from the query string
    course_name = request.args.get('course')
    location = request.args.get('location')
    school = request.args.get('school')
    tuition = request.args.get('tuition')

    data = request.form 
    course = load_course_from_db(id, course_name, location, school, tuition)
    if course is None:
        return render_template("notfound.html")
    else:
        # Store the data in DB 
        # send an email 
        # display an acknowledgement 
        add_application_to_db(id, course_name, location, school, tuition, data)
        return render_template('application_submitted.html', application=data, course=course)




@app.route('/search')
def search_courses():
    query = request.args.get('q')
    location = request.args.get('location')
    page = request.args.get('page', default=1, type=int)
    sort_by = request.args.get('sort_by', None)
    filters = request.args.getlist('filters')

    if not query and not location:
        # If neither query nor location provided, display all courses
        courses = load_courses_from_db(page=page, sort_by=sort_by, filters=filters)
        return render_template('home.html', courses=courses, page=page, sort_by=sort_by, filters=filters)

    # Perform a database query to search for courses with pagination and filtering
    search_results = search_courses_in_db(query, page=page, filters=filters)

    if location:
        # If location provided, filter courses by location
        search_results = [course for course in search_results if course['location'] == location]

    # Sort courses by location if location is provided
    sorted_results = sorted(search_results, key=lambda x: x['location'])

    return render_template('search_results.html', query=query, results=sorted_results, page=page, sort_by=sort_by, filters=filters)


