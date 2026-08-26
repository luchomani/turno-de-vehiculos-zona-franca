import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'turnos_zfs.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            estado TEXT NOT NULL,
            hora_registro TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def registrar_turno(placa):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Registramos la placa y por defecto entra 'EN ESPERA'
    c.execute("INSERT INTO turnos (placa, estado, hora_registro) VALUES (?, 'EN ESPERA', ?)", (placa.upper(), hora))
    conn.commit()
    turno_id = c.lastrowid
    conn.close()
    return turno_id

def obtener_turnos(estado=None):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, placa, estado, hora_registro FROM turnos"
    if estado:
        query += f" WHERE estado='{estado}'"
    query += " ORDER BY id DESC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def actualizar_estado(id_turno, nuevo_estado):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE turnos SET estado = ? WHERE id = ?", (nuevo_estado, id_turno))
    conn.commit()
    conn.close()