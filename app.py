from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "12345"

def crear_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nombre TEXT,
        talla TEXT,
        color TEXT,
        stock INTEGER,
        precio REAL,
        ubicacion TEXT,
        imagen TEXT
    )
    """)
    conn.commit()
    conn.close()

crear_db()

# BUSCAR PRODUCTO (público)
@app.route("/", methods=["GET", "POST"])
def buscar():
    producto = None
    if request.method == "POST":
        codigo = request.form["codigo"]
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
        SELECT nombre, talla, color, stock, precio, ubicacion, imagen
        FROM productos WHERE codigo = ?
        """, (codigo,))
        producto = cursor.fetchone()
        conn.close()
    return render_template("buscar.html", producto=producto)

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        if usuario == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Usuario o contraseña incorrectos"
    return render_template("login.html", error=error)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ADMIN (protegido)
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")
    
    if request.method == "POST":
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        talla = request.form["talla"]
        color = request.form["color"]
        stock = request.form["stock"]
        precio = request.form["precio"]
        ubicacion = request.form["ubicacion"]
        imagen = request.form["imagen"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO productos (codigo, nombre, talla, color, stock, precio, ubicacion, imagen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nombre, talla, color, stock, precio, ubicacion, imagen))
        conn.commit()
        conn.close()

    return render_template("admin.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)