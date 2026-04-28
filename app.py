from flask import Flask, render_template, request, redirect, session
import os
import psycopg2
from datetime import datetime
import cloudinary
import cloudinary.uploader
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# CONFIGURACIÓN
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL")

cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET")
)

if not DATABASE_URL:
    raise ValueError("Falta DATABASE_URL")

if not os.environ.get("CLOUD_NAME"):
    raise ValueError("Falta CLOUD_NAME")

if not os.environ.get("API_KEY"):
    raise ValueError("Falta API_KEY")

if not os.environ.get("API_SECRET"):
    raise ValueError("Falta API_SECRET")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Falta SECRET_KEY")

app = Flask(__name__)
app.secret_key = SECRET_KEY

# =========================
# BASE DE DATOS
# =========================

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def crear_db():
    conn = get_conn()
    cursor = conn.cursor()

    from werkzeug.security import generate_password_hash

    admin_pass = generate_password_hash("Admin#2026_Seguro!")
    vendedor_pass = generate_password_hash("Vendedor#2026!")

    cursor.execute("UPDATE usuarios SET password=%s WHERE usuario='admin'", (admin_pass,))
    cursor.execute("UPDATE usuarios SET password=%s WHERE usuario='vendedor'", (vendedor_pass,))

    # PRODUCTOS
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

    cursor.execute("DROP TABLE IF EXISTS usuarios")

    # USUARIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        usuario TEXT UNIQUE,
        password TEXT,
        rol TEXT
    )
    """)

    # CREAR USUARIOS SEGUROS
    admin_pass = generate_password_hash("1234")
    vendedor_pass = generate_password_hash("1234")

    cursor.execute("""
    INSERT INTO usuarios (usuario, password, rol)
    VALUES (%s, %s, %s)
    ON CONFLICT (usuario) DO NOTHING
    """, ("admin", admin_pass, "admin"))

    cursor.execute("""
    INSERT INTO usuarios (usuario, password, rol)
    VALUES (%s, %s, %s)
    ON CONFLICT (usuario) DO NOTHING
    """, ("vendedor", vendedor_pass, "vendedor"))

    # VENTAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id SERIAL PRIMARY KEY,
        codigo TEXT,
        nombre TEXT,
        cantidad INTEGER,
        precio REAL,
        total REAL,
        vendedor TEXT,
        fecha TEXT
    )
    """)

    # COLUMNA EXTRA
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN costo REAL")
    except:
        pass

    conn.commit()
    conn.close()

crear_db()

# =========================
# RUTAS
# =========================

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

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT password, rol FROM usuarios WHERE usuario=%s", (usuario,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[0], password):
            session["usuario"] = usuario
            session["rol"] = user[1]
            return redirect("/inicio")
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# INICIO
@app.route("/inicio")
def inicio():
    if not session.get("rol"):
        return redirect("/login")
    return render_template("inicio.html", rol=session["rol"])

# ADMIN
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("rol") != "admin":
        return redirect("/login")

    if request.method == "POST":
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        talla = request.form["talla"]
        color = request.form["color"]
        stock = request.form["stock"]
        precio = request.form["precio"]
        ubicacion = request.form["ubicacion"]
        costo = request.form.get("costo") or 0
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        imagen = ""
        if "imagen" in request.files and request.files["imagen"].filename != "":
            archivo = request.files["imagen"]
            resultado = cloudinary.uploader.upload(archivo)
            imagen = resultado["secure_url"]

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO productos (codigo, nombre, talla, color, stock, precio, ubicacion, imagen, fecha, costo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (codigo, nombre, talla, color, stock, precio, ubicacion, imagen, fecha, costo))

        conn.commit()
        conn.close()

    return render_template("admin.html")

