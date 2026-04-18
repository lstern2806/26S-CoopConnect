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
@employer.route("/<int:employer_id>/outreach/history", methods=["GET"])
def get_outreach_threads(employer_id):
    if employer_id is None:
        return jsonify({"error": "employerId query parameter is required and must be an integer"}), 400

    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
          """SELECT *
              FROM EMPLOYEROUTREACH
              WHERE employerId = %s""",
              (employer_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


#Create a new employer outreach message [Jackson - 1]
@employer.route("/<int:employer_id>/outreach", methods=["POST"])
def post_new_outreach(employer_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = [ "studentId", "content"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO EMPLOYEROUTREACH (employerId, studentId, content, dateSent, response, responseDate)
            VALUES (%s, %s, %s, NOW(), NULL, NULL)
        """
        cursor.execute(query, (
            employer_id,
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

@employer.route("/analytics/interest_over_time", methods=["GET"])
def get_interest_over_time():
    company_id = request.args.get("companyId", type=int)
    if company_id is None:
        return jsonify({"error": "companyId query parameter is required and must be an integer"}), 400

    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
          """SELECT 
                DATE(dateSent) AS day,
                COUNT(*) AS messageCount
            FROM STUDENTOUTREACH
            WHERE companyId = %s
            GROUP BY DATE(dateSent)
            ORDER BY day;""",
              (company_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Retrieve engagement metrics compared to peer company averages. [Jackson-5]
# right now are mock-data is not sufficient so the average for the other companies will be 0.
@employer.route("/analytics/company_comparison", methods=["GET"])
def get_peer_comparison():
    company_id = request.args.get("companyId", type=int)
    if company_id is None:
        return jsonify({"error": "companyId query parameter is required"}), 400

    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
        SELECT 
            c.day,
            c.messageCount,
            COALESCE(o.avgMessageOtherCompanies, 0) AS avgMessageOtherCompanies
        FROM (
            SELECT 
                DATE(dateSent) AS day,
                COUNT(*) AS messageCount
            FROM STUDENTOUTREACH
            WHERE companyId = %s
            GROUP BY DATE(dateSent)
        ) c
        LEFT JOIN (
            SELECT 
                day,
                AVG(daily_count) AS avgMessageOtherCompanies
            FROM (
                SELECT 
                    companyId,
                    DATE(dateSent) AS day,
                    COUNT(*) AS daily_count
                FROM STUDENTOUTREACH
                WHERE companyId != %s
                GROUP BY companyId, DATE(dateSent)
            ) sub
            GROUP BY day
        ) o
        ON c.day = o.day
        ORDER BY c.day;
        """

        cursor.execute(query, (company_id, company_id))
        return jsonify(cursor.fetchall()), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()



# List all anonymized experience-reports
@employer.route("/experience_reports", methods=["GET"])
def get_experience_reports():
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
          """SELECT DISTINCT c.companyName, cr.title, ce.notes 
              FROM COMPANY c
              JOIN COOPROLE cr ON c.companyId = cr.companyId
              JOIN COOPEXPERIENCE ce ON ce.companyId = c.companyId""")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# List all roles for this company
@employer.route("/roles", methods=["GET"])
def get_roles():
    company_id = request.args.get("companyId", type=int)
    if company_id is None:
        return jsonify({"error": "companyId query parameter is required and must be an integer"}), 400

    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
          """SELECT DISTINCT cr.title
              FROM COMPANY c
              JOIN COOPROLE cr ON c.companyId = cr.companyId
              WHERE cr.companyId = %s""",
              (company_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()



#Create a new employer outreach message [Jackson - 1]
@employer.route("/roles/create", methods=["POST"])
def post_new_role():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()

        required_fields = ["companyId", "title", "department", "salary", "duration"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        query = """
            INSERT INTO EMPLOYEROUTREACH (companyId, title, department, salary, duration)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["companyId"],
            data["title"],
            data["department"],
            data["salary"],
            data["duration"]
        ))

        get_db().commit()
        return jsonify({"message": "Role created successfully", "roleId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()




