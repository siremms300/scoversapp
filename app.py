#app.py

from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash 
import json
import secrets
import uuid
import bcrypt
from dotenv import load_dotenv
import os
 
# import pymysql
from database import (

                      load_courses_from_db, load_user_applications_from_db, update_application_status_in_db,
                      add_user_to_db, load_course_from_db, search_courses_in_db, load_all_applications_from_db, 
                      add_application_to_db, save_user_to_db, get_user_by_email, load_users_from_db,
                      load_single_user_applications_from_db, save_course_to_db
                      
                    )

app = Flask(__name__)  


appConf = {
    "OAUTH2_CLIENT_ID": "950826060226-fis6v47trlbv8vqiei40rji69u3fgdo3.apps.googleusercontent.com",
    "OAUTH2_CLIENT_SECRET": "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",
    "OAUTH2_META_URL": "https://accounts.google.com/.well-known/openid-configuration",
    "FLASK_SECRET": "7da06fed-aa86-4fa8-a964-0075cc98b604",
    "FLASK_PORT": 5000
} 


oauth = OAuth(app) 

load_dotenv()

# appConf = {
#     "OAUTH2_CLIENT_ID": os.getenv('OAUTH2_CLIENT_ID'),
#     "OAUTH2_CLIENT_SECRET": os.getenv('OAUTH2_CLIENT_SECRET'),
#     "OAUTH2_META_URL": os.getenv('OAUTH2_META_URL'),
#     "FLASK_SECRET": os.getenv('FLASK_SECRET'),
#     "FLASK_PORT": os.getenv('FLASK_PORT', 5000)
# }

 
app.secret_key = appConf.get('FLASK_SECRET')


 
oauth.register("myApp",
               client_id=appConf.get("OAUTH2_CLIENT_ID"),
               client_secret=appConf.get("OAUTH2_CLIENT_SECRET"),
               server_metadata_url=appConf.get("OAUTH2_META_URL"),
               client_kwargs= {
                   "scope": "openid profile email"
               }
               ) 


PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

@app.route('/')
def index():
    page = request.args.get('page', default=1, type=int)
    sort_by = request.args.get('sort_by', None)
    filters = request.args.getlist('filters')
    courses = load_courses_from_db(page=page, sort_by=sort_by, filters=filters)
    return render_template('home.html', courses=courses, page=page, sort_by=sort_by, filters=filters, 
                           session=session.get("user"), pretty=json.dumps(session.get("user"), indent=4))



@app.route('/google-login')
def googleLogin():
    nonce = secrets.token_urlsafe()
    session['nonce'] = nonce
    return oauth.myApp.authorize_redirect(redirect_uri=url_for("googleCallback", _external=True), nonce=nonce)




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

    flash('Login successful!', 'success')
    
    return redirect(url_for("index"))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)

        if user and bcrypt.checkpw(password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
            session['user'] = {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'is_admin': user.get('is_admin', False)
            }
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')



# ADMIN LOGIN 
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)

        if user and bcrypt.checkpw(password.encode('utf-8'), user['hashed_password'].encode('utf-8')) and user.get('is_admin'):
            session['user'] = {
                'user_id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'is_admin': user.get('is_admin', False)
            }
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password, or not an admin', 'danger')
            return redirect(url_for('adminlogin'))

    return render_template('adminlogin.html')





@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form and request.form['is_admin'] == 'on'

        # Generate a unique user_id
        user_id = str(uuid.uuid4())

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Save the new user to the database
        save_user_to_db(user_id, name, email, hashed_password, is_admin)

        # Redirect to login or some other page
        return redirect(url_for('index'))

    return render_template('signup.html')




@app.route('/adminregister', methods=['GET', 'POST'])
def adminregister():

    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form and request.form['is_admin'] == 'on'

        # Generate a unique user_id
        user_id = str(uuid.uuid4())

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Save the new user to the database
        save_user_to_db(user_id, name, email, hashed_password, is_admin)

        # Redirect to login or some other page
        return redirect(url_for('index'))

    return render_template('adminregister.html')





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
    
    application_dashboard = load_user_applications_from_db(user['user_id'])
    return render_template('application_dashboard.html', user=user, applications=application_dashboard) 



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


# APPLICATION LOGIC


@app.route('/course/<id>/apply', methods=['POST']) 
def apply_course(id):
    user = session.get("user")
    if not user:
        return redirect(url_for('login'))
    
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    document_url = request.form['document_url']
    
    course_name = request.form['course_name']
    location = request.form['location']
    school = request.form['school']
    tuition = request.form['tuition']
    
    add_application_to_db(user['user_id'], id, full_name, email, phone, document_url, course_name, location, school, tuition)
    
    return render_template('application_submitted.html', application=request.form)


# ADMIN FUNCTIONALITY 



# Route for admin dashboard
@app.route('/admin')
def admin_dashboard():
    user = session.get('user')
    if not user or not user.get('is_admin'):
        return redirect(url_for('login'))
    users = load_users_from_db()
    return render_template('admin_dashboard.html', user=user, users=users)



# I WILL GET BACK TO THIS FOR LOADING ALL APPLICATIONS FROM DB
@app.route('/admin/applications')
def admin_applications():
    user = session.get("user")
    if not user or not user.get('is_admin'):
        return redirect(url_for('login'))
    
    applications = load_all_applications_from_db()
    return render_template('viewapplication.html', applications=applications) 




@app.route('/admin/user/<user_id>/applications')
def view_user_applications(user_id):
    user = session.get('user')
    if not user or not user.get('is_admin'):
        return redirect(url_for('login'))
    
    applications = load_single_user_applications_from_db(user_id)
    return render_template('single_user_application.html', applications=applications)




@app.route('/admin/applications/<id>/update', methods=['POST'])
def update_application_status(id):
    user = session.get("user")
    if not user or not user.get('is_admin'):
        return redirect(url_for('login'))
    
    new_status = request.form['status']
    update_application_status_in_db(id, new_status)
    return redirect(url_for('admin_applications'))



# @app.route('/admin/singleapplications/<id>/update', methods=['POST'])
# def update_application_status_for_single_user(id):
#     user = session.get("user")
#     if not user or not user.get('is_admin'):
#         return redirect(url_for('login'))
    
#     new_status = request.form['status']
#     update_application_status_in_db(id, new_status) 
#     user_id = user.get('user_id')
#     return redirect(url_for('view_user_applications', user_id=user_id))



@app.route('/admin/singleapplications/<id>/update', methods=['POST'])
def update_application_status_for_single_user(id):
    user = session.get("user")
    if not user or not user.get('is_admin'):
        return redirect(url_for('login'))
    
    new_status = request.form['status']
    update_application_status_in_db(id, new_status)
    user_id = request.form['user_id']  # Assuming you include user_id in the form data
    return redirect(url_for('view_user_applications', user_id=user_id))


# app.py

@app.route('/admin/create_course', methods=['GET', 'POST'])
def create_course():
    user = session.get("user")
    if not user or not user.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Collect form data
        course_name = request.form['course']
        location = request.form['location']
        school = request.form['school']
        tuition = request.form['tuition']
        currency = request.form['currency']
        explanation = request.form['explanation']
        requirement = request.form['requirement']

        # Save the new course to the database
        # Assuming you have a function `save_course_to_db` in your database.py
        save_course_to_db(course_name, location, school, tuition, currency, explanation, requirement)

        # Redirect to admin dashboard or course list page
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_course.html')





if __name__ == '__main__':
    app.run(debug=True)
