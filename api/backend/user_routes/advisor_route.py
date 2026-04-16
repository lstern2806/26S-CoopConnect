from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

advisor_students = Blueprint("advisor_students", __name__)
advisor_networking = Blueprint("advisor_networking", __name__)
advisor_placements = Blueprint("advisor_placements", __name__)
advisor_dashboards = Blueprint("advisor_dashboards", __name__)

# =====================================================
# ADVISOR STUDENTS BLUEPRINT
# =====================================================

@advisor_students.route("/students", methods=["GET"])
def get_students():
    cursor = get_db().cursor(dictionary=True)
    try:
        major = request.args.get("major")
        experience_level = request.args.get("experience_level")
        previous_coop = request.args.get("previous_coop")

        query = """
            SELECT s.studentId, u.firstName, u.lastName, s.major, s.GPA, s.gradYear
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            WHERE 1=1
        """
        params = []

        if major:
            query += " AND s.major = %s"
            params.append(major)

        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_students.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT s.studentId, u.firstName, u.lastName, s.major, s.GPA, s.gradYear
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


@advisor_students.route("/students/filter", methods=["GET"])
def filter_students():
    cursor = get_db().cursor(dictionary=True)
    try:
        major = request.args.get("major")
        experience_level = request.args.get("experience_level")
        previous_coop = request.args.get("previous_coop")

        query = """
            SELECT s.studentId, u.firstName, u.lastName, s.major, s.GPA, s.gradYear
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            WHERE 1=1
        """
        params = []

        if major:
            query += " AND s.major = %s"
            params.append(major)

        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_students.route("/students", methods=["POST"])
