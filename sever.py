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
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        avatar TEXT,
        bio TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        avatar TEXT,
        room TEXT,
        content TEXT,
        content_type TEXT,
        time TEXT
    )""")
    con.commit()
    con.close()

def query_db(query, args=(), one=False):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    con.commit()
    con.close()
    return (rv[0] if rv else None) if one else rv

# Khởi tạo DB
init_db()
users_online = {}  # username -> avatar
rooms = {"general": []}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT
@app.route("/")
def index():
    ...
@app.route("/register", methods=["POST"])
def register():
    ...
@app.route("/login", methods=["POST"])
def login():
    ...
@app.route("/logout")
def logout():
    ...
@app.route("/chat")
def chat():
    ...
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    ...
@app.route('/upload', methods=['POST'])
def upload_file():
    ...
@app.route("/history/<room>")
def history(room):
    ...
@socketio.on("join")
def handle_join(data):
    ...

@socketio.on("leave")
def handle_leave(data):
    ...

@socketio.on("typing")
def handle_typing(data):
    ...

@socketio.on("send_message")
def handle_message(data):
    ...

@socketio.on("reaction")
def handle_reaction(data):
    ...
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
