# -*- coding: utf-8 -*-
"""
Sistema de Gestión de Turnos y Registro de Conductores — Zona Franca Santander
================================================================================
Módulo unificado: Portal del Conductor + Panel de Administración con Autorización
"""

import os
import json
from datetime import datetime
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Configuración de página y Estilos Corporativos ZFC
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Turnos y Accesos | Zona Franca Santander",
    page_icon="🚛",
    layout="wide",
)

st.markdown("""
<style>
    :root {
        --zf-green-dark: #1B4D3E;
        --zf-green-medium: #2C6B56;
        --zf-olive: #8A9A28;
        --zf-card-bg: #FFFFFF;
        --zf-text-main: #2C3E50;
    }

    .stApp {
        background-color: #F4F7F6;
    }

    h1, h2, h3 {
        color: var(--zf-green-dark) !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    .ficho-card {
        background: linear-gradient(135deg, #1B4D3E 0%, #2C6B56 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        margin: 20px 0px;
    }

    .stButton>button {
        background-color: var(--zf-green-dark);
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: var(--zf-green-medium);
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Gestión de Datos Persistentes (Archivo local JSON)
# --------------------------------------------------------------------------
DATA_FILE = "turnos_zfc.json"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

if "turnos" not in st.session_state:
    st.session_state.turnos = cargar_datos()

if "ultimo_turno_registrado" not in st.session_state:
    st.session_state.ultimo_turno_registrado = None

# --------------------------------------------------------------------------
# Interfaz Principal (Navegación por Roles)
# --------------------------------------------------------------------------
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    if os.path.exists("LOGO ZFS-ZFC.jpeg"):
        st.image("LOGO ZFS-ZFC.jpeg", width=180)
    else:
        st.markdown("🏢 **ZONA FRANCA**")

with col_tit:
    st.markdown("## Sistema de Enturnamiento y Control de Accesos")
    st.caption("Zona Franca Santander | Cúcuta")

st.divider()

# Selector de Modo en la barra lateral
st.sidebar.markdown("### 🧭 Menú de Navegación")
modo = st.sidebar.radio("Seleccione el Portal:", ["🚛 Portal del Conductor", "🔐 Panel de Administración"])

# ==========================================================================
# MÓDULO 1: PORTAL DEL CONDUCTOR
# ==========================================================================
if modo == "🚛 Portal del Conductor":
    st.markdown("### 📋 Registro y Turno de Ingreso")
    st.markdown("Estimado conductor, por favor ingrese sus datos para asignarle su ficho de turno en la Zona Franca.")

    tab_reg, tab_tablero = st.tabs(["✍️ Registrarse / Sacar Turno", "📊 Tablero de Turnos en Vivo"])

    with tab_reg:
        # Si acaba de registrarse, mostrar el ficho limpio en pantalla
        if st.session_state.ultimo_turno_registrado:
            t_info = st.session_state.ultimo_turno_registrado
            st.markdown(f"""
                <div class="ficho-card">
                    <h2>¡TURNO ASIGNADO CON ÉXITO!</h2>
                    <p style="font-size: 18px; margin-bottom: 5px;">PLACA DEL VEHÍCULO</p>
                    <h1 style="color: #FFD700 !important; font-size: 45px; margin-top: 0;">{t_info['placa']}</h1>
                    <hr style="border-color: rgba(255,255,255,0.2);">
                    <p style="font-size: 18px; margin-bottom: 5px;">NÚMERO DE TURNO (FICHO)</p>
                    <h1 style="color: #FFFFFF !important; font-size: 55px; margin-top: 0;">{t_info['id_turno']}</h1>
                    <p><b>Bodega Destino:</b> {t_info['bodega']}</p>
                    <p><i>Por favor manténgase atento al tablero de avisos.</i></p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Registrar otro vehículo / Nuevo Turno"):
                st.session_state.ultimo_turno_registrado = None
                st.rerun()
        else:
            with st.form("form_conductor", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    placa = st.text_input("Placa del Vehículo * (Ej: ABC123)").upper().strip()
                    remolque = st.text_input("Remolque / Unidad de Carga (Opcional)").upper().strip()
                    nombre = st.text_input("Nombre Completo del Conductor *").title().strip()
                with col2:
                    cedula = st.text_input("Número de Cédula / Documento *").strip()
                    telefono = st.text_input("Número de Contacto / Celular *").strip()
                    bodega = st.selectbox("Bodega / Usuario de Destino *", [
                        "Seleccione una bodega...",
                        "Bodega Principal / Genérica",
                        "Alfranca Cúcuta S.A.S.",
                        "Inversiones Cargamax HYJ S.A.S.",
                        "Logística Aduanera J.H. Ltda.",
                        "Setracomex S.A.S.",
                        "Otra Bodega / Operador"
                    ])

                submitted = st.form_submit_button("🎟️ Obtener mi Turno")

                if submitted:
                    if not placa or not nombre or not cedula or not telefono or bodega == "Seleccione una bodega...":
                        st.error("⚠️ Por favor complete todos los campos obligatorios marcados con asterisco (*).")
                    else:
                        nuevo_id = len(st.session_state.turnos) + 1
                        turno_str = f"T-{nuevo_id:03d}"
                        
                        nuevo_registro = {
                            "id_turno": turno_str,
                            "placa": placa,
                            "remolque": remolque if remolque else "N/A",
                            "nombre": nombre,
                            "cedula": cedula,
                            "telefono": telefono,
                            "bodega": bodega,
                            "estado": "En Espera",
                            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "mensaje_admin": "En espera de autorización"
                        }
                        
                        st.session_state.turnos.append(nuevo_registro)
                        guardar_datos(st.session_state.turnos)
                        st.session_state.ultimo_turno_registrado = nuevo_registro
                        st.rerun()

    with tab_tablero:
        st.markdown("#### 📺 Sala de Espera Virtual")
        st.markdown("Considere el estado actual de las placas en la fila y los vehículos autorizados para ingresar.")

        if not st.session_state.turnos:
            st.info("No hay vehículos registrados en el sistema actualmente.")
        else:
            df_turnos = pd.DataFrame(st.session_state.turnos)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Vehículos en Espera", len(df_turnos[df_turnos["estado"] == "En Espera"]))
            c2.metric("🟢 Con Luz Verde (Autorizados)", len(df_turnos[df_turnos["estado"].str.contains("AUTORIZADO", case=False, na=False)]))
            c3.metric("Total Registrados Hoy", len(df_turnos))

            st.markdown("---")
            
            # Tabla resumida amigable para ver placas y turnos en pantalla
            cols_mostrar = ["id_turno", "placa", "bodega", "estado", "mensaje_admin"]
            df_vista = df_turnos[cols_mostrar].rename(columns={
                "id_turno": "Turno",
                "placa": "Placa",
                "bodega": "Destino / Bodega",
                "estado": "Estado Actual",
                "mensaje_admin": "Aviso / Instrucción"
            })
            
            st.dataframe(df_vista, use_container_width=True, hide_index=True)

# ==========================================================================
# MÓDULO 2: PANEL DE ADMINISTRACIÓN
# ==========================================================================
elif modo == "🔐 Panel de Administración":
    st.markdown("### ⚙️ Panel de Control y Autorización de Ingresos")
    
    if "auth_admin" not in st.session_state:
        st.session_state.auth_admin = False

    if not st.session_state.auth_admin:
        col_log1, col_log2, col_log3 = st.columns([1, 2, 1])
        with col_log2:
            st.markdown("#### Acceso Restringido")
            usuario_ing = st.text_input("Usuario Administrador")
            pass_ing = st.text_input("Contraseña", type="password")
            
            if st.button("Iniciar Sesión", use_container_width=True):
                # Credenciales estrictas solicitadas
                if usuario_ing == "Zona Franca Santander" and pass_ing == "ZONAFRANCA123":
                    st.session_state.auth_admin = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique el usuario y la contraseña.")
    else:
        if st.sidebar.button("Cerrar Sesión Admin"):
            st.session_state.auth_admin = False
            st.rerun()

        st.success("🔓 Sesión de Administrador Activa — Zona Franca Santander")

        if not st.session_state.turnos:
            st.info("No hay registros de vehículos pendientes en este momento.")
        else:
            df_admin = pd.DataFrame(st.session_state.turnos)

            st.markdown("#### 🚦 Dar Luz Verde y Autorizar Ingreso")
            
            # Seleccionar turno / placa a gestionar
            turno_sel = st.selectbox("Seleccione la Placa / Turno a Autorizar", df_admin["id_turno"] + " — Placa: " + df_admin["placa"] + " (" + df_admin["estado"] + ")")
            id_seleccionado = turno_sel.split(" — ")[0]

            reg_actual = next((item for item in st.session_state.turnos if item["id_turno"] == id_seleccionado), None)

            if reg_actual:
                with st.form("form_admin_luz_verde"):
                    st.markdown(f"**Conductor:** {reg_actual['nombre']} | **Cédula:** {reg_actual['cedula']} | **Bodega:** {reg_actual['bodega']}")
                    
                    nuevo_estado = st.selectbox(
                        "Estado de Autorización",
                        ["En Espera", "🟢 LUZ VERDE / AUTORIZADO A INGRESAR", "Ingresado en ZFC", "Salida Finalizada"],
                        index=0 if reg_actual["estado"] == "En Espera" else 1
                    )
                    
                    mensaje_personalizado = st.text_input("Mensaje / Muelle asignado para el conductor", value=reg_actual["mensaje_admin"])
                    
                    btn_autorizar = st.form_submit_button("🚀 Aplicar Cambios y Dar Aviso")
                    
                    if btn_autorizar:
                        reg_actual["estado"] = nuevo_estado
                        reg_actual["mensaje_admin"] = mensaje_personalizado
                        guardar_datos(st.session_state.turnos)
                        st.success(f"¡Se actualizó el estado para la placa {reg_actual['placa']} correctamente!")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 📊 Listado Completo de Placas y Turnos Registrados")
            st.dataframe(pd.DataFrame(st.session_state.turnos), use_container_width=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🗑️ Reiniciar Todos los Turnos"):
                    st.session_state.turnos = []
                    guardar_datos([])
                    st.success("Tablero reiniciado con éxito.")
                    st.rerun()
            with col_d2:
                csv_export = pd.DataFrame(st.session_state.turnos).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Descargar Reporte en CSV", data=csv_export, file_name="control_turnos_zfc.csv", mime="text/csv")
