from flask import Flask, render_template, request, redirect, session
import psycopg2
from datetime import datetime
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = "dwgbi7glk",
    api_key = "844949396175941",
    api_secret = "GQOSypE5teK1ZtXxokPOxP39ZVo"
)

app = Flask(__name__)
app.secret_key = "12345"

DATABASE_URL = "postgresql://inventario_db_i3fa_user:IOv3pW8g4v5NtGDSny4Z7cTl4RIfl2PL@dpg-d7n9hhf7f7vs73fl3r40-a/inventario_db_i3fa"

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def crear_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id SERIAL PRIMARY KEY,
        codigo TEXT,
        nombre TEXT,
        talla TEXT,
        color TEXT,
        stock INTEGER,
        precio REAL,
        ubicacion TEXT,
        imagen TEXT,
        fecha TEXT
    )
    """)
    conn.commit()
    conn.close()

crear_db()

@app.route("/", methods=["GET", "POST"])
def buscar():
    producto = None
    if request.method == "POST":
        codigo = request.form["codigo"]
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT nombre, talla, color, stock, precio, ubicacion, imagen
        FROM productos WHERE codigo = %s
        """, (codigo,))
        producto = cursor.fetchone()
        conn.close()
    return render_template("buscar.html", producto=producto)

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

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
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        imagen = ""
        if "imagen" in request.files and request.files["imagen"].filename != "":
            archivo = request.files["imagen"]
            resultado = cloudinary.uploader.upload(archivo)
            imagen = resultado["secure_url"]
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO productos (codigo, nombre, talla, color, stock, precio, ubicacion, imagen, fecha)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (codigo, nombre, talla, color, stock, precio, ubicacion, imagen, fecha))
        conn.commit()
        conn.close()
    return render_template("admin.html")

@app.route("/admin/lista")
def lista_productos():
    if not session.get("admin"):
        return redirect("/login")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, nombre, talla, color, stock, precio, fecha FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    conn.close()
    return render_template("lista.html", productos=productos)

@app.route("/admin/eliminar/<int:id>")
def eliminar(id):
    if not session.get("admin"):
        return redirect("/login")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin/lista")

@app.route("/admin/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if not session.get("admin"):
        return redirect("/login")
    conn = get_conn()
    cursor = conn.cursor()
    if request.method == "POST":
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        talla = request.form["talla"]
        color = request.form["color"]
        stock = request.form["stock"]
        precio = request.form["precio"]
        ubicacion = request.form["ubicacion"]
        imagen = None
        if "imagen" in request.files and request.files["imagen"].filename != "":
            archivo = request.files["imagen"]
            resultado = cloudinary.uploader.upload(archivo)
            imagen = resultado["secure_url"]
        
        if imagen:
            cursor.execute("""
            UPDATE productos SET codigo=%s, nombre=%s, talla=%s, color=%s, stock=%s, precio=%s, ubicacion=%s, imagen=%s
            WHERE id=%s
            """, (codigo, nombre, talla, color, stock, precio, ubicacion, imagen, id))
        else:
            cursor.execute("""
            UPDATE productos SET codigo=%s, nombre=%s, talla=%s, color=%s, stock=%s, precio=%s, ubicacion=%s
            WHERE id=%s
            """, (codigo, nombre, talla, color, stock, precio, ubicacion, id))
        conn.commit()
        conn.close()
        return redirect("/admin/lista")
    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()
    conn.close()
    return render_template("editar.html", producto=producto)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)