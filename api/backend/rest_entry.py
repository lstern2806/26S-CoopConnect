from flask import Flask
from dotenv import load_dotenv
import os
import logging
from backend.db_connection import init_app as init_db
from backend.user_routes.student_routes import students
from backend.user_routes.employer_route import employer
from backend.user_routes.admin_route import admin
from backend.user_routes.advisor_route import advisor


def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('API startup')

    # Load environment variables from the .env file so they are
    # accessible via os.getenv() below.
    load_dotenv()

    # Secret key used by Flask for securely signing session cookies.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Database connection settings — values come from the .env file.
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    # Register the routes from each Blueprint with the app object
    # and give a url prefix to each.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(students, url_prefix="/stu")
    app.register_blueprint(employer, url_prefix="/emp")
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(advisor, url_prefix="/adv")

    return app