def create_student():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        query = """
            INSERT INTO STUDENT (userId, major, GPA, gradYear)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["userId"],
            data.get("major"),
            data.get("GPA"),
            data.get("gradYear")
        ))
        get_db().commit()
        return jsonify({"message": "Student created successfully", "studentId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_students.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        allowed_fields = ["major", "GPA", "gradYear"]
        update_fields = [f"{field} = %s" for field in allowed_fields if field in data]
        params = [data[field] for field in allowed_fields if field in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(student_id)
        query = f"UPDATE STUDENT SET {', '.join(update_fields)} WHERE studentId = %s"
        cursor.execute(query, params)
        get_db().commit()

        return jsonify({"message": "Student updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# =====================================================
# ADVISOR NETWORKING BLUEPRINT
# =====================================================

@advisor_networking.route("/networking/activity", methods=["GET"])
def get_networking_activity():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT s.studentId, u.firstName, u.lastName,
                   COUNT(DISTINCT so.messageId) AS totalStudentOutreach,
                   COUNT(DISTINCT eo.empMessageId) AS totalEmployerResponses
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            LEFT JOIN STUDENTOUTREACH so ON s.studentId = so.senderId
            LEFT JOIN EMPLOYEROUTREACH eo ON s.studentId = eo.studentId
            GROUP BY s.studentId, u.firstName, u.lastName
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_networking.route("/networking/activity/<int:student_id>", methods=["GET"])
def get_student_networking_activity(student_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT s.studentId, u.firstName, u.lastName,
                   COUNT(DISTINCT so.messageId) AS totalStudentOutreach,
                   COUNT(DISTINCT eo.empMessageId) AS totalEmployerResponses
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            LEFT JOIN STUDENTOUTREACH so ON s.studentId = so.senderId
            LEFT JOIN EMPLOYEROUTREACH eo ON s.studentId = eo.studentId
            WHERE s.studentId = %s
            GROUP BY s.studentId, u.firstName, u.lastName
        """
        cursor.execute(query, (student_id,))
        result = cursor.fetchone()
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_networking.route("/networking/engagement", methods=["GET"])
def get_engagement_metrics():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT s.studentId, u.firstName, u.lastName,
                   COUNT(DISTINCT so.messageId) AS outreachSent,
                   COUNT(DISTINCT eo.empMessageId) AS employerMessages,
                   CASE
                       WHEN COUNT(DISTINCT so.messageId) = 0 THEN 0
                       ELSE ROUND(COUNT(DISTINCT eo.empMessageId) / COUNT(DISTINCT so.messageId), 2)
                   END AS responseRate
            FROM STUDENT s
            JOIN USER u ON s.userId = u.userId
            LEFT JOIN STUDENTOUTREACH so ON s.studentId = so.senderId
            LEFT JOIN EMPLOYEROUTREACH eo ON s.studentId = eo.studentId
            GROUP BY s.studentId, u.firstName, u.lastName
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_networking.route("/networking/outreach", methods=["POST"])
def create_outreach():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        query = """
            INSERT INTO STUDENTOUTREACH (senderId, recipientId, content)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            data["senderId"],
            data["recipientId"],
            data.get("content")
        ))
        get_db().commit()
        return jsonify({"message": "Outreach created successfully", "messageId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_networking.route("/networking/outreach/<int:message_id>", methods=["DELETE"])
def delete_outreach(message_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM STUDENTOUTREACH WHERE messageId = %s", (message_id,))
        get_db().commit()
        return jsonify({"message": "Outreach deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# =====================================================
# ADVISOR PLACEMENTS BLUEPRINT
# =====================================================

@advisor_placements.route("/placements", methods=["GET"])
def get_placements():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT ce.experienceId, ce.studentId, ce.companyId, c.companyName, c.industry
            FROM COOPEXPERIENCE ce
            JOIN COMPANY c ON ce.companyId = c.companyId
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_placements.route("/placements/trends", methods=["GET"])
def get_placement_trends():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT c.companyName, c.industry, COUNT(ce.experienceId) AS totalPlacements
            FROM COOPEXPERIENCE ce
            JOIN COMPANY c ON ce.companyId = c.companyId
            GROUP BY c.companyName, c.industry
            ORDER BY totalPlacements DESC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_placements.route("/placements/company/<int:company_id>", methods=["GET"])
def get_company_placements(company_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT ce.experienceId, ce.studentId, c.companyName, c.industry
            FROM COOPEXPERIENCE ce
            JOIN COMPANY c ON ce.companyId = c.companyId
            WHERE c.companyId = %s
        """
        cursor.execute(query, (company_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_placements.route("/placements", methods=["POST"])
def create_placement():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        query = """
            INSERT INTO COOPEXPERIENCE (studentId, companyId)
            VALUES (%s, %s)
        """
        cursor.execute((query), (
            data["studentId"],
            data["companyId"]
        ))
        get_db().commit()
        return jsonify({"message": "Placement created successfully", "experienceId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_placements.route("/placements/<int:experience_id>", methods=["PUT"])
def update_placement(experience_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        allowed_fields = ["studentId", "companyId"]
        update_fields = [f"{field} = %s" for field in allowed_fields if field in data]
        params = [data[field] for field in allowed_fields if field in data]

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(experience_id)
        query = f"UPDATE COOPEXPERIENCE SET {', '.join(update_fields)} WHERE experienceId = %s"
        cursor.execute(query, params)
        get_db().commit()
        return jsonify({"message": "Placement updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# =====================================================
# ADVISOR DASHBOARDS BLUEPRINT
# =====================================================

@advisor_dashboards.route("/dashboards/kpis", methods=["GET"])
def get_kpis():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT
                COUNT(DISTINCT s.studentId) AS totalStudents,
                COUNT(DISTINCT so.messageId) AS totalOutreach,
                COUNT(DISTINCT eo.empMessageId) AS totalResponses,
                COUNT(DISTINCT ce.experienceId) AS totalPlacements,
                CASE
                    WHEN COUNT(DISTINCT so.messageId) = 0 THEN 0
                    ELSE ROUND(COUNT(DISTINCT eo.empMessageId) / COUNT(DISTINCT so.messageId), 2)
                END AS responseRate
            FROM STUDENT s
            LEFT JOIN STUDENTOUTREACH so ON s.studentId = so.senderId
            LEFT JOIN EMPLOYEROUTREACH eo ON s.studentId = eo.studentId
            LEFT JOIN COOPEXPERIENCE ce ON s.studentId = ce.studentId
        """
        cursor.execute(query)
        return jsonify(cursor.fetchone()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_dashboards.route("/dashboards/performance", methods=["GET"])
def get_performance():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT c.industry,
                   COUNT(DISTINCT ce.experienceId) AS placements,
                   COUNT(DISTINCT ce.studentId) AS studentsPlaced
            FROM COOPEXPERIENCE ce
            JOIN COMPANY c ON ce.companyId = c.companyId
            GROUP BY c.industry
            ORDER BY placements DESC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_dashboards.route("/dashboards/reports/<int:advisor_id>", methods=["GET"])
def get_reports(advisor_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT reportId, advisorId, reportName, createdAt
            FROM ADVISORREPORT
            WHERE advisorId = %s
        """
        cursor.execute(query, (advisor_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_dashboards.route("/dashboards/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        query = "UPDATE ADVISORREPORT SET reportName = %s WHERE reportId = %s"
        cursor.execute(query, (data["reportName"], report_id))
        get_db().commit()
        return jsonify({"message": "Report updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_dashboards.route("/dashboards/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM ADVISORREPORT WHERE reportId = %s", (report_id,))
        get_db().commit()
        return jsonify({"message": "Report deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@advisor_dashboards.route("/dashboards/reports", methods=["POST"])
def create_report():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        query = """
            INSERT INTO ADVISORREPORT (advisorId, reportName, createdAt)
            VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (
            data["advisorId"],
            data["reportName"]
        ))
        get_db().commit()
        return jsonify({"message": "Report created successfully", "reportId": cursor.lastrowid}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
