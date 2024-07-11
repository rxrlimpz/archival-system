from flask import Flask, render_template, redirect, url_for, session, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import HTTPException
from flask_login import LoginManager, login_required, current_user, AnonymousUserMixin
from flask_argon2 import Argon2
from flask_session_captcha import FlaskSessionCaptcha
from werkzeug.exceptions import HTTPException
from .forms import LoginForm
from . import config
from app.Blueprints.admin import admin_bp
from app.Blueprints.staff import staff_bp
from datetime import timedelta
import os

# Create Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = "ABCDEFG12345"
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["SESSION_COOKIE_SAMESITE"] = "strict"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
app.config["REMEMBER_COOKIE_SECURE"] = True
app.config['REMEMBER_COOKIE_DURATION'] =  timedelta(days=1)

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

@app.before_request
def update_Session():
    if request.endpoint and request.endpoint != "auth.heartbeat":
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)
        checkConnection()

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
    error_message = '500 Internal Server Error'
    description = 'The server has encountered an unexpected condition or configuration problem that prevents it from fulfilling the request made by the browser or client.'
    print(e)
    if isinstance(e, HTTPException):
        code = e.code
        code_message = f"{code} {e.name}"
        description = e.description
    else:
        code_message = "500 Internal Server Error"
        description = str(e)
        
    return render_template('errors/error.html', error_number=code_message, error_message=description), code

#Register authentication logic
from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)
#Register fetch datatable source logic
from .records import fetch_records as records_blueprint
app.register_blueprint(records_blueprint)
#Register fetch datatable source logic
from .documents import fetch_documents as documents_blueprint
app.register_blueprint(documents_blueprint)
#text recognition logics
from .ocr_app import ocr_App as ocr_blueprint
app.register_blueprint(ocr_blueprint)
#Register get colleges list
from .fetchColleges import fetchColleges as fetchCollegesBlueprint
app.register_blueprint(fetchCollegesBlueprint)
#Register account profile
from .profile import profile_data as proifileBlueprint
app.register_blueprint(proifileBlueprint)
#upload manager logics
from .upload_manager import uploader_manager as uploader_blueprint
app.register_blueprint(uploader_blueprint)
#Register Dashboard
from .dashboard import dashboard_data as dashboard_dateblueprint
app.register_blueprint(dashboard_dateblueprint)
#Register account_manager
from .account_manager import account_manager as user_controlblueprint
app.register_blueprint(user_controlblueprint)
#Register college and courses manager 
from .college_manager import college_manager as college_managerBlueprint
app.register_blueprint(college_managerBlueprint)
from .trashbin import trashbin_data as trashbinBlueprint
app.register_blueprint(trashbinBlueprint)
#Reister authenticated accounts
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)

#Non-authentication needed pages
@app.route('/ards/')
def index():
    return redirect(url_for('home'))

@app.route('/ards')
def home():
    form = LoginForm()
    return render_template('public/index.html', form=form)

#Role-based, authentication require pages
#Account page route
@app.route('/account')
@login_required
def account():
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
