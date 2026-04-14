from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

# Create a Blueprint for NGO routes
students = Blueprint("students", __name__)



# Get all students with their profile information
@students.route("/students", methods=["GET"])
def get_all_students():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /stu/students')
 
        query = """
            SELECT s.studentId, u.firstName, u.lastName, u.email,
                   s.major, s.GPA, s.gradYear, s.advisorId
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
        """

        cursor.execute(query)
        students_list = cursor.fetchall()

        current_app.logger.info(f'Retrieved {len(students_list)} students')
        return jsonify(students_list), 200
    except Error as e:
        current_app.logger.error(f'Database error in get_all_students: {e}')
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get a specific student's profile by studentId
@students.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /stu/students/{student_id}')
 
        query = """
            SELECT s.studentId, u.firstName, u.lastName, u.email,
                   s.major, s.GPA, s.gradYear, s.advisorId
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            WHERE s.studentId = %s
        """
        cursor.execute(query, (student_id,))
        student = cursor.fetchone()
 
        if not student:
            return jsonify({"error": "Student not found"}), 404
 
        return jsonify(student), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update a student's profile (major, GPA, gradYear)
@students.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'PUT /stu/students/{student_id}')
        data = request.get_json()
 
        cursor.execute("SELECT studentId FROM STUDENT WHERE studentId = %s", (student_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Student not found"}), 404
 
        # Build update query dynamically based on provided fields
        allowed_fields = ["major", "GPA", "gradYear"]
        update_fields = [f"{f} = %s" for f in allowed_fields if f in data]
        params = [data[f] for f in allowed_fields if f in data]
 
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
 
        params.append(student_id)
        query = f"UPDATE STUDENT SET {', '.join(update_fields)} WHERE studentId = %s"
        cursor.execute(query, params)
        get_db().commit()
 
        return jsonify({"message": "Student profile updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Search all co-op experiences with optional filtering by company, industry, or role
@students.route("/experiences", methods=["GET"])
def search_experiences():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info('GET /stu/experiences')
 
        company = request.args.get("company")
        industry = request.args.get("industry")
        role = request.args.get("role")
 
        query = """
            SELECT ce.experienceId, u.firstName, u.lastName,
                   c.companyName, c.industry, c.location,
                   cr.title, cr.department, cr.salary,
                   ce.semester, ce.year, ce.notes
            FROM COOPEXPERIENCE ce
            JOIN STUDENT s ON ce.studentId = s.studentId
            JOIN USER u ON s.userId = u.userId
            JOIN COMPANY c ON ce.companyId = c.companyId
            JOIN COOPROLE cr ON ce.roleId = cr.roleId
            WHERE 1=1
        """
        params = []
 
        if company:
            query += " AND c.companyName LIKE %s"
            params.append(f"%{company}%")
        if industry:
            query += " AND c.industry = %s"
            params.append(industry)
        if role:
            query += " AND cr.title LIKE %s"
            params.append(f"%{role}%")
 
        cursor.execute(query, params)
        results = cursor.fetchall()
 
        current_app.logger.info(f'Retrieved {len(results)} experiences')
        return jsonify(results), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Get all co-op experiences for a specific student
@students.route("/students/<int:student_id>/experiences", methods=["GET"])
def get_student_experiences(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'GET /stu/students/{student_id}/experiences')
 
        cursor.execute("SELECT studentId FROM STUDENT WHERE studentId = %s", (student_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Student not found"}), 404
 
        query = """
            SELECT ce.experienceId, c.companyName, c.industry, c.location,
                   cr.title, cr.department, cr.salary, cr.duration,
                   ce.semester, ce.year, ce.notes
            FROM COOPEXPERIENCE ce
            JOIN COMPANY c ON ce.companyId = c.companyId
            JOIN COOPROLE cr ON ce.roleId = cr.roleId
            WHERE ce.studentId = %s
            ORDER BY ce.year DESC, ce.semester
        """
        cursor.execute(query, (student_id,))
        experiences = cursor.fetchall()
 
        return jsonify(experiences), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Add a new co-op experience for a student
# Required fields: companyId, roleId, semester, year
# Example: POST /stu/students/1/experiences with JSON body
@students.route("/students/<int:student_id>/experiences", methods=["POST"])
def add_experience(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'POST /stu/students/{student_id}/experiences')
        data = request.get_json()
 
        required_fields = ["companyId", "roleId", "semester", "year"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
 
        query = """
            INSERT INTO COOPEXPERIENCE (studentId, companyId, roleId, semester, year, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            student_id,
            data["companyId"],
            data["roleId"],
            data["semester"],
            data["year"],
            data.get("notes", "")
        ))
        get_db().commit()
 
        return jsonify({"message": "Co-op experience added successfully",
                        "experienceId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a co-op experience for a student
# Example: DELETE /stu/students/1/experiences/3
@students.route("/students/<int:student_id>/experiences/<int:experience_id>", methods=["DELETE"])
def delete_experience(student_id, experience_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f'DELETE /stu/students/{student_id}/experiences/{experience_id}')
 
        cursor.execute("""SELECT experienceId FROM COOPEXPERIENCE
                          WHERE experienceId = %s AND studentId = %s""",
                       (experience_id, student_id))
        if not cursor.fetchone():
            return jsonify({"error": "Experience not found"}), 404
 
        cursor.execute("DELETE FROM COOPEXPERIENCE WHERE experienceId = %s", (experience_id,))
        get_db().commit()
 
        return jsonify({"message": "Co-op experience deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()



