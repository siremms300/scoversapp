#database.py 

import pymysql

# Database connection details
host = 'up-es-mad1-mysql-1.db.run-on-seenode.com'
port = 11550
user = 'db-apxgqtiyl5lt'
password = 'nkFjvzhlcaOP9jDD3oS1A4Dm'
database = 'db-apxgqtiyl5lt'



def load_courses_from_db(page=1, per_page=8, sort_by=None, filters=None):
    try:
        connection = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        with connection.cursor() as cursor:
            # Calculate the offset based on the page number
            offset = (page - 1) * per_page

            # Construct the SQL query with optional filtering and sorting
            sql = "SELECT * FROM courses"   
            params = []
            if filters:
                filter_clauses = []
                for filter_value in filters:
                    filter_clauses.append("course LIKE %s")
                    params.append(f"%{filter_value}%")
                sql += " WHERE " + " OR ".join(filter_clauses)

            if sort_by:
                sql += f" ORDER BY location {sort_by}"

            sql += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])

            cursor.execute(sql, params)
            result = cursor.fetchall()

            # Convert the result to a list of dictionaries
            result_dict_list = []
            for row in result:
                row_dict = {
                    "id": row[0],
                    "course": row[1],
                    "location": row[2],
                    "school": row[3],
                    "tuition": row[4],
                    "currency": row[5],
                    "explanation": row[6],
                    "requirement": row[7]
                }
                result_dict_list.append(row_dict)

            return result_dict_list

    except pymysql.Error as e:
        print(f"Error loading courses from the database: {e}")
        return []
    finally:
        connection.close()



def load_course_from_db(id, course=None, location=None, school=None, tuition=None):
    try:
        connection = pymysql.connect(host=host,
                                     port=port,
                                     user=user,
                                     password=password,
                                     database=database) 
        
        with connection.cursor() as cursor:
            # Construct the SQL query dynamically based on the provided parameters
            sql = "SELECT * FROM courses WHERE id = %s"
            params = [id]

            if course is not None:
                sql += " AND course = %s"
                params.append(course)
            if location is not None:
                sql += " AND location = %s"
                params.append(location)
            if school is not None:
                sql += " AND school = %s"
                params.append(school)
            if tuition is not None:
                sql += " AND tuition = %s"
                params.append(tuition)

            cursor.execute(sql, params)
            result = cursor.fetchone()  # Use fetchone instead of fetchall

            if result is None:
                return None 
            else:
                # Construct a dictionary for the single course
                course_dict = {
                    "id": result[0],
                    "course": result[1],
                    "location": result[2],
                    "school": result[3],
                    "tuition": result[4],
                    "currency": result[5],
                    "explanation": result[6],
                    "requirement": result[7]
                }
                return course_dict

    except pymysql.Error as e:
        print(f"Failed to load course from database: {e}")




def add_application_to_db(course_id, course_name, location, school, tuition, data):
    try:
        connection = pymysql.connect(host=host,
                                     port=port,
                                     user=user,
                                     password=password,
                                     database=database)

        with connection.cursor() as cursor:
            # Execute the SQL INSERT statement
            cursor.execute(
                "INSERT INTO applications (course_id, course_name, location, school, tuition, full_name, email, phone, document_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (course_id, course_name, location, school, tuition, data['full_name'], data['email'], data['phone'], data.get('document_url', None))
            )

            # Check if insertion was successful (returns the number of rows affected)
            if cursor.rowcount == 1:
                connection.commit()
                return True  # Indicate success
            else:
                return False  # Indicate failure

    except pymysql.Error as e:
        # If an error occurs, print the error message
        print(f"Failed to add application to the database: {e}")
        return False  # Indicate failure

    finally:
        # Close the database connection regardless of success or failure
        connection.close()




def search_courses_in_db(query, page=1, per_page=8, filters=None):
    try:
        connection = pymysql.connect(host=host,
                                    port=port,
                                    user=user,
                                    password=password,
                                    database=database)
        with connection.cursor() as cursor:
            # Calculate the offset based on the page number
            offset = (page - 1) * per_page

            # Construct the SQL query to search for courses with pagination
            sql = "SELECT * FROM courses WHERE (course LIKE %s OR location LIKE %s OR school LIKE %s)"
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]

            if filters:
                filter_clauses = []
                for filter_value in filters:
                    filter_clauses.append("course LIKE %s")
                    params.append(f"%{filter_value}%")
                sql += " AND (" + " OR ".join(filter_clauses) + ")"

            sql += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            
            cursor.execute(sql, params)
            result = cursor.fetchall()

            # Convert the result to a list of dictionaries
            result_dict_list = []
            for row in result:
                row_dict = {
                    "id": row[0],
                    "course": row[1],
                    "location": row[2],
                    "school": row[3],
                    "tuition": row[4],
                    "currency": row[5],
                    "explanation": row[6],
                    "requirement": row[7]
                }
                result_dict_list.append(row_dict)

            return result_dict_list

    except pymysql.Error as e:
        print(f"Error searching courses in the database: {e}")
        return []
    finally:
        connection.close()


def add_user_to_db(user_id, user_name, user_email):
    try:
        connection = pymysql.connect(host=host,
                                     port=port,
                                     user=user,
                                     password=password,
                                     database=database)
        with connection.cursor() as cursor:
            # Check if the user already exists
            cursor.execute("SELECT email FROM users WHERE email = %s", (user_email,)) 
            if cursor.fetchone() is None:
                # Insert the new user
                cursor.execute("INSERT INTO users (user_id, name, email) VALUES (%s, %s, %s)", 
                               (user_id, user_name, user_email))
                connection.commit()
    except pymysql.Error as e:
        print(f"Failed to add user to the database: {e}")
    finally:
        connection.close()
