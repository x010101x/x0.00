#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import hashlib
import secrets
import threading
import webbrowser
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ==========================================
# CONFIGURATION ET DONNÉES DU SERVEUR (API)
# ==========================================

app = Flask(__name__)
CORS(app)

USERS_FILE = 'users.json'
TICKETS_FILE = 'tickets.json'

ADMINS = {
    'admin1': hashlib.sha256('admin123'.encode()).hexdigest(),
    'admin2': hashlib.sha256('admin456'.encode()).hexdigest()
}

active_tokens = {}

def init_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f: json.dump({}, f)
    if not os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'w') as f: json.dump([], f)

def load_users():
    with open(USERS_FILE, 'r') as f: return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f: json.dump(users, f, indent=2)

def load_tickets():
    with open(TICKETS_FILE, 'r') as f: return json.load(f)

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f: json.dump(tickets, f, indent=2)

# --- ROUTES API ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    if username in ADMINS and ADMINS[username] == pwd_hash:
        token = secrets.token_hex(32)
        active_tokens[token] = {'username': username, 'role': 'admin'}
        return jsonify({'token': token, 'username': username, 'role': 'admin'}), 200

    users = load_users()
    if username in users and users[username]['password'] == pwd_hash:
        token = secrets.token_hex(32)
        active_tokens[token] = {'username': username, 'role': 'user'}
        return jsonify({'token': token, 'username': username, 'role': 'user'}), 200

    return jsonify({'error': 'Identifiants incorrects'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    users = load_users()
    if username in users: return jsonify({'error': 'Utilisateur existe déjà'}), 400
    
    users[username] = {
        'password': hashlib.sha256(password.encode()).hexdigest(),
        'role': 'user',
        'created_at': datetime.now().isoformat()
    }
    save_users(users)
    return jsonify({'message': 'Succès'}), 201

@app.route('/api/tickets', methods=['POST', 'GET'])
def handle_tickets():
    auth = request.headers.get('Authorization', '').replace('Bearer ', '')
    if auth not in active_tokens: return jsonify({'error': 'Non autorisé'}), 401
    
    if request.method == 'POST':
        data = request.json
        tickets = load_tickets()
        new_ticket = {
            'id': len(tickets) + 1,
            'username': active_tokens[auth]['username'],
            'discord_username': data.get('discord_username'),
            'reason': data.get('reason'),
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        tickets.append(new_ticket)
        save_tickets(tickets)
        return jsonify({'message': 'Ticket créé'}), 201
    
    return jsonify({'tickets': load_tickets()}), 200

# ==========================================
# LOGIQUE DU LANCEUR (AUTOMATISATION)
# ==========================================

def run_flask():
    """Lance le serveur Flask sans le mode debug pour éviter les conflits de threads"""
    init_files()
    app.run(port=5000, debug=False, use_reloader=False)

def run_frontend_server():
    """Lance un serveur HTTP simple pour les fichiers HTML/JS"""
    try:
        subprocess.run([sys.executable, "-m", "http.server", "8000"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def setup():
    print("🚀 Démarrage du Système 0x00...")
    
    # Installation auto des dépendances
    try:
        import flask, flask_cors
    except ImportError:
        print("📦 Installation des bibliothèques manquantes...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])

    # Démarrage du Backend dans un thread séparé
    backend_thread = threading.Thread(target=run_flask, daemon=True)
    backend_thread.start()
    
    # Démarrage du Frontend dans un thread séparé
    frontend_thread = threading.Thread(target=run_frontend_server, daemon=True)
    frontend_thread.start()

    time.sleep(2)
    print("✅ Serveurs actifs :")
    print("   - Frontend : http://localhost:8000")
    print("   - API      : http://localhost:5000")
    
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    setup()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Fermeture du système.")