from flask import Flask, render_template, request, jsonify 
# import pymysql
from database import load_courses_from_db, load_course_from_db, add_application_to_db, search_courses_in_db

app = Flask(__name__)  


@app.route('/') 
def index(): 
    courses = load_courses_from_db()
    # return "Hello world" 
    return render_template('home.html', courses=courses) 




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

    if not query and not location:
        # If neither query nor location provided, display all courses
        return render_template('home.html', courses=load_courses_from_db())

    # Perform a database query to search for courses
    search_results = search_courses_in_db(query)

    if location:
        # If location provided, filter courses by location
        search_results = [course for course in search_results if course['location'] == location]

    # Sort courses by location if location is provided
    sorted_results = sorted(search_results, key=lambda x: x['location'])

    return render_template('search_results.html', query=query, results=sorted_results)





