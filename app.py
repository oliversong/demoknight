"""
    Demoknight
    ~~~~~~~~~~

    Scoping, load balancing tasks

"""
from __future__ import with_statement
import time, os, sys, json
from flask import Flask, render_template, request, redirect, url_for, abort, g, flash, escape, session, make_response, jsonify
from werkzeug import check_password_hash, generate_password_hash
from datetime import datetime, tzinfo, timedelta
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.datastructures import CallbackDict
import parsedatetime.parsedatetime as pdt
from copy import deepcopy

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
    due = db.Column(db.Integer)
    estimate = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    plan_dates = db.relationship("Plan_date", backref='task', lazy='dynamic') 

    def __init__(self, name, due, estimate):
        self.name = name
        self.due = due
        self.estimate = estimate

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id'        : self.id,
            'name'      : self.name,
            'completed' : self.completed,
            'due'       : self.due,
            'estimate'  : self.estimate,
            'user_id'   : self.user_id,
            'plan_dates': self.plan_dates.all()
        }

class Plan_date(db.Model):
    __tablename__ = 'plan_dates'
    id = db.Column(db.Integer, primary_key=True)
    date_stamp = db.Column(db.String(120))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))

    def __init__(self, date_stamp):
        self.date_stamp = date_stamp

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
    return render_template('home.html')

@app.route('/home_data',methods=['GET'])
def home_data():
    if not g.user:
        flash('Please sign in')
        return redirect(url_for('login'))
    # we don't want to calculate on templates, and the date should be rendered instantly, so no JS
    # just do it in python and pass it in
    # What is today? Get the two week interval by stepping back until I find Monday
    two_week_strings = []

    monday = datetime.now()
    makeit = ""
    makeday = ""
    if len(str(monday.month)) == 1:
        makeit = "0"
    elif len(str(monday.day)) == 1:
        makeday = "0"
    today = makeit+str(monday.month)+'-'+makeday+str(monday.day)+'-'+str(monday.year)
    while True:
        if monday.weekday() == 0:
            break
        delta = timedelta(days = 1)
        monday -= delta

    # floor that Monday
    monday = monday - timedelta(hours=monday.hour,minutes=monday.minute,seconds=monday.second,microseconds=monday.microsecond)

    week = {"Monday":[],"Tuesday":[],"Wednesday":[],"Thursday":[],"Friday":[],"Saturday":[],"Sunday":[]}
    weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

    # zip it up
    aw_yeah = dict(zip(range(7),weekdays))

    # time to count forward
    for x in range(14):
        delta = timedelta(days=x)
        current_dt = monday+delta
        two_week_strings.append(aw_yeah[current_dt.weekday()] + ' ' + str(current_dt.month) + '/' + str(current_dt.day))

    # get two weeks worth of tasks
    # get current unix timestamp TODO: This is wrong
    right_now = time.mktime(monday.timetuple())
    two_weeks = right_now + 1209600
    one_week = right_now + 604800
    # raise Exception('hi')
    # get unix timestamp for 2 weeks from now
    tasks = db.session.query(Task).filter(Task.user == g.user).filter(Task.due.between(right_now,two_weeks)).all()
    tasks_yo = {"First": deepcopy(week),"Second": deepcopy(week)}
    plans_yo = deepcopy(week)

    # sort tasks in to day buckets
    i = 0
    while i <= 13:
        left = right_now + i * 86400
        right = left + 86400
        for task in tasks:
            if left <= task.due < right:
                if i <= 6:
                    print "task between ", left, " and ", right, "looks like ", aw_yeah[i], "index ",i
                    tasks_yo["First"][aw_yeah[i]].append(task.serialize)
                else:
                    print "task between ", left, " and ", right, "looks like ", aw_yeah[i%7], "index ",i
                    tasks_yo["Second"][aw_yeah[i%7]].append(task.serialize)
        i += 1
    # I have tasks, and each task has dates for planning. I need to go through every task within the 2 week period,
    # find every plan, and add that task to the appropriate day.
    # Go through every task, find it's plandays.
    # for every planday, add the task to that day's list.
    # for task in tasks:
    #     for planned in task.plan_dates:
    #         # planned is a unix timestamp
    #         # convert unix timestamp to a day, as long as it is in the right interval (right now and two weeks)
    #         if right_now <= planned < one_week:
    #             plans_yo[aw_yeah[datetime.fromtimestamp(planned).weekday()]].append(task)

    categories = g.user.categories.all()

    # make data into JSON object
    home_data = {"categories":categories,"tasks":tasks_yo,"two_weeks":two_week_strings,"planned":plans_yo,"today":today}
    return jsonify(home_data)

