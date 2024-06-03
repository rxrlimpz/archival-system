from flask import render_template, redirect, url_for, request, Blueprint, jsonify, session
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
import datetime
import socket
import httpagentparser
from device_detector import DeviceDetector
import hashlib
import secrets
import string
from . import config, login_manager, argon2, captcha 
from flask import current_app as app
from .forms import LoginForm

auth = Blueprint('auth', __name__)

logged_devices = []
blocklist = []
MAX_ATTEMPTS = 10
BLOCK_THRESHOLD = datetime.timedelta(hours=1) 

#generate id random character string
def generate_id(length=256):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))

#generate token based on data, key and key2 for session
def generate_token(data, key, key2):
    combined_data = str(data) + app.config['SECRET_KEY'] + key + key2
    hashed_data = hashlib.sha256(combined_data.encode()).hexdigest()
    return hashed_data

#verify the token and return true
def check_token(token, data, key, key2):
    expected_token = generate_token(data, key, key2)
    return token == expected_token

#generate device information of user
def getUserInfo():
    device_data = {'device': '', 'os': '', 'browser': '', 'ip_address': ''}
    ip_address = socket.gethostbyname(socket.gethostname())
    agent = request.headers.get('User-Agent')
    browser_info = httpagentparser.detect(agent)

    browser_name = browser_info.get('browser', {}).get('name', 'Unknown')
    device = DeviceDetector(agent).parse()
    deviceType= device.device_type()
    os = f"{device.os_name()} {device.os_version()}" 

    device_data = {'device': (deviceType), 'os': os, 'browser': browser_name, 'ip_address': ip_address}
    return device_data

#get the user from the array
def find_device(user):
    for device in logged_devices:
        if device['user'] == user:
            return device
    return None

#determine if user is blocked and remove if time exceeds the threshold
def is_blocked(user):
    current_time = datetime.datetime.now()
    existing_device = find_device(user)
    for device in blocklist:
        if device['user'] == user:
            if current_time - device['blocked_datetime'] < BLOCK_THRESHOLD:
                return True
            else:
                blocklist.remove(device)
                if existing_device:
                    existing_device['attempts'] = 0
                return False
    return False

#limit the unsuccessful login attempts request of an ip address 
def loginAttempt(action):
    user_info = getUserInfo()
    ipaddress = user_info['ip_address']
    user = hashlib.sha256(ipaddress.encode()).hexdigest()
    existing_device = find_device(user)
    
    if is_blocked(user):
        print( ipaddress," is currently blocked from making login attempts.")
    
    else:
        if action == 'reset':
            if existing_device:
                existing_device['attempts'] = 0
            else:
                logged_devices.append({'user': user, 'attempts': 0})

        elif action == 'count':
            if existing_device:
                existing_device['attempts'] += 1
                if existing_device['attempts'] >= MAX_ATTEMPTS:
                    if not any(device['user'] == user for device in blocklist):
                        blocklist.append({'user': user, 'blocked_datetime': datetime.datetime.now()})
            else:
                logged_devices.append({'user': user, 'attempts': 1})

#generate a user device information and append to the database login history
def loginHistory(user_id, session_data):
    with config.conn.cursor() as cursor:
        user_deviceInfo = getUserInfo()
        device = user_deviceInfo['device']
        browser = user_deviceInfo['browser']
        os = user_deviceInfo['os']
        ip_address = user_deviceInfo['ip_address']

        cursor.execute('SELECT * FROM login_history WHERE session_data = %s', (session_data,))
        current_history = cursor.fetchone()
     
        if not current_history:
            cursor.execute('INSERT INTO login_history(user_id, device, browser, os, ip_address, session_data) VALUES (%s, %s, %s, %s, %s, %s)',
                           (str(user_id), device, browser, os, ip_address, session_data))
            config.conn.commit()

#setup query to update database when user session expired
def session_expired(username):
    if username:
        with config.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM user WHERE username = %s AND online = 1', (username))
            userData = cursor.fetchone()

            if userData:
                cursor.execute('SELECT * FROM session WHERE username = %s AND online = 1', (username))
                sessionData = cursor.fetchone()

                if sessionData:
                    cursor.execute('DELETE FROM session WHERE username = %s', (username,))
                    config.conn.commit()
                else:
                    print('session user not found')
            else:
                print('session user not found')

