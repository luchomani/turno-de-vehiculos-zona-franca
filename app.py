# -*- coding: utf-8 -*-
"""
Sistema de Gestión de Turnos y Registro de Conductores — Zona Franca Santander
================================================================================
"""

import os
import json
from datetime import datetime
import pandas as pd
import streamlit as st

# Configuración de página adaptada para móviles
st.set_page_config(
    page_title="Turnos y Accesos | Zona Franca Santander",
    page_icon="🚛",
    layout="centered",
)

# Estilos CSS optimizados para mayor legibilidad y botones grandes
st.markdown("""
<style>
    .stApp {
        background-color: #F8F9FA;
    }

    h1, h2, h3 {
        color: #1B4D3E !important;
        font-family: Arial, sans-serif;
    }

    input, select, textarea {
        font-size: 18px !important;
        padding: 12px !important;
    }

    .stButton>button {
        background-color: #1B4D3E;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        font-size: 18px;
        padding: 0.8rem 1.5rem;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stButton>button:hover {
        background-color: #2C6B56;
        color: white;
    }

    .ficho-card {
        background: #1B4D3E;
        color: white;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        margin: 20px 0px;
    }
</style>
""", unsafe_allow_html=True)

# Gestión de Datos en Archivo Local JSON
DATA_FILE = "turnos_zfc.json"

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                for item in datos:
                    if "tipo_movimiento" not in item:
                        item["tipo_movimiento"] = "Ingresar"
                    if "fecha_hora" not in item:
                        item["fecha_hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return datos
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

# Encabezado institucional
st.markdown("## Zona Franca Santander")
st.caption("Sistema de Enturnamiento y Control de Accesos - Cúcuta")
st.divider()

# Menú de Navegación lateral simplificado
st.sidebar.markdown("### Navegación")
modo = st.sidebar.radio("Seleccione el Portal:", ["Portal del Conductor", "Panel de Administración"])

# ==========================================================================
# PORTAL DEL CONDUCTOR
# ==========================================================================
if modo == "Portal del Conductor":
    st.markdown("### Registro y Turno de Ingreso")
    st.markdown("Por favor ingrese sus datos para asignarle su turno de forma rápida.")

    tab_reg, tab_tablero = st.tabs(["Registrarse y Sacar Turno", "Tablero de Turnos"])

    with tab_reg:
        if st.session_state.ultimo_turno_registrado:
            t_info = st.session_state.ultimo_turno_registrado
            st.markdown(f"""
                <div class="ficho-card">
                    <h3 style="color: white !important; margin:0;">TURNO ASIGNADO</h3>
                    <p style="font-size: 16px; margin: 5px 0;">PLACA DEL VEHICULO</p>
                    <h1 style="color: #FFD700 !important; font-size: 40px; margin: 0;">{t_info['placa']}</h1>
                    <hr style="border-color: rgba(255,255,255,0.2);">
                    <p style="font-size: 16px; margin: 5px 0;">NUMERO DE FICHO</p>
                    <h1 style="color: #FFFFFF !important; font-size: 50px; margin: 0;">{t_info['id_turno']}</h1>
                    <p style="margin-top: 10px;"><b>Destino:</b> {t_info['bodega']}</p>
                    <p style="font-size: 13px; color: #E0E0E0;">Fecha y Hora: {t_info['fecha_hora']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Registrar otro vehiculo"):
                st.session_state.ultimo_turno_registrado = None
                st.rerun()
        else:
            with st.form("form_conductor", clear_on_submit=True):
                placa = st.text_input("Placa del Vehiculo (Ej: ABC123)").upper().strip()
                nombre = st.text_input("Nombre Completo del Conductor").title().strip()
                cedula = st.text_input("Numero de Cedula").strip()
                
                bodega = st.selectbox("Bodega de Destino", [
                    "Seleccione una bodega...",
                    "Bodega Principal / Generica",
                    "Alfranca Cucuta S.A.S.",
                    "Inversiones Cargamax HYJ S.A.S.",
                    "Logistica Aduanera J.H. Ltda.",
                    "Setracomex S.A.S.",
                    "Otra Bodega / Operador"
                ])

                submitted = st.form_submit_button("Obtener mi Turno")

                if submitted:
                    if not placa or not nombre or not cedula or bodega == "Seleccione una bodega...":
                        st.error("Por favor complete todos los campos obligatorios.")
                    else:
                        nuevo_id = len(st.session_state.turnos) + 1
                        turno_str = f"T-{nuevo_id:03d}"
                        
                        nuevo_registro = {
                            "id_turno": turno_str,
                            "placa": placa,
                            "nombre": nombre,
                            "cedula": cedula,
                            "bodega": bodega,
                            "tipo_movimiento": "Ingresar",
                            "estado": "En Espera",
                            "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "mensaje_admin": "En espera de autorizacion"
                        }
                        
                        st.session_state.turnos.append(nuevo_registro)
                        guardar_datos(st.session_state.turnos)
                        st.session_state.ultimo_turno_registrado = nuevo_registro
                        st.rerun()

    with tab_tablero:
        st.markdown("### Tablero de Turnos en Vivo")

        if not st.session_state.turnos:
            st.info("No hay vehiculos registrados en el sistema actualmente.")
        else:
            df_turnos = pd.DataFrame(st.session_state.turnos)
            
            espera_count = len(df_turnos[df_turnos["estado"] == "En Espera"])
            st.metric("Vehiculos en Espera (Esturnados)", espera_count)

            st.markdown("---")
            
            # Incluimos fecha_hora en la visualización para control
            cols_mostrar = ["id_turno", "placa", "fecha_hora", "bodega", "tipo_movimiento", "estado", "mensaje_admin"]
            df_vista = df_turnos[cols_mostrar].rename(columns={
                "id_turno": "Turno",
                "placa": "Placa",
                "fecha_hora": "Fecha y Hora",
                "bodega": "Bodega Destino",
                "tipo_movimiento": "Movimiento",
                "estado": "Estado Actual",
                "mensaje_admin": "Mensaje / Aviso"
            })
            
            st.dataframe(df_vista, use_container_width=True, hide_index=True)

# ==========================================================================
# PANEL DE ADMINISTRACIÓN
# ==========================================================================
elif modo == "Panel de Administración":
    st.markdown("### Panel de Control Administrativo")
    
    if "auth_admin" not in st.session_state:
        st.session_state.auth_admin = False

    if not st.session_state.auth_admin:
        st.markdown("#### Acceso Restringido")
        usuario_ing = st.text_input("Usuario Administrador")
        pass_ing = st.text_input("Contrasena", type="password")
        
        if st.button("Iniciar Sesion"):
            if usuario_ing == "Zona Franca Santander" and pass_ing == "ZONAFRANCA123":
                st.session_state.auth_admin = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas. Verifique el usuario y la contrasena.")
    else:
        if st.sidebar.button("Cerrar Sesion"):
            st.session_state.auth_admin = False
            st.rerun()

        st.success("Sesion de Administrador Activa")

        if not st.session_state.turnos:
            st.info("No hay registros pendientes en este momento.")
        else:
            df_admin = pd.DataFrame(st.session_state.turnos)

            st.markdown("#### Gestion de Turnos y Autorizaciones")
            
            turno_sel = st.selectbox("Seleccione la Placa / Turno a Administrar", df_admin["id_turno"] + " - Placa: " + df_admin["placa"] + " (" + df_admin["estado"] + ")")
            id_seleccionado = turno_sel.split(" - ")[0]

            reg_actual = next((item for item in st.session_state.turnos if item["id_turno"] == id_seleccionado), None)

            if reg_actual:
                with st.form("form_admin_autorizacion"):
                    st.markdown(f"**Conductor:** {reg_actual['nombre']} | **Cedula:** {reg_actual['cedula']} | **Bodega:** {reg_actual['bodega']}")
                    st.markdown(f"**Fecha y Hora de Enturnamiento:** {reg_actual['fecha_hora']}")
                    
                    tipo_mov = st.selectbox(
                        "Tipo de Movimiento",
                        ["Ingresar", "Salir"],
                        index=0 if reg_actual.get("tipo_movimiento", "Ingresar") == "Ingresar" else 1
                    )

                    nuevo_estado = st.selectbox(
                        "Estado de Autorizacion",
                        ["En Espera", "AUTORIZADO PARA INGRESAR", "AUTORIZADO PARA SALIR", "Finalizado"],
                        index=0 if reg_actual["estado"] == "En Espera" else 1
                    )
                    
                    mensaje_personalizado = st.text_input("Mensaje / Muelle asignado", value=reg_actual["mensaje_admin"])
                    
                    btn_autorizar = st.form_submit_button("Aplicar Cambios")
                    
                    if btn_autorizar:
                        reg_actual["tipo_movimiento"] = tipo_mov
                        reg_actual["estado"] = nuevo_estado
                        reg_actual["mensaje_admin"] = mensaje_personalizado
                        guardar_datos(st.session_state.turnos)
                        st.success("Cambios aplicados correctamente.")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### Listado General de Vehiculos Registrados")
            
            # Tabla limpia organizada con la fecha y hora incluida para auditoría
            cols_admin_vista = ["id_turno", "placa", "nombre", "cedula", "fecha_hora", "bodega", "tipo_movimiento", "estado", "mensaje_admin"]
            df_admin_tabla = df_admin[cols_admin_vista].rename(columns={
                "id_turno": "Turno",
                "placa": "Placa",
                "nombre": "Conductor",
                "cedula": "Cedula",
                "fecha_hora": "Fecha y Hora",
                "bodega": "Bodega",
                "tipo_movimiento": "Movimiento",
                "estado": "Estado",
                "mensaje_admin": "Mensaje"
            })
            st.dataframe(df_admin_tabla, use_container_width=True, hide_index=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Reiniciar Todos los Turnos"):
                    st.session_state.turnos = []
                    guardar_datos([])
                    st.success("Tablero reiniciado con exito.")
                    st.rerun()
            with col_d2:
                csv_export = df_admin.to_csv(index=False).encode("utf-8")
                st.download_button("Descargar Reporte en CSV", data=csv_export, file_name="control_turnos_zfc.csv", mime="text/csv")