# LISTA PRODUCTOS
@app.route("/admin/lista")
def lista_productos():
    if session.get("rol") != "admin":
        return redirect("/login")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, codigo, nombre, talla, color, stock, precio, fecha
    FROM productos ORDER BY id DESC
    """)

    productos = cursor.fetchall()
    conn.close()

    return render_template("lista.html", productos=productos)

# ELIMINAR
@app.route("/admin/eliminar/<int:id>")
def eliminar(id):
    if session.get("rol") != "admin":
        return redirect("/login")

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin/lista")

# EDITAR
@app.route("/admin/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if session.get("rol") != "admin":
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
        costo = request.form.get("costo") or 0

        imagen = None
        if "imagen" in request.files and request.files["imagen"].filename != "":
            archivo = request.files["imagen"]
            resultado = cloudinary.uploader.upload(archivo)
            imagen = resultado["secure_url"]

        if imagen:
            cursor.execute("""
            UPDATE productos SET codigo=%s, nombre=%s, talla=%s, color=%s, stock=%s,
            precio=%s, ubicacion=%s, imagen=%s, costo=%s WHERE id=%s
            """, (codigo, nombre, talla, color, stock, precio, ubicacion, imagen, costo, id))
        else:
            cursor.execute("""
            UPDATE productos SET codigo=%s, nombre=%s, talla=%s, color=%s, stock=%s,
            precio=%s, ubicacion=%s, costo=%s WHERE id=%s
            """, (codigo, nombre, talla, color, stock, precio, ubicacion, costo, id))

        conn.commit()
        conn.close()
        return redirect("/admin/lista")

    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()
    conn.close()

    return render_template("editar.html", producto=producto)

# VENTAS
@app.route("/ventas", methods=["GET", "POST"])
def ventas():
    if not session.get("rol"):
        return redirect("/login")

    mensaje = None
    producto = None

    if request.method == "POST":
        accion = request.form.get("accion")
        codigo = request.form.get("codigo")

        conn = get_conn()
        cursor = conn.cursor()

        if accion == "buscar":
            cursor.execute("SELECT nombre, stock, precio FROM productos WHERE codigo = %s", (codigo,))
            producto = cursor.fetchone()
            if not producto:
                mensaje = "❌ Producto no encontrado"

        elif accion == "vender":
            cantidad = int(request.form.get("cantidad", 0))

            cursor.execute("SELECT nombre, stock, precio FROM productos WHERE codigo = %s", (codigo,))
            producto = cursor.fetchone()

            if producto and producto[1] >= cantidad:
                total = cantidad * producto[2]
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

                cursor.execute("""
                INSERT INTO ventas (codigo, nombre, cantidad, precio, total, vendedor, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (codigo, producto[0], cantidad, producto[2], total, session["usuario"], fecha))

                cursor.execute("UPDATE productos SET stock = stock - %s WHERE codigo = %s", (cantidad, codigo))

                conn.commit()
                mensaje = f"Venta registrada — {cantidad} unidades de {producto[0]}"
                producto = None
            else:
                mensaje = "❌ Stock insuficiente"

        conn.close()

    return render_template("ventas.html", producto=producto, mensaje=mensaje)

# REPORTES
@app.route("/reportes")
def reportes():
    if session.get("rol") != "admin":
        return redirect("/login")

    conn = get_conn()
    cursor = conn.cursor()

    hoy = datetime.now().strftime("%d/%m/%Y")

    cursor.execute("""
    SELECT COUNT(*), SUM(cantidad), SUM(total)
    FROM ventas WHERE fecha LIKE %s
    """, (hoy + "%",))
    resumen_hoy = cursor.fetchone()

    cursor.execute("""
    SELECT nombre, cantidad, precio, total, vendedor, fecha
    FROM ventas ORDER BY id DESC LIMIT 20
    """)
    ventas = cursor.fetchall()

    cursor.execute("""
    SELECT codigo, nombre, stock
    FROM productos WHERE stock < 5 ORDER BY stock ASC
    """)
    stock_bajo = cursor.fetchall()

    conn.close()

    return render_template("reportes.html", resumen_hoy=resumen_hoy, ventas=ventas, stock_bajo=stock_bajo)

# SERVICE WORKER
@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")

# INVENTARIO
@app.route("/inventario")
def inventario():
    orden = request.args.get("orden", "nombre")
    direccion = request.args.get("dir", "asc")

    columnas_validas = ["nombre", "codigo", "talla", "color", "stock", "precio", "fecha"]
    if orden not in columnas_validas:
        orden = "nombre"

    sql_dir = "ASC" if direccion == "asc" else "DESC"

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT codigo, nombre, talla, color, stock, precio, ubicacion, fecha
    FROM productos ORDER BY {orden} {sql_dir}
    """)

    productos = cursor.fetchall()
    conn.close()

    return render_template("inventario.html", productos=productos, orden=orden, dir=direccion)

# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)