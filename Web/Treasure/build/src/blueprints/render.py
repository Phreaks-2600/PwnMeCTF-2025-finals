from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

from src.app import db
from src.models.user import User
from src.utils import login_required, admin_required, nologin_required, localhost_required

render_bp = Blueprint('render', __name__)

@render_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@render_bp.route('/login', methods=['GET', 'POST'])
@nologin_required
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('render.login'))
        
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('render.login'))
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        return redirect(url_for('render.index'))

@render_bp.route('/register', methods=['GET', 'POST'])
@nologin_required
@localhost_required
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirmation = request.form.get('password_confirmation')

        if password != password_confirmation:
            flash('Passwords do not match', 'error')
            return redirect(url_for('render.register'))

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('render.register'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return redirect(url_for('render.register'))
        
        if len(username) > 32:
            flash('Username must be at most 32 characters long', 'error')
            return redirect(url_for('render.register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('render.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('render.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully', 'success')
        return redirect(url_for('render.register'))
    
@render_bp.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('render.login'))

@render_bp.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html')

@render_bp.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')