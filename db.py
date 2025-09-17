# db.py
import sqlite3

# Crear la base de datos y la tabla si no existe
def crear_tabla():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            correo TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

# Insertar usuario nuevo
def agregar_usuario(nombre, correo):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nombre, correo) VALUES (?, ?)", (nombre, correo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Buscar usuario por nombre o correo
def buscar_usuario(entrada):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, correo FROM usuarios WHERE nombre=? OR correo=?", (entrada, entrada))
    usuario = cursor.fetchone()
    conn.close()
    return usuario  # devuelve (nombre, correo) o None

# Listar todos los usuarios
def listar_usuarios():
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, correo FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios
