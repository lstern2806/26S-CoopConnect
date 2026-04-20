from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

advisor = Blueprint("advisor", __name__)


# =====================================================
# STUDENTS
# =====================================================

# Return a list of students and profile attributes such as major, experience
# level, and previous co-op for filtering and advising
# [FinanceAdvisor-5], [Maya-2]
@advisor.route("/students", methods=["GET"])
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
        if experience_level:
            query += " AND s.experienceLevel = %s"
            params.append(experience_level)
        if previous_coop is not None:
            query += " AND s.previousCoop = %s"
            params.append(previous_coop)

        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Return detailed information for one student, including networking activity
# and outcomes
# [FinanceAdvisor-1], [FinanceAdvisor-3], [Maya-2], [Jackson-1]
@advisor.route("/students/<int:student_id>", methods=["GET"])
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


# Update student profile [Maya-4]
@advisor.route("/students/<int:student_id>", methods=["PUT"])
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
# NETWORKING ACTIVITY
# =====================================================

# Return aggregated networking activity across students, including outreach,
# responses, and engagement metrics
# [FinanceAdvisor-1], [FinanceAdvisor-3], [FinanceAdvisor-4]
@advisor.route("/networking-activity", methods=["GET"])
def get_networking_activity():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT s.studentId, u.firstName, u.lastName,
                   COUNT(DISTINCT so.messageId) AS totalStudentOutreach,
                   COUNT(DISTINCT eo.empMessageId) AS totalEmployerResponses,
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


# Return networking activity for a specific student to monitor engagement and
# identify students needing support [FinanceAdvisor-3]
@advisor.route("/networking-activity/<int:student_id>", methods=["GET"])
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
        if not result:
            return jsonify({"error": "Student not found"}), 404
        return jsonify(result), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# =====================================================
# PLACEMENTS
# =====================================================

# Return co-op placement records by student, company, and industry
# [FinanceAdvisor-1], [FinanceAdvisor-2], [FinanceAdvisor-6]
@advisor.route("/placements", methods=["GET"])
def get_placements():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT ce.experienceId, ce.studentId, ce.companyId,
                   c.companyName, c.industry
            FROM COOPEXPERIENCE ce
            JOIN COMPANY c ON ce.companyId = c.companyId
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Return trend data on successful co-op placements by company, industry, and
# time period [FinanceAdvisor-2], [FinanceAdvisor-6]
@advisor.route("/placements/trends", methods=["GET"])
def get_placement_trends():
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT c.companyName, c.industry,
                   COUNT(ce.experienceId) AS totalPlacements
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


# =====================================================
# DASHBOARDS
# =====================================================

# Return dashboard KPI data such as response rates, offer conversion rates,
# and engagement measures [FinanceAdvisor-4], [FinanceAdvisor-6]
@advisor.route("/dashboards/kpis", methods=["GET"])
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
                    WHEN COUNT(DISTINCT so.messageId) = 0 THEN 0.0
                    ELSE ROUND(COUNT(DISTINCT eo.empMessageId) * 1.0 / COUNT(DISTINCT so.messageId), 2)
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


# Return overall program performance metrics over time for reporting and
# improvement analysis [FinanceAdvisor-6]
@advisor.route("/dashboards/performance", methods=["GET"])
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


# =====================================================
# FILTERS
# =====================================================

# Return filtered student data based on major, experience level, or previous
# co-op [FinanceAdvisor-5]
@advisor.route("/filters/students", methods=["GET"])
def get_filtered_students():
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
        if experience_level:
            query += " AND s.experienceLevel = %s"
            params.append(experience_level)
        if previous_coop is not None:
            query += " AND s.previousCoop = %s"
            params.append(previous_coop)

        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Submit filter criteria for advanced analytics queries [FinanceAdvisor-5]
@advisor.route("/filters/students", methods=["POST"])
def post_filter_students():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json() or {}
        major = data.get("major")
        experience_level = data.get("experience_level")
        previous_coop = data.get("previous_coop")
        min_gpa = data.get("min_gpa")
        grad_year = data.get("gradYear")

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
        if experience_level:
            query += " AND s.experienceLevel = %s"
            params.append(experience_level)
        if previous_coop is not None:
            query += " AND s.previousCoop = %s"
            params.append(previous_coop)
        if min_gpa is not None:
            query += " AND s.GPA >= %s"
            params.append(min_gpa)
        if grad_year:
            query += " AND s.gradYear = %s"
            params.append(grad_year)

        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# =====================================================
# ADVISOR REPORTS
# =====================================================

# Return saved advisor reports on student outcomes, networking success, and
# program performance
# [FinanceAdvisor-1], [FinanceAdvisor-2], [FinanceAdvisor-6]
@advisor.route("/advisors/reports", methods=["GET"])
def get_reports():
    cursor = get_db().cursor(dictionary=True)
    try:
        advisor_id = request.args.get("advisorId", type=int)
        query = """
            SELECT reportId, advisorId, reportName, createdAt
            FROM ADVISORREPORT
        """
        params = []
        if advisor_id is not None:
            query += " WHERE advisorId = %s"
            params.append(advisor_id)
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Create a new custom report for advising or business school reporting
# [FinanceAdvisor-6]
@advisor.route("/advisors/reports", methods=["POST"])
def create_report():
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        required_fields = ["advisorId", "reportName"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        query = """
            INSERT INTO ADVISORREPORT (advisorId, reportName, createdAt)
            VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (data["advisorId"], data["reportName"]))
        get_db().commit()
        return jsonify({
            "message": "Report created successfully",
            "reportId": cursor.lastrowid
        }), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Update an existing saved report configuration [FinanceAdvisor-6]
@advisor.route("/advisors/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        data = request.get_json()
        if "reportName" not in data:
            return jsonify({"error": "Missing required field: reportName"}), 400
        query = "UPDATE ADVISORREPORT SET reportName = %s WHERE reportId = %s"
        cursor.execute(query, (data["reportName"], report_id))
        get_db().commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Report not found"}), 404
        return jsonify({"message": "Report updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


# Delete a saved report no longer needed [FinanceAdvisor-6]
@advisor.route("/advisors/reports/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):
    cursor = get_db().cursor()
    try:
        cursor.execute("DELETE FROM ADVISORREPORT WHERE reportId = %s", (report_id,))
        get_db().commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Report not found"}), 404
        return jsonify({"message": "Report deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
