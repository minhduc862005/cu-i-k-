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
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET","change_this_secret_for_prod")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*")
# Init DB
init_db()

# In-memory online users and rooms
users_online = {}  # username -> avatar
rooms = {"general": []}

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

# ---- Routes ----
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("chat"))
    avatars = sorted(os.listdir(os.path.join(app.static_folder, 'avatars')))
    return render_template("login_register.html", avatars=avatars)

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username","").strip()
    password = request.form.get("password","").strip()
    avatar = request.form.get("avatar")
    if not username or not password:
        flash("Tên hoặc mật khẩu không hợp lệ", "error")
        return redirect(url_for("index"))
