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
    just_created = db.Column(db.Boolean, default=True)
    categories = db.relationship('Category', backref='user', lazy='dynamic')
    tasks = db.relationship('task', backref='task', lazy='dynamic')

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    color = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tasks = db.relationship('Task', secondary=taskTable, backref=db.backref('categories', lazy='dynamic'))

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    completed = db.Column(db.Boolean, default=False)
    duedate = db.Column(db.String(120))
    estimate = db.Column(db.String(120))
    importance = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # check password hash and whatnot
    return 'hmm'

@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect(url_for('index'))

@app.route('/settings')
def settings():
    if 'userid' not in session:
        flash('Please sign in.')
        return redirect(url_for('index'))
    return render_template('settings.html')

@app.route('/login')
def login():
    if 'userid' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup')
def signup():
    if 'userid' in session:
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/home')
def home():
    if 'userid' not in session:
        flash('Please sign in')
        return redirect(url_for('index'))
    return render_template('home.html', categories=categories, tasks=tasks)

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