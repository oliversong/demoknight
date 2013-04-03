"""
    Demoknight
    ~~~~~~~~~~

    Scoping, load balancing tasks

"""
from __future__ import with_statement
import time, os, sys, json
from flask import Flask, render_template, request, redirect, url_for, abort, g, flash, escape, session, make_response
from werkzeug import check_password_hash, generate_password_hash
from datetime import datetime, tzinfo, timedelta
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.datastructures import CallbackDict
import parsedatetime.parsedatetime as pdt

# make app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# config
DEBUG = True
SECRET_KEY = "devopsborat"

# local configs
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/demoknightdb'

# EC2
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hello:shoopdawoop@localhost/rocketjumpdb'

app.config['DEBUG'] = DEBUG
app.config['SECRET_KEY'] = SECRET_KEY
db = SQLAlchemy(app)

# Database things

def initdb():
    db.drop_all()
    db.create_all()
    db.session.commit()

def get_user_id(email):
    print 'getting user id'
    user = db.session.query(User).filter(User.email==email).first()
    if user:
        print 'already a user'
        return user.id
    else:
        print 'no such user'
        return None

# Objects and Relationships

# A task can have many categories, and a category can have many tasks
taskTable = db.Table('taskTable',
    db.Column('task.id', db.Integer, db.ForeignKey('tasks.id')),
    db.Column('category.id', db.Integer, db.ForeignKey('categories.id'))
    )

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(80))
    lname = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    just_created = db.Column(db.Boolean, default=True)
    categories = db.relationship('Category', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def __init__(self, fname, lname, email, password):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    color = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tasks = db.relationship('Task', secondary=taskTable, backref=db.backref('categories', lazy='dynamic'))

    def __init__(self, name, color, user):
        self.name = name
        self.color = color
        self.user = user

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    completed = db.Column(db.Boolean, default=False)
    dueday = db.Column(db.String(120))
    duetime = db.Column(db.String(80))
    estimate = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plandate = db.Column(db.String(120))

    def __init__(self, name, dueday, duetime, estimate):
        self.name = name
        self.dueday = dueday
        self.duetime = duetime
        self.estimate = estimate

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    if 'userid' not in session:
        flash('Please sign in.')
        return redirect(url_for('index'))
    return render_template('settings.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user: 
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        user = db.session.query(User).filter(User.email==request.form['email']).first()
        if not user:
            error = 'Invalid email or password'
        elif not user.check_password(request.form['password']):
            error = 'Invalid email or password'
        else:
            flash('You were logged in')
            session['userid'] = user.id
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('userid', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if g.user:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        if not request.form['email'] or '@' not in request.form['email']:
            error = 'You must enter a valid email addresss'
        elif not request.form['fname'] or not request.form['lname']:
            error = 'You must enter a name'
        elif not request.form['password']:
            error = 'You must enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'Your passwords do not match'
        elif get_user_id(request.form['email']) is not None:
            error = 'That email is already taken'
        else:
            print 'adding new user'
            new_user = User(request.form['fname'],request.form['lname'],request.form['email'],request.form['password'])
            db.session.add(new_user)
            db.session.commit()
            session['userid'] = new_user.id
            print 'redirecting'
            return redirect(url_for('home'))
    return render_template('signup.html', error=error)

@app.route('/home')
def home():
    if not g.user:
        flash('Please sign in')
        return redirect(url_for('login'))
    # get two weeks worth of tasks
    tasks = g.user.tasks.all().filter
    categories = g.user.categories.all()
    return render_template('home.html', categories=categories, tasks=tasks)

@app.route('/addtask', methods=['POST'])
def parsetask():
    if not g.user:
        abort(404)
    else:
        unparsed = request.form['new_task']
        # parse the input to get name, dueday, duetime, estimate
        # 6.033 pset due next friday at 10pm should take about 3 hours
        # 6.033 pset due friday 10pm 3hr

        # right now doing a primitive version, TODO: use Hamming distance or classifiers / HMM to get true accuracy / robustness
        # keywords: before due, after due, after at, before hours
        split_up = unparsed.split()
        due_index = unparsed.index('due')
        at_index = unparsed.index('at')
        hours_index = unparsed.index('hours')
        errors = []

        # STRING
        name = ' '.join(split_up[:due_index])
        if not name:
            errors.append('No task name found')

        # STRING that must be parsed in to a unix timestamp not including day
        day_string = ' '.join(split_up[due_index:at_index])
        cal = pdt.Calendar()
        due_day = cal.parse(day_string)
        if due_day[1] == 0 or due_day[1] == 2:
            errors.append('No due day found')
        elif due_day[1] == 1 or due_day[1] == 3:
            due_day = time.mktime(datetime(due_day[0].tm_year,due_day[0].tm_mon,due_day[0].tm_mday).timetuple())

        # STRING that must be parsed in to a number of milliseconds
        time_string = split_up[at_index+1]
        due_time = cal.parse(time_string)
        if due_time[1] == 2:
            #good
            due_time = time.mktime(datetime(due_time[0].tm_hour))
        else:
            # no time string, this is okay
            due_time = None 

        # STRING that must be parsed in to a number of milliseconds
        estimate = split_up[hours_index-1]

        # make/add new Task
        task = Task(name, due_day, due_time, estimate)
        g.user.tasks.append(task)
        db.session.commit()
        return "Done"

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/robots.txt')
def robots():
    res = app.make_response('User-agent: *\nAllow: /')
    res.mimetype = 'text/plain'
    return res

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)

@app.before_request
def before_request():
    g.user = None
    if 'userid' in session:
        try:
            g.user = db.session.query(User).from_statement(
                "SELECT * FROM users where id=:user_id").\
                params(user_id=session['userid']).first()
        except:
            session.pop('userid', None)

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)