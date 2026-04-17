from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error


employer = Blueprint("employer", __name__)

# Retrieve list of high potential students based on GPA/Major criteria [Jackson - 5]
@employer.route("/students", methods=["GET"])
def get_high_potential_students():
    cursor = get_db().cursor(dictionary=True)
    try:
        gpa_cutoff = request.args.get("gpa", 3.5)
        query = """
        SELECT u.firstName, u.lastName, s.GPA, s.major, s.gradYear
        FROM STUDENT s
        JOIN USER u ON s.userId = u.userId
        WHERE gpa >= %s"""
        cursor.execute(query, (gpa_cutoff,))
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()

# Return all detail information for a particular student. [Jackson - 1]
@employer.route("/students/<int:id>", methods=["GET"])
def get_student_detail(id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * 
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            WHERE studentId = %s""", (id,))
        student = cursor.fetchone()
        return jsonify(student) if student else (jsonify({"error": "Student not found"}), 404)
    finally:
        cursor.close()


# List students who previously completed co-ops at the company. [Jackson - 6]
@employer.route("/students/history", methods=["GET"])
def get_coop_history():
    company_id = request.args.get("companyId", type=int)
    if company_id is None:
        return jsonify({"error": "companyId query parameter is required and must be an integer"}), 400

    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
          """SELECT DISTINCT u.firstName, u.lastName, u.email, s.major, s.GPA
              FROM USER u
              JOIN STUDENT s ON u.userId = s.userId
              JOIN COOPEXPERIENCE ce ON s.studentId = ce.studentId
              WHERE ce.companyId = %s""",
              (company_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Return all outreach threads and send new outreach messages to students[Jackson - 1]
@employer.route("/employer_outreach/history", methods=["GET"])
def get_outreach_threads():
    employerId = request.args.get("employerId", type=int)
    if employerId is None:
        return jsonify({"error": "employerId query parameter is required and must be an integer"}), 400

    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
          """SELECT *
              FROM EMPLOYEROUTREACH
              WHERE employerId = %s""",
              (employerId,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


#Create a new employer outreach message [Jackson - 1]
@employer.route("/employer_outreach/send", methods=["POST"])
def post_new_outreach():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["employerId", "studentId", "content"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO EMPLOYEROUTREACH (employerId, studentId, content)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            data["employerId"],
            data["studentId"],
            data["content"]
        ))

        get_db().commit()
        return jsonify({"message": "Outreach message created successfully", "empMessageId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

# Delete old, irrelevant employer outreach messages
@employer.route("/employer_outreach/history", methods=["DELETE"])
def delete_message(empMessageId):
    cursor = get_db().cursor()
    try:
        query = "DELETE FROM EMPLOYEROUTREACH WHERE empMessageId = %s"
        cursor.execute(query, (empMessageId,))
        get_db().commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Message not found"}), 404
        return jsonify({"message": "Message deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

    