#setup for user session
class User(UserMixin):
    def __init__(self, id, username, role, token):
        self.id = id
        self.username  = username
        self.role = role
        self.token = token

    #fetch user information based on input
    def get_User(self):
        with config.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM session WHERE session_id = %s', (self.id,))
            user_session = cursor.fetchone()

            if user_session:
                cursor.execute('SELECT * FROM user WHERE user_id = %s', (user_session['user_id'],))
                return cursor.fetchone()
            else:
                return None
            
    #verify user session token authentication           
    @property
    def is_authenticated(self):
        with config.conn.cursor() as cursor:
            user = self.get_User()
            if user and check_token(self.token, user['password'], user['pass_key'], self.id):
                cursor.execute('UPDATE user SET online = 1, last_online = NULL WHERE user_id = %s AND online = 0', (user['user_id'],))
                config.conn.commit()
                return True
            else:
                return False
            
    #verify if user account is not deactivated
    @property
    def is_active(self):
        user = self.get_User()
        if user and user['status'] == 1:
            return True
        else:
            return False
        
#load user account in session
@login_manager.user_loader
def load_user(session_id):
    try:
        with config.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM session WHERE session_id = %s', (session_id))
            search_session = cursor.fetchone()
           
            if search_session:
                cursor.execute('SELECT * FROM user WHERE user_id = %s', (search_session['user_id'],))
                user = cursor.fetchone()
                    
                if user:
                    token = generate_token(user['password'], user['pass_key'], session_id)
                    return User(session_id, search_session['username'], {1: 'admin', 2: 'staff'}.get(search_session['role']), token)
                else:
                    return None
            else:
                return None
            
    except Exception as e:
        print(f"login loader: {e}")

#login user
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    role = ''
    invalidError = 'User not Found or Invalid Password. Please Try Again!'
    captchaError = 'Please solve the captcha to verify you’re not a robot. Please Try Again!'
    attemptError = 'Excessive login attempts detected. Your account is temporarily blocked for 1 hour. Please try again later.'
    error = invalidError
    
    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        input_captcha = request.form.get('captcha')
        form.captcha.data = ''
        user_role = {'1': 'admin', '2': 'staff'}.get(role, 'error')
        role = int(role)
        
        user_info = getUserInfo()
        ipaddress = user_info['ip_address']
        device = hashlib.sha256(ipaddress.encode()).hexdigest()

        if is_blocked(device):
                error = attemptError
        else:
            with config.conn.cursor() as cursor:
                #Search for the user in the database
                cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
                user = cursor.fetchone()

                if captcha.get_answer() == input_captcha:#validate captcha input
                    if user and argon2.check_password_hash(user['password'], password) and user['status'] == 1:#authentication for login

                        cursor.execute('SELECT * FROM session WHERE user_id = %s', (user['user_id']))
                        session_data = cursor.fetchone()

                        if session_data and len(session_data['session_id']) == 256:
                            session_id = session_data['session_id']
                        else:
                            session_id = generate_id()
                            cursor.execute('INSERT INTO session(session_id, user_id, username, role) VALUES (%s,%s,%s,%s)', (session_id, user['user_id'], username, role))
                            config.conn.commit()
                            
                        if session_id:
                            #generate token for session creation on cookies
                            token = generate_token(user['password'], user['pass_key'], session_id)
                            login_user(User(session_id, username, user_role, token), remember=False)
                            loginHistory((user['user_id']), session_id)
                            loginAttempt('reset')
                            redirect_url = {1: 'admin.dashboard', 2: 'staff.records'}.get(user['role'], 'auth.logout')

                            if redirect_url:#redirect if user is authenicated and authorized
                                return redirect(url_for(redirect_url))
                            else:
                                error = invalidError
                        else:
                            error = invalidError
                    else:
                        error = invalidError
                else:
                    error = captchaError
    loginAttempt('count')           
    return render_template('public/index.html', error_message=error, role = role, form=form)

#logout user
@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if current_user:
        with config.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM session WHERE session_id = %s', (current_user.id,))
            user_session = cursor.fetchone()

            if user_session:
                cursor.execute('DELETE FROM session WHERE session_id = %s', (current_user.id,))
                config.conn.commit()
            else:
                print('Sign out error occurred')

            logout_user()
            session.clear()

    return redirect(url_for('home'))











#check for session timeout
@auth.route('/get_heartbeat/<username>', endpoint='heartbeat')
def heartbeat(username):
    if current_user:
        if current_user.is_authenticated and current_user.is_active:
            return jsonify(session_Inactive = False)
        else:
            print('timeout')
            if username:
                session_expired(username)
            return jsonify(session_Inactive = True)
    else:
        session_expired(username)
        return jsonify(session_Inactive = True)
    
#return to logout to prevent rendering expired csrf token
@auth.route('/authenticate-user/check-token/timeout/')
def user_timeout():
    return redirect(url_for('auth.logout'))


