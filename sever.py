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

# ---- Database helpers ----
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
    # check exists
    existing = query_db("SELECT id FROM users WHERE username=?", (username,), one=True)
    if existing:
        flash("Tên người dùng đã tồn tại", "error")
        return redirect(url_for("index"))
    pwdhash = generate_password_hash(password)
    query_db("INSERT INTO users (username,password_hash,avatar) VALUES (?,?,?)", (username, pwdhash, avatar))
    flash("Đăng ký thành công. Bạn có thể đăng nhập ngay.", "success")
    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username","").strip()
    password = request.form.get("password","").strip()
    user = query_db("SELECT username, password_hash, avatar FROM users WHERE username=?", (username,), one=True)
    if not user:
        flash("Tài khoản không tồn tại", "error")
        return redirect(url_for("index"))
    if not check_password_hash(user[1], password):
        flash("Mật khẩu không đúng", "error")
        return redirect(url_for("index"))
    session["username"] = user[0]
    session["avatar"] = user[2] or ""
    return redirect(url_for("chat"))

@app.route("/logout")
def logout():
    user = session.get("username")
    session.clear()
    # emit updated online users to everyone
    socketio.emit("online_users", [{"username":u,"avatar":a} for u,a in users_online.items()])
    return redirect(url_for("index"))

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("index"))
    return render_template("chat_pro.html", username=session["username"], avatar=session.get("avatar",""), rooms=list(rooms.keys()))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'ok':False, 'error':'no file'})
    f = request.files['file']
    if f.filename == '':
        return jsonify({'ok':False, 'error':'no filename'})
    if not allowed_file(f.filename):
        return jsonify({'ok':False, 'error':'invalid ext'})
    filename = secure_filename(str(uuid.uuid4().hex + '_' + f.filename))
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(dest)
    url = url_for('uploaded_file', filename=filename)
    return jsonify({'ok':True, 'url': url})

# ---- Socket events ----
@socketio.on("join")
def handle_join(data):
    username = data.get("username")
    avatar = data.get("avatar")
    room = data.get("room","general")
    users_online[username] = avatar
    join_room(room)
    # broadcast updated list
    socketio.emit("online_users", [{"username":u,"avatar":a} for u,a in users_online.items()])
    emit("system", {"msg": f"{username} đã vào phòng {room}"}, room=room)

@socketio.on("leave")
def handle_leave(data):
    username = data.get("username")
    room = data.get("room","general")
    users_online.pop(username, None)
    leave_room(room)
    socketio.emit("online_users", [{"username":u,"avatar":a} for u,a in users_online.items()])
    emit("system", {"msg": f"{username} đã rời phòng {room}"}, room=room)

@socketio.on("typing")
def handle_typing(data):
    room = data.get("room","general")
    emit("typing", {"user": data.get("username")}, room=room, include_self=False)

@socketio.on("send_message")
def handle_message(data):
    username = data.get("username")
    avatar = data.get("avatar")
    room = data.get("room","general")
    msg = data.get("message","")
    ctype = data.get("type","text")
    time = datetime.now().strftime("%H:%M")
    # save to db
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO messages (user,avatar,room,content,content_type,time) VALUES (?,?,?,?,?,?)",
             (username, avatar, room, msg, ctype, time))
    con.commit()
    con.close()
    emit("message", {"user":username,"avatar":avatar,"msg":msg,"time":time,"type":ctype}, room=room)

@socketio.on("reaction")
def handle_reaction(data):
    emit("reaction", data)

@app.route("/history/<room>")
def history(room):
    rows = query_db("SELECT user,avatar,content,content_type,time FROM messages WHERE room=? ORDER BY id ASC", (room,))
    return jsonify([{"user":r[0],"avatar":r[1],"content":r[2],"type":r[3],"time":r[4]} for r in rows])

if __name__ == "__main__":
    # listen on all interfaces so other machines in LAN can connect
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
