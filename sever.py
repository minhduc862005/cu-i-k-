from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
import os, sqlite3, uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"png","jpg","jpeg","gif","webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET","change_this_secret_for_prod")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*")
