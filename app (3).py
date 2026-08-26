import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Gestión de Turnos ZFS", page_icon="🚛", layout="wide")

# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect('turnos_zfs.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL,
            nombre TEXT NOT NULL,
            cedula TEXT NOT NULL,
            telefono TEXT,
            bodega TEXT NOT NULL,
            estado TEXT NOT NULL,
            hora_registro TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def registrar_turno(placa, nombre, cedula, telefono, bodega):
    conn = sqlite3.connect('turnos_zfs.db')
    c = conn.cursor()
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO turnos (placa, nombre, cedula, telefono, bodega, estado, hora_registro)
        VALUES (?, ?, ?, ?, ?, 'EN ESPERA', ?)
    ''', (placa.upper(), nombre, cedula, telefono, bodega.upper(), hora_actual))
    conn.commit()
    conn.close()

def obtener_turnos(estado=None):
    conn = sqlite3.connect('turnos_zfs.db')
    if estado:
        df = pd.read_sql_query(f"SELECT id, placa, nombre, bodega, estado, hora_registro FROM turnos WHERE estado='{estado}'", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM turnos", conn)
    conn.close()
    return df

def actualizar_estado(id_turno, nuevo_estado):
    conn = sqlite3.connect('turnos_zfs.db')
    c = conn.cursor()
    c.execute("UPDATE turnos SET estado = ? WHERE id = ?", (nuevo_estado, id_turno))
    conn.commit()
    conn.close()

# Inicializar la base de datos al arrancar
init_db()

# ==========================================
# VISTA: CONDUCTOR (PÚBLICA)
# ==========================================
def vista_conductor():
    st.title("🚛 Portal de Conductores - Enturnamiento")
    st.write("Bienvenido. Registre sus datos para obtener un turno de ingreso.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Solicitar Turno")
        with st.form("registro_conductor"):
            placa = st.text_input("Placa del Vehículo (Ej. ABC-123)")
            nombre = st.text_input("Nombre Completo")
            cedula = st.text_input("Cédula de Ciudadanía")
            telefono = st.text_input("Número de Teléfono (Celular)")
            bodega = st.selectbox("Bodega de Destino", ["Bodega 1", "Bodega 2", "Bodega 3", "Patio de Carga", "Otro"])
            
            submit = st.form_submit_button("Generar Turno", type="primary")
            
            if submit:
                if placa and nombre and cedula:
                    registrar_turno(placa, nombre, cedula, telefono, bodega)
                    st.success(f"Turno generado con éxito para la placa {placa.upper()}. Por favor, esté atento al tablero.")
                else:
                    st.error("La placa, nombre y cédula son obligatorios.")

    with col2:
        st.subheader("2. Tablero de Turnos (En Vivo)")
        st.write("Verifique si su placa ha sido llamada para ingresar.")
        
        tab_llamados, tab_espera = st.tabs(["🟢 AUTORIZADOS PARA INGRESO", "🟡 EN ESPERA"])
        
        with tab_llamados:
            df_llamados = obtener_turnos("AUTORIZADO")
            if not df_llamados.empty:
                for index, row in df_llamados.iterrows():
                    st.info(f"📢 **PLACA: {row['placa']}** | Dirigirse a: {row['bodega']}")
            else:
                st.write("No hay vehículos en tránsito de ingreso en este momento.")

        with tab_espera:
            df_espera = obtener_turnos("EN ESPERA")
            if not df_espera.empty:
                st.dataframe(df_espera[['placa', 'hora_registro', 'bodega']], use_container_width=True, hide_index=True)
            else:
                st.write("No hay vehículos en fila de espera.")

# ==========================================
# VISTA: ADMINISTRADOR (PRIVADA)
# ==========================================
def vista_admin():
    st.title("🛡️ Panel de Administración ZFS")
    
    # Sistema básico de login
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.info("Por favor, ingrese sus credenciales para gestionar los turnos.")
        clave = st.text_input("Contraseña de Administrador", type="password")
        if st.button("Ingresar"):
            if clave == "admin123":  # Contraseña para el prototipo
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.success("Sesión iniciada como Operador ZFS")
        if st.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

        st.markdown("---")
        st.subheader("Control de Flujo Vehicular")
        
        # Obtener todos los datos
        df_todos = obtener_turnos()
        
        col_espera, col_acciones = st.columns([2, 1])
        
        with col_espera:
            st.write("**Vehículos Registrados (Base de Datos General):**")
            st.dataframe(df_todos, use_container_width=True)
            
        with col_acciones:
            st.write("**Acciones de Operación**")
            
            # Llamar a ingreso
            vehiculos_espera = obtener_turnos("EN ESPERA")
            if not vehiculos_espera.empty:
                placa_llamar = st.selectbox("Llamar vehículo a ingreso:", vehiculos_espera['placa'].tolist())
                if st.button("✅ Autorizar Ingreso"):
                    id_llamar = vehiculos_espera[vehiculos_espera['placa'] == placa_llamar]['id'].values[0]
                    actualizar_estado(id_llamar, "AUTORIZADO")
                    st.rerun()
            else:
                st.info("No hay vehículos en espera.")
                
            st.markdown("---")
            
            # Dar salida / Finalizar turno
            vehiculos_autorizados = obtener_turnos("AUTORIZADO")
            if not vehiculos_autorizados.empty:
                placa_salir = st.selectbox("Registrar salida de Zona Franca:", vehiculos_autorizados['placa'].tolist())
                if st.button("🔴 Finalizar Turno / Salida"):
                    id_salir = vehiculos_autorizados[vehiculos_autorizados['placa'] == placa_salir]['id'].values[0]
                    actualizar_estado(id_salir, "FINALIZADO")
                    st.rerun()
            else:
                st.info("No hay vehículos en operación interna en este momento.")

# ==========================================
# CONTROL DE NAVEGACIÓN (BARRA LATERAL)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/User_icon_2.svg/2048px-User_icon_2.svg.png", width=100) # Placeholder para logo
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Seleccione el portal:", ["👨‍✈️ Portal Conductor", "⚙️ Panel Administrador"])

st.sidebar.markdown("---")
st.sidebar.caption("Sistema de Enturnamiento V1.0")

if opcion == "👨‍✈️ Portal Conductor":
    vista_conductor()
elif opcion == "⚙️ Panel Administrador":
    vista_admin()
