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
        query = "SELECT * FROM STUDENT WHERE gpa >= %s"
        cursor.execute(query, (gpa_cutoff,))
        return jsonify(cursor.fetchall()), 200
    finally:
        cursor.close()

# Return all detail information for a particular student. [Jackson - 1]
@employer.route("/students/<int:id>", methods=["GET"])
def get_student_detail(id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM STUDENT WHERE studentId = %s", (id,))
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

