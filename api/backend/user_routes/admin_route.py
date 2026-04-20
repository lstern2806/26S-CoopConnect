from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from mysql.connector import Error

admin = Blueprint("admin", __name__)
DEFAULT_ADMIN_ID = 1
ALLOWED_ACCOUNT_STATUSES = ["active", "suspended"]
ALLOWED_ACCESS_ROLES = ["STUDENT", "ADVISOR", "EMPLOYER"]


def add_audit_log(admin_id, action_type, details, record):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO AUDITLOG (adminId, actionType, actionDetails, affectedRecord, actionTimestamp)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (admin_id, action_type, details, record),
        )
    finally:
        cursor.close()


def user_exists(cursor, user_id):
    cursor.execute("SELECT userId FROM `USER` WHERE userId = %s", (user_id,))
    return cursor.fetchone() is not None


def setting_exists(cursor, setting_id):
    cursor.execute("SELECT settingId FROM SYSTEMSETTING WHERE settingId = %s", (setting_id,))
    return cursor.fetchone() is not None


def role_counts(cursor, user_id):
    cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM ADMIN WHERE userId = %s) AS admin_rows,
            (SELECT COUNT(*) FROM ADVISOR WHERE userId = %s) AS advisor_rows,
            (SELECT COUNT(*) FROM STUDENT WHERE userId = %s) AS student_rows,
            (SELECT COUNT(*) FROM EMPLOYER WHERE userId = %s) AS employer_rows
        """,
        (user_id, user_id, user_id, user_id),
    )
    return cursor.fetchone()


@admin.route("/users", methods=["GET"])
def get_all_users():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/users")
        status, search = request.args.get("status"), request.args.get("q")
        uid_filter = request.args.get("userId")
        query = """
            SELECT u.userId, u.firstName, u.lastName, u.email, u.accountStatus,
                   CONCAT_WS(', ',
                       IF(a.adminId IS NOT NULL, 'ADMIN', NULL),
                       IF(ad.advisorId IS NOT NULL, 'ADVISOR', NULL),
                       IF(s.studentId IS NOT NULL, 'STUDENT', NULL),
                       IF(e.employerId IS NOT NULL, 'EMPLOYER', NULL)
                   ) AS roles
            FROM `USER` u
            LEFT JOIN ADMIN a ON u.userId = a.userId
            LEFT JOIN ADVISOR ad ON u.userId = ad.userId
            LEFT JOIN STUDENT s ON u.userId = s.userId
            LEFT JOIN EMPLOYER e ON u.userId = e.userId
            WHERE 1=1
        """
        params = []
        if uid_filter is not None and str(uid_filter).strip() != "":
            try:
                uid_val = int(uid_filter)
            except (TypeError, ValueError):
                return jsonify({"error": "userId must be a positive integer"}), 400
            if uid_val < 1:
                return jsonify({"error": "userId must be a positive integer"}), 400
            query += " AND u.userId = %s"
            params.append(uid_val)
        if status:
            query += " AND u.accountStatus = %s"
            params.append(status)
        if search:
            like = f"%{search}%"
            query += " AND (u.firstName LIKE %s OR u.lastName LIKE %s OR u.email LIKE %s)"
            params.extend([like, like, like])
        query += " ORDER BY u.userId"
        cursor.execute(query, params)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"GET /admin/users/{user_id}")
        cursor.execute(
            """
            SELECT u.userId, u.firstName, u.lastName, u.email, u.accountStatus,
                   CONCAT_WS(', ',
                       IF(a.adminId IS NOT NULL, 'ADMIN', NULL),
                       IF(ad.advisorId IS NOT NULL, 'ADVISOR', NULL),
                       IF(s.studentId IS NOT NULL, 'STUDENT', NULL),
                       IF(e.employerId IS NOT NULL, 'EMPLOYER', NULL)
                   ) AS roles
            FROM `USER` u
            LEFT JOIN ADMIN a ON u.userId = a.userId
            LEFT JOIN ADVISOR ad ON u.userId = ad.userId
            LEFT JOIN STUDENT s ON u.userId = s.userId
            LEFT JOIN EMPLOYER e ON u.userId = e.userId
            WHERE u.userId = %s
            """,
            (user_id,),
        )
        user = cursor.fetchone()
        return (jsonify(user), 200) if user else (jsonify({"error": "User not found"}), 404)
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/users", methods=["POST"])
def create_user():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("POST /admin/users")
        data = request.get_json() or {}
        for field in ["firstName", "lastName", "email", "password"]:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        status = data.get("accountStatus", "active")
        if status not in ALLOWED_ACCOUNT_STATUSES:
            return jsonify({"error": f"accountStatus must be one of: {ALLOWED_ACCOUNT_STATUSES}"}), 400
        cursor.execute("SELECT userId FROM `USER` WHERE email = %s", (data["email"],))
        if cursor.fetchone():
            return jsonify({"error": "A user with that email already exists"}), 409
        cursor.execute(
            "INSERT INTO `USER` (firstName, lastName, email, password, accountStatus) VALUES (%s, %s, %s, %s, %s)",
            (data["firstName"], data["lastName"], data["email"], data["password"], status),
        )
        user_id = cursor.lastrowid
        add_audit_log(data.get("adminId", DEFAULT_ADMIN_ID), "INSERT", f"Created user account for {data['email']}", f"USER:{user_id}")
        get_db().commit()
        return jsonify({"message": "User created successfully", "userId": user_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"PUT /admin/users/{user_id}")
        data = request.get_json() or {}
        if not user_exists(cursor, user_id):
            return jsonify({"error": "User not found"}), 404
        if data.get("accountStatus") and data["accountStatus"] not in ALLOWED_ACCOUNT_STATUSES:
            return jsonify({"error": f"accountStatus must be one of: {ALLOWED_ACCOUNT_STATUSES}"}), 400
        if data.get("email"):
            cursor.execute("SELECT userId FROM `USER` WHERE email = %s AND userId <> %s", (data["email"], user_id))
            if cursor.fetchone():
                return jsonify({"error": "Another user already has that email"}), 409
        fields = [f"{k} = %s" for k in ["firstName", "lastName", "email", "password", "accountStatus"] if k in data]
        params = [data[k] for k in ["firstName", "lastName", "email", "password", "accountStatus"] if k in data]
        if not fields:
            return jsonify({"error": "No valid fields to update"}), 400
        cursor.execute(f"UPDATE `USER` SET {', '.join(fields)} WHERE userId = %s", params + [user_id])
        add_audit_log(data.get("adminId", DEFAULT_ADMIN_ID), "UPDATE", f"Updated user account {user_id}", f"USER:{user_id}")
        get_db().commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"DELETE /admin/users/{user_id}")
        if not user_exists(cursor, user_id):
            return jsonify({"error": "User not found"}), 404
        counts = role_counts(cursor, user_id)
        if any(counts[k] > 0 for k in counts):
            return jsonify({"error": "Cannot delete user while subtype access rows still exist", "roleCounts": counts}), 409
        cursor.execute("DELETE FROM `USER` WHERE userId = %s", (user_id,))
        add_audit_log(request.args.get("adminId", DEFAULT_ADMIN_ID), "DELETE", f"Deleted user account {user_id}", f"USER:{user_id}")
        get_db().commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/users/<int:user_id>/status", methods=["GET", "PUT"])
def user_status(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"{request.method} /admin/users/{user_id}/status")
        if not user_exists(cursor, user_id):
            return jsonify({"error": "User not found"}), 404
        if request.method == "GET":
            cursor.execute("SELECT userId, accountStatus FROM `USER` WHERE userId = %s", (user_id,))
            return jsonify(cursor.fetchone()), 200
        data = request.get_json() or {}
        if data.get("accountStatus") not in ALLOWED_ACCOUNT_STATUSES:
            return jsonify({"error": f"accountStatus must be one of: {ALLOWED_ACCOUNT_STATUSES}"}), 400
        cursor.execute("UPDATE `USER` SET accountStatus = %s WHERE userId = %s", (data["accountStatus"], user_id))
        add_audit_log(data.get("adminId", DEFAULT_ADMIN_ID), "UPDATE", f"Updated accountStatus for user {user_id} to {data['accountStatus']}", f"USER:{user_id}")
        get_db().commit()
        return jsonify({"message": "User status updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/users/<int:user_id>/access", methods=["GET", "POST", "PUT", "DELETE"])
def user_access(user_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"{request.method} /admin/users/{user_id}/access")
        if not user_exists(cursor, user_id):
            return jsonify({"error": "User not found"}), 404
        if request.method == "GET":
            result = {"userId": user_id}
            for table, cols, key in [("ADMIN", "adminId, userId, lastLogin", "admin"), ("ADVISOR", "advisorId, userId, department", "advisor"), ("STUDENT", "studentId, userId, advisorId, major, GPA, gradYear", "student"), ("EMPLOYER", "employerId, userId, companyId, jobTitle", "employer")]:
                cursor.execute(f"SELECT {cols} FROM {table} WHERE userId = %s LIMIT 1", (user_id,))
                result[key] = cursor.fetchone()
            return jsonify(result), 200

        data = request.get_json() or {}
        role_type = (data.get("roleType") or request.args.get("roleType", "")).upper()
        if role_type not in ALLOWED_ACCESS_ROLES:
            return jsonify({"error": f"roleType must be one of: {ALLOWED_ACCESS_ROLES}"}), 400

        if request.method == "POST":
            counts = role_counts(cursor, user_id)
            if any(counts[k] > 0 for k in counts):
                return jsonify({"error": "User already has a system access assignment"}), 409
            if role_type == "ADVISOR":
                cursor.execute("INSERT INTO ADVISOR (userId, department) VALUES (%s, %s)", (user_id, data.get("department")))
            elif role_type == "STUDENT":
                cursor.execute("INSERT INTO STUDENT (userId, advisorId, major, GPA, gradYear) VALUES (%s, %s, %s, %s, %s)", (user_id, data.get("advisorId"), data.get("major"), data.get("GPA"), data.get("gradYear")))
            else:
                if not data.get("companyId"):
                    return jsonify({"error": "Missing required field: companyId"}), 400
                cursor.execute("INSERT INTO EMPLOYER (userId, companyId, jobTitle) VALUES (%s, %s, %s)", (user_id, data["companyId"], data.get("jobTitle")))
            action, msg = "INSERT", f"{role_type} access assigned successfully"

        elif request.method == "PUT":
            if role_type == "ADVISOR":
                if "department" not in data:
                    return jsonify({"error": "Missing required field: department"}), 400
                cursor.execute("UPDATE ADVISOR SET department = %s WHERE userId = %s", (data["department"], user_id))
            else:
                allowed = ["advisorId", "major", "GPA", "gradYear"] if role_type == "STUDENT" else ["companyId", "jobTitle"]
                fields = [f"{k} = %s" for k in allowed if k in data]
                params = [data[k] for k in allowed if k in data]
                if not fields:
                    return jsonify({"error": f"No valid {role_type} fields to update"}), 400
                table = "STUDENT" if role_type == "STUDENT" else "EMPLOYER"
                cursor.execute(f"UPDATE {table} SET {', '.join(fields)} WHERE userId = %s", params + [user_id])
            if cursor.rowcount == 0:
                return jsonify({"error": f"User does not currently have {role_type} access"}), 404
            action, msg = "UPDATE", f"{role_type} access updated successfully"

        else:
            table = {"STUDENT": "STUDENT", "ADVISOR": "ADVISOR", "EMPLOYER": "EMPLOYER"}[role_type]
            cursor.execute(f"DELETE FROM {table} WHERE userId = %s", (user_id,))
            if cursor.rowcount == 0:
                return jsonify({"error": f"User does not currently have {role_type} access"}), 404
            action, msg = "DELETE", f"{role_type} access removed successfully"

        add_audit_log(data.get("adminId", DEFAULT_ADMIN_ID), action, f"{action.title()} {role_type} access for user {user_id}", f"ACCESS:{user_id}")
        get_db().commit()
        return jsonify({"message": msg}), 200 if request.method != "POST" else 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/system-settings", methods=["GET", "POST"])
def system_settings():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"{request.method} /admin/system-settings")
        if request.method == "GET":
            cursor.execute("SELECT settingId, updatedBy, settingName, settingValue, settingDescription, updatedAt FROM SYSTEMSETTING ORDER BY settingId")
            return jsonify(cursor.fetchall()), 200
        data = request.get_json() or {}
        if not data.get("settingName"):
            return jsonify({"error": "Missing required field: settingName"}), 400
        cursor.execute("SELECT settingId FROM SYSTEMSETTING WHERE settingName = %s", (data["settingName"],))
        if cursor.fetchone():
            return jsonify({"error": "A setting with that name already exists"}), 409
        cursor.execute("INSERT INTO SYSTEMSETTING (updatedBy, settingName, settingValue, settingDescription, updatedAt) VALUES (%s, %s, %s, %s, NOW())", (data.get("updatedBy", DEFAULT_ADMIN_ID), data["settingName"], data.get("settingValue"), data.get("settingDescription")))
        setting_id = cursor.lastrowid
        add_audit_log(data.get("updatedBy", DEFAULT_ADMIN_ID), "INSERT", f"Created system setting {data['settingName']}", f"SYSTEMSETTING:{setting_id}")
        get_db().commit()
        return jsonify({"message": "System setting created successfully", "settingId": setting_id}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/system-settings/<int:setting_id>", methods=["GET", "PUT", "DELETE"])
def system_setting(setting_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info(f"{request.method} /admin/system-settings/{setting_id}")
        if not setting_exists(cursor, setting_id):
            return jsonify({"error": "System setting not found"}), 404
        if request.method == "GET":
            cursor.execute("SELECT * FROM SYSTEMSETTING WHERE settingId = %s", (setting_id,))
            return jsonify(cursor.fetchone()), 200
        if request.method == "DELETE":
            cursor.execute("SELECT settingName FROM SYSTEMSETTING WHERE settingId = %s", (setting_id,))
            setting = cursor.fetchone()
            cursor.execute("DELETE FROM SYSTEMSETTING WHERE settingId = %s", (setting_id,))
            add_audit_log(request.args.get("adminId", DEFAULT_ADMIN_ID), "DELETE", f"Deleted system setting {setting['settingName']}", f"SYSTEMSETTING:{setting_id}")
            get_db().commit()
            return jsonify({"message": "System setting deleted successfully"}), 200
        data = request.get_json() or {}
        fields = [f"{k} = %s" for k in ["settingName", "settingValue", "settingDescription"] if k in data]
        params = [data[k] for k in ["settingName", "settingValue", "settingDescription"] if k in data]
        if not fields:
            return jsonify({"error": "No valid fields to update"}), 400
        cursor.execute(f"UPDATE SYSTEMSETTING SET updatedBy = %s, updatedAt = NOW(), {', '.join(fields)} WHERE settingId = %s", [data.get("updatedBy", DEFAULT_ADMIN_ID)] + params + [setting_id])
        add_audit_log(data.get("updatedBy", DEFAULT_ADMIN_ID), "UPDATE", f"Updated system setting {setting_id}", f"SYSTEMSETTING:{setting_id}")
        get_db().commit()
        return jsonify({"message": "System setting updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/audit-logs")
        cursor.execute("SELECT logId, adminId, actionType, actionDetails, affectedRecord, actionTimestamp FROM AUDITLOG ORDER BY actionTimestamp DESC, logId DESC")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/audit-logs/summary", methods=["GET"])
def get_audit_log_summary():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/audit-logs/summary")
        cursor.execute("SELECT actionType, COUNT(*) AS totalActions FROM AUDITLOG GROUP BY actionType ORDER BY totalActions DESC, actionType")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/integrity/user-role-conflicts", methods=["GET"])
def get_user_role_conflicts():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/integrity/user-role-conflicts")
        cursor.execute(
            """
            SELECT u.userId, u.firstName, u.lastName, u.email,
                   CONCAT_WS(', ',
                       IF(a.adminId IS NOT NULL, 'ADMIN', NULL),
                       IF(ad.advisorId IS NOT NULL, 'ADVISOR', NULL),
                       IF(s.studentId IS NOT NULL, 'STUDENT', NULL),
                       IF(e.employerId IS NOT NULL, 'EMPLOYER', NULL)
                   ) AS roles,
                   (IF(a.adminId IS NOT NULL, 1, 0) + IF(ad.advisorId IS NOT NULL, 1, 0) + IF(s.studentId IS NOT NULL, 1, 0) + IF(e.employerId IS NOT NULL, 1, 0)) AS role_count
            FROM `USER` u
            LEFT JOIN ADMIN a ON u.userId = a.userId
            LEFT JOIN ADVISOR ad ON u.userId = ad.userId
            LEFT JOIN STUDENT s ON u.userId = s.userId
            LEFT JOIN EMPLOYER e ON u.userId = e.userId
            HAVING role_count <> 1 ORDER BY u.userId
            """
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/dashboards/admin-kpis", methods=["GET"])
def get_admin_kpis():
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/dashboards/admin-kpis")
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM `USER`) AS totalUsers,
                (SELECT COUNT(*) FROM `USER` WHERE accountStatus = 'active') AS activeUsers,
                (SELECT COUNT(*) FROM `USER` WHERE accountStatus = 'suspended') AS suspendedUsers,
                (SELECT COUNT(*) FROM ADVISOR) AS totalAdvisors,
                (SELECT COUNT(*) FROM STUDENT) AS totalStudents,
                (SELECT COUNT(*) FROM EMPLOYER) AS totalEmployers,
                (SELECT COUNT(*) FROM AUDITLOG) AS totalAuditLogs,
                (SELECT COUNT(*) FROM SYSTEMSETTING) AS totalSystemSettings
            """
        )
        return jsonify(cursor.fetchone()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/dashboards/audit-activity", methods=["GET"])
def get_audit_activity():
    """Audit log counts per calendar day for the last 30 days (for dashboard charts)."""
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/dashboards/audit-activity")
        cursor.execute(
            """
            SELECT DATE(actionTimestamp) AS activityDate, COUNT(*) AS cnt
            FROM AUDITLOG
            WHERE actionTimestamp >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(actionTimestamp)
            ORDER BY activityDate
            """
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@admin.route("/dashboards/student-stats", methods=["GET"])
def get_student_stats():
    """GPA buckets and graduation year counts for admin dashboard charts."""
    cursor = get_db().cursor(dictionary=True)
    try:
        current_app.logger.info("GET /admin/dashboards/student-stats")
        cursor.execute(
            """
            SELECT bucket AS gpaBucket, COUNT(*) AS studentCount
            FROM (
                SELECT
                    CASE
                        WHEN GPA IS NULL THEN 'Unknown'
                        WHEN GPA < 2.0 THEN '< 2.0'
                        WHEN GPA < 2.5 THEN '2.0-2.49'
                        WHEN GPA < 3.0 THEN '2.5-2.99'
                        WHEN GPA < 3.5 THEN '3.0-3.49'
                        ELSE '3.5-4.0'
                    END AS bucket
                FROM STUDENT
            ) AS GPABuckets
            GROUP BY bucket
            ORDER BY FIELD(
                bucket,
                '< 2.0', '2.0-2.49', '2.5-2.99', '3.0-3.49', '3.5-4.0', 'Unknown'
            )
            """
        )
        gpa_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT gradYear AS gradYear, COUNT(*) AS studentCount
            FROM STUDENT
            GROUP BY gradYear
            ORDER BY gradYear
            """
        )
        year_rows = cursor.fetchall()
        return jsonify({"gpaDistribution": gpa_rows, "gradYearDistribution": year_rows}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
