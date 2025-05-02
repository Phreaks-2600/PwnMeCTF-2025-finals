from flask import Blueprint, jsonify, request, session, make_response, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import urllib.parse
import random
import json
import os
import re
import asyncio

from src.app import db
from src.models.user import User
from src.models.inventory import Inventory
from src.models.reset_token import ResetToken
from src.utils import *
from src.bot import visit_report

CHEST_COST = 100

def drop_items(n, items):
    items_dropped = []
    for _ in range(n):
        total_rate = sum(item['drop_rate'] for item in items)
        pick = random.uniform(0, total_rate)
        current = 0
        for item in items:
            current += item['drop_rate']
            if current > pick:
                items_dropped.append(item)
                break

    return items_dropped

def cors_config(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '')

    referer = urllib.parse.unquote(request.headers.get('Referer', ''))
    if re.search('^https?:\\/\\/localhost:5000\\/.*', referer, re.MULTILINE):
        response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response

api_bp = Blueprint('api', __name__)

@api_bp.route('/drop', methods=['GET', 'POST'])
@login_required
def drop():
    with open(os.environ['DROP_FILENAME'], 'r') as f:
        items = json.load(f).get('items')

    if request.method == 'GET':
        return jsonify({"chest_cost": CHEST_COST, "items": items})

    elif request.method == 'POST':
        user_id = session.get('user_id')
        balance = db.session.query(User).filter_by(id=user_id).first().balance

        data = request.get_json()
        nb = data.get('nb')

        if not nb:
            return jsonify({"error": "Missing number of chests."}), 400

        if int(nb) < 0:
            return jsonify({"error": "Cannot take less than 0."}), 400
        
        if int(nb) > 3:
            return jsonify({"error": "Cannot take more than 3."}), 400
        
        if balance < int(nb) * CHEST_COST:
            return jsonify({"error": "Not enough money."}), 400

        balance -= nb * CHEST_COST

        db.session.query(User).filter_by(id=user_id).update({'balance': balance})
        db.session.commit()

        items_dropped = drop_items(int(nb), items)

        for item in items_dropped:
            inventory_item = db.session.query(Inventory).filter_by(user_id=user_id, item_id=item['id']).first()
            if inventory_item:
                inventory_item.quantity += 1
            else:
                if item['rarity'] == 'impossible' and session.get('role') != 'admin':
                    name = os.environ['FLAG']
                else:
                    name = item['name']

                new_inventory_item = Inventory(
                    user_id=user_id,
                    item_id=item['id'],
                    name=name,
                    rarity=item['rarity'],
                    image=item['image']
                )
                db.session.add(new_inventory_item)
        db.session.commit()
        
        return jsonify({"items": items_dropped})

@api_bp.route('/inventory', methods=['GET'])
@login_required
def inventory():
    user_id = session.get('user_id')
    inventory = db.session.query(Inventory).filter_by(user_id=user_id).all()

    return jsonify([{
        'id': item.item_id,
        'name': item.name,
        'rarity': item.rarity,
        'image': item.image,
        'quantity': item.quantity
    } for item in inventory])

@api_bp.route('/profile', methods=['OPTIONS'])
def options_profile():
    response = make_response('', 204)
    return cors_config(response)

@api_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        user_id = session.get('user_id')
        user = db.session.query(User).filter_by(id=user_id).first()

        response = make_response(jsonify({
            'uuid': user.uuid, 
            'role': user.role, 
            'username': user.username, 
            'balance': user.balance,
        }))

        return cors_config(response)
    
    elif request.method == 'POST':
        response = make_response(jsonify({"success": "Profile updated."}))
        return cors_config(response)
    
@api_bp.route('/backup', methods=['POST'])
@admin_required
def backup():
    t = request.json.get('time')
    if re.search(r'[A-Za-z!"#%&\'()*+,-./:;<=>@[\]^_`{|}~ \\]', t):
        return jsonify({"error": "Invalid time."}), 400

    output = os.popen(f'cd src/admin_data_uploaded && timeout {t}s ../backup.sh 2>&1').read()
    
    return jsonify({"output": output})

@api_bp.route('/upload', methods=['POST'])
@admin_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, {'json', 'png', 'jpg', 'jpeg'}):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(current_app.config['ADMIN_UPLOAD_FOLDER'] , filename))

    return jsonify({"success": f"File '{filename}' uploaded successfully"}), 200

# Endpoints under construction
@api_bp.route('/report', methods=['POST']) # No page is rendered for the request on /report for now.
@login_required
def report():
    if request.method == 'POST':
        url = request.json.get('url')
        if not url.startswith('http://') and not url.startswith('https://'):
            return jsonify({"error": "Url format not supported."}), 400

        asyncio.run(
            visit_report(
                target_url=url,
                password=current_app.config['ADMIN_PASSWORD']
            )
        )
        return jsonify({"success": "Report submitted."})

@api_bp.route('/reset_token', methods=['POST'])
@nologin_required
@localhost_required
def reset_token():
    username = request.json.get('username')

    user = db.session.query(User).filter_by(username=username).first()
    if not user:
        return jsonify({"error": "Invalid username."}), 400
    
    if db.session.query(ResetToken).filter_by(user_id=user.id).first():
        return jsonify({"error": "Token already sent."}), 400
    
    reset_token = ResetToken(
        user_id=user.id,
        token=generate_reset_token(username, user.uuid)
    )
    db.session.add(reset_token)
    db.session.commit()

    # SMTP process...

    return jsonify({"success": "Reset token sent to your email."})
    
@api_bp.route('/change_password', methods=['POST'])
@nologin_required
def change_password():
    password = request.json.get('password')
    password_confirmation = request.json.get('password_confirmation')
    token = request.json.get('token')

    if password != password_confirmation:
        return jsonify({"error": "Passwords do not match."}), 400

    reset_token = db.session.query(ResetToken).filter_by(token=token).first()

    if not reset_token:
        return jsonify({"error": "Invalid reset token."}), 400 
    
    if reset_token.is_expired():
        return jsonify({"error": "Token has expired."}), 400

    db.session.query(User).filter_by(id=reset_token.user_id).update({
        'password': generate_password_hash(password)
    })
    db.session.commit()

    return jsonify({"success": "Password changed."})
    