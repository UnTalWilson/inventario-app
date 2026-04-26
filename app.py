from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "12345"

# Crear base de datos
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
# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == "admin" and password == "123":
            session["admin"] = True
            return redirect("/admin")
        else:
            return "Credenciales incorrectas"

    return render_template("login.html")
# BUSCAR PRODUCTO
@app.route("/", methods=["GET", "POST"])
def buscar():
    producto = None

    if request.method == "POST":
        codigo = request.form["codigo"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT nombre, talla, color, stock, precio, ubicacion, imagen
        FROM productos
        WHERE codigo = ?
        """, (codigo,))

        producto = cursor.fetchone()

        conn.close()

    return render_template("buscar.html", producto=producto)


# PANEL ADMIN
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
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