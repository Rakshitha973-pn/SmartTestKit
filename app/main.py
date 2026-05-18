"""
SmartTestKit — Sample Task Manager REST API
This is the app your tests will verify.
"""
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, jwt, datetime, functools

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
DB_PATH = os.environ.get("DB_PATH", "taskdb.sqlite")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                email    TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role     TEXT DEFAULT 'user'
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                title      TEXT NOT NULL,
                priority   TEXT DEFAULT 'medium',
                done       INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)


init_db()


def token_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            request.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0", "db": "connected"})


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or "@" not in email:
        return jsonify({"error": "Invalid email"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password too short (min 8 chars)"}), 400
    try:
        with get_db() as db:
            db.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                       (email, generate_password_hash(password)))
        return jsonify({"message": "User created"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 409


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    token = jwt.encode({
        "user_id": user["id"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"token": token}), 200


@app.route("/tasks", methods=["GET"])
@token_required
def get_tasks():
    priority = request.args.get("priority")
    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [request.user_id]
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY created_at DESC"
    with get_db() as db:
        tasks = db.execute(query, params).fetchall()
    return jsonify([{**dict(t), "done": bool(t["done"])} for t in tasks]), 200


@app.route("/tasks", methods=["POST"])
@token_required
def create_task():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    priority = data.get("priority", "medium")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 200:
        return jsonify({"error": "Title too long (max 200 chars)"}), 400
    if priority not in ("low", "medium", "high"):
        return jsonify({"error": "Priority must be low, medium, or high"}), 400
    with get_db() as db:
        cursor = db.execute("INSERT INTO tasks (user_id, title, priority) VALUES (?, ?, ?)",
                            (request.user_id, title, priority))
        task_id = cursor.lastrowid
    return jsonify({"id": task_id, "title": title, "priority": priority, "done": False}), 201


@app.route("/tasks/<int:task_id>", methods=["PATCH"])
@token_required
def update_task(task_id):
    data = request.get_json() or {}
    with get_db() as db:
        task = db.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?",
                          (task_id, request.user_id)).fetchone()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        done = data.get("done", task["done"])
        title = data.get("title", task["title"]).strip()
        db.execute("UPDATE tasks SET done = ?, title = ? WHERE id = ?",
                   (int(done), title, task_id))
    return jsonify({"id": task_id, "title": title, "done": bool(done)}), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(task_id):
    with get_db() as db:
        task = db.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?",
                          (task_id, request.user_id)).fetchone()
        if not task:
            return jsonify({"error": "Task not found"}), 404
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return jsonify({"message": "Task deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
