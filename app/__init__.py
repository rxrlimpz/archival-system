from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.exceptions import HTTPException
from flask_login import LoginManager, login_required, current_user, AnonymousUserMixin
from flask_argon2 import Argon2
from flask_session_captcha import FlaskSessionCaptcha
from werkzeug.exceptions import HTTPException
from datetime import timedelta
import os

from app.secure.login_form import LoginForm
from app.database import config
from app.secure.user_logs import updateDB
from app.dynamic.source_updater import updater
from app.dynamic.settings import json_data_selector
from app.routes.admin import admin_bp
from app.routes.staff import staff_bp
from app.blueprints.account_manager import account_manager
from app.blueprints.college_manager import college_manager
from app.blueprints.dashboard import dashboard_data
from app.blueprints.documents import fetch_documents
from app.blueprints.profile import profile_data
from app.blueprints.records import fetch_records
from app.blueprints.trashbin import trashbin_data
from app.blueprints.upload_manager import uploader_manager
from app.blueprints.ocr_app import ocr_App
from app.blueprints.benchmark_manager import benchmark_manager


# Create Flask app
app = Flask(__name__, static_folder='static')
app.config.from_object('config.Config')

app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 6
app.config['CAPTCHA_WIDTH'] = 180
app.config['CAPTCHA_HEIGHT'] = 60
captcha = FlaskSessionCaptcha(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.refresh_view = 'index'
login_manager.login_view = 'auth.login'

csrf = CSRFProtect()
csrf.init_app(app)
argon2 = Argon2(app)

app.config['UPLOAD_FOLDER'] = os.path.realpath('app/upload_folder')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.role = 'Anonymous'

login_manager.anonymous_user = Anonymous

#Register authentication logic
from app.secure.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)
#Register ocr logic
app.register_blueprint(ocr_App)
#Reister authenticated accounts
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(account_manager)
app.register_blueprint(college_manager)
app.register_blueprint(dashboard_data)
app.register_blueprint(fetch_documents)
app.register_blueprint(profile_data)
app.register_blueprint(fetch_records)
app.register_blueprint(trashbin_data)
app.register_blueprint(uploader_manager)
app.register_blueprint(benchmark_manager)

@app.route('/fetch_selector/<selector>' , methods=['GET'])
def fetchSource(selector):
    return jsonify(json_data_selector(selector, "settings.json"))

@app.route('/fetch_toast/<selector>' , methods=['GET'])
def fetchToast(selector):
    return jsonify(json_data_selector(selector, "toast.json"))

#Non-authentication needed pages
@app.route('/ards/')
def index():
    return redirect(url_for('home'))

@app.route('/ards')
def home():
    form = LoginForm()

    return render_template('public/index.html', form=form)

#Account page route
@app.route('/account')
@login_required
def account():
    updateDB()
    redirect_url = {'admin': 'admin.account', 'staff': 'staff.account'}.get(current_user.role)
    return redirect(url_for(redirect_url, user = current_user.username))

#Records page route
@app.route('/records')
@login_required
def records():
    redirect_url = {'admin': 'admin.records', 'staff': 'staff.records'}.get(current_user.role)
    return redirect(url_for(redirect_url))

#Documents page route
@app.route('/documents')
@login_required
def documents():
    redirect_url = {'admin': 'admin.documents', 'staff': 'staff.documents'}.get(current_user.role)
    return redirect(url_for(redirect_url))

#Upload page route
@app.route('/upload')
@login_required
def upload():
    return redirect(url_for('staff.upload'))

#Dashboard page route
@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('admin.dashboard'))

#Dashboard page route
@app.route('/trashbin')
@login_required
def trashbin():
    return redirect(url_for('admin.trashbin'))

#Account Manager page route
@app.route('/account_manager')
@login_required
def account_manager():
    return redirect(url_for('admin.account_manager'))

#Collage and Course Manager page route
@app.route('/col_course_manager')
@login_required
def col_course_manager():
    return redirect(url_for('admin.col_course_manager'))

#Collage and Course Manager page route
@app.route('/benchmark')
@login_required
def benchmarker():
    return redirect(url_for('admin.benchmarker'))

#refresh session
@app.before_request
def update_Session():
    if request.endpoint and request.endpoint != "auth.heartbeat":
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)
        checkConnection()

#check mySQL server connection and reconnection when die
def checkConnection():
    try:
        if not config.conn.open:
            print("Connection is closed. Reconnect or establish a new connection.")
            config.conn.ping(reconnect=True)
            
    except Exception as e:
        print(f"Failed to reconnect: {e}")

#error handling of pages
@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    print('ERROR HANDLER: ',e)

    if isinstance(e, CSRFError):
        code = e.code
        name = "Invalid Token"
        code_message = f"{code} {name}"
        description = "The form token provided is invalid. Please ensure you are using the correct token and try again."
    
    elif isinstance(e, HTTPException):
        code = e.code
        code_message = f"{code} {e.name}"
        description = e.description
    else:
        code_message = "Internal Server Error"
        description = 'The server has encountered an unexpected condition or configuration problem that prevents it from fulfilling the request made by the browser or client.'
        
    return render_template('errors/error.html', error_number=code_message, error_message=description), code