@app.route('/addtask', methods=['POST'])
def parsetask():
    if not g.user:
        abort(404)
    else:
        # FUCK IT
        # # parse natural language
        # unparsed = request.form['new_task']
        # # parse the input to get name, dueday, duetime, estimate
        # # 6.033 pset due next friday at 10pm should take about 3 hours
        # # 6.033 pset due friday 10pm 3hr

        # # right now doing a primitive version, TODO: use Hamming distance or classifiers / HMM to get true accuracy / robustness
        # # keywords: before due, after due, after at, before hours
        # split_up = unparsed.split()
        # due_index = split_up.index('due')
        # if unparsed.find('at') != -1:
        #     at_index = split_up.index('at')
        # else:
        #     at_index = None 
        # if unparsed.find('hours') != -1:
        #     hours_index = split_up.index('hours')
        # else:
        #     hours_index = None

        # errors = []

        # # TODO: refactor this crap

        # # name of task. return: STRING
        # name = ' '.join(split_up[:due_index])
        # if not name:
        #     errors.append('No task name found')

        # # due day. return: UNIX TIMESTAMP
        # if at_index != 
        # day_string = ' '.join(split_up[due_index:at_index])
        # cal = pdt.Calendar()
        # due_day = cal.parse(day_string)
        # if due_day[1] == 0 or due_day[1] == 2:
        #     errors.append('No due day found')
        # elif due_day[1] == 1 or due_day[1] == 3:
        #     due_day = time.mktime(datetime(due_day[0].tm_year,due_day[0].tm_mon,due_day[0].tm_mday).timetuple())

        # # due time. return: MILLISECONDS
        # time_string = split_up[at_index+1]
        # due_time = cal.parse(time_string)
        # if due_time[1] == 2:
        #     #good
        #     due_time = time.mktime(datetime(due_time[0].tm_hour))
        # else:
        #     # no time string, this is okay
        #     due_time = None

        # # estimated time required. return: MILLISECONDS
        # estimate = split_up[hours_index-1]

        # Assume that inputs come in already parsed
        name = request.form['name']
        day_string = request.form['date'] # Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
        #time_string = request.form['due_time']  # HH:MM
        time_string = "noon"
        estimate = request.form['length']

        dt = None

        cal = pdt.Calendar()
        okay = day_string.split()[1]+' at '+time_string
        print okay  
        due, what = cal.parse(okay)
        print due, what
        unixstmp = None
        if what in (1, 2):
            # result is struct_time
            dt = datetime(*due[:6])
            unixstmp = int(dt.strftime("%s"))
            print "unixstmp",unixstmp
        else:
            # result is datetime
            unixstmp = int(time.mktime(due))
            print "unixstmp",unixstmp
        if not unixstmp:
            print "Could not understand"
            abort(404)
        # make/add new Task
        print "making new task"
        task = Task(name, unixstmp, estimate)
        print task
        g.user.tasks.append(task)
        db.session.commit()
        return "Done"

@app.route('/check', methods=['POST'])
def check():
    print "hello!"
    if not g.user:
        print "oops"
        abort(404)
    task_id = request.form['task_id']
    task_id = task_id.split('_')[1]
    print "task_id", task_id
    task = db.session.query(Task).filter(Task.user == g.user).filter(Task.id == task_id).all()
    if len(task) == 1 and task[0] in g.user.tasks.all():
        print task[0]
        task[0].completed = True
        db.session.commit()
        return "Done"
    else:
        print "other oops"
        abort(404)

@app.route('/uncheck', methods=['POST'])
def uncheck():
    if not g.user:
        abort(404)
    task_id = request.form['task_id']
    task_id = task_id.split('_')[1]
    task = db.session.query(Task).filter(Task.user == g.user).filter(Task.id == task_id).all()
    if len(task) == 1 and task[0] in g.user.tasks.all():
        task[0].completed = False
        db.session.commit()
        return "Done"
    else:
        abort(404)

@app.route('/delete', methods=['POST'])
def delete():
    if not g.user:
        abort(404)
    task_id = request.form['task_id']
    task_id = task_id.split('_')[1]
    task = db.session.query(Task).filter(Task.user == g.user).filter(Task.id == task_id).all()
    if len(task) == 1 and task[0] in g.user.tasks.all():
        db.session.delete(task[0])
        db.session.commit()
        return "Done"
    else:
        abort(404)

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