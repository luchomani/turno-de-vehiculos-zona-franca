import streamlit as st
import database as db

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Control de Ingreso ZFS", page_icon="🚛", layout="centered")

# Inicializar base de datos
db.init_db()

# Variables de sesión para controlar la vista del conductor
if 'turno_actual' not in st.session_state:
    st.session_state.turno_actual = None
if 'placa_actual' not in st.session_state:
    st.session_state.placa_actual = None

# ==========================================
# MENÚ DE NAVEGACIÓN
# ==========================================
st.sidebar.title("Módulos")
opcion = st.sidebar.radio("Navegación", ["👨‍✈️ Portal Conductor", "🛡️ Panel Administrador"])

# ==========================================
# VISTA: CONDUCTOR
# ==========================================
if opcion == "👨‍✈️ Portal Conductor":
    
    # Si el conductor NO ha sacado turno, mostramos el formulario
    if st.session_state.turno_actual is None:
        st.title("Asignación de Turno")
        st.write("Ingrese su placa para registrarse en el sistema.")
        
        placa_input = st.text_input("Placa del Vehículo", max_chars=7, placeholder="Ej: ABC123").upper()
        
        # Botón responsivo para móviles (use_container_width)
        if st.button("Solicitar Turno", type="primary", use_container_width=True):
            if len(placa_input) >= 5:
                turno_id = db.registrar_turno(placa_input)
                # Guardamos los datos en sesión para mostrar el ticket
                st.session_state.turno_actual = turno_id
                st.session_state.placa_actual = placa_input
                st.rerun()
            else:
                st.error("Por favor, ingrese una placa válida.")
                
    # Si el conductor YA sacó turno, mostramos el ticket grande
    else:
        st.markdown("<h3 style='text-align: center; color: gray;'>SU TURNO ASIGNADO ES</h3>", unsafe_allow_html=True)
        
        # Diseño de números grandes adaptado para móviles
        st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #003366;'>{st.session_state.turno_actual:02d}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'>PLACA: {st.session_state.placa_actual}</h2>", unsafe_allow_html=True)
        
        st.info("🕒 Por favor, espere la luz verde del administrador para su ingreso.")
        
        st.markdown("---")
        if st.button("Registrar otro vehículo", use_container_width=True):
            st.session_state.turno_actual = None
            st.session_state.placa_actual = None
            st.rerun()

# ==========================================
# VISTA: ADMINISTRADOR
# ==========================================
elif opcion == "🛡️ Panel Administrador":
    st.title("Panel Operativo de Turnos")
    
    # Control de Autenticación
    if 'admin_auth' not in st.session_state:
        st.session_state.admin_auth = False
        
    if not st.session_state.admin_auth:
        st.info("🔒 Ingrese sus credenciales operativas.")
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True):
            if user == "Zona Franca Santander" and pwd == "ZONAFRANCA123":
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas.")
    
    else:
        # Botón de cierre de sesión
        if st.button("Cerrar Sesión"):
            st.session_state.admin_auth = False
            st.rerun()
            
        st.markdown("---")
        st.subheader("🚦 Vehículos en Espera")
        df_espera = db.obtener_turnos("EN ESPERA")
        
        if not df_espera.empty:
            for index, row in df_espera.iterrows():
                # Diseño en columnas para la lista de turnos
                col_info, col_btn = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Placa:** {row['placa']} | **Turno:** {row['id']:02d}")
                    st.caption(f"Registrado: {row['hora_registro']}")
                    
                with col_btn:
                    # Botón para dar luz verde
                    if st.button("✅ Dar Luz Verde", key=f"btn_{row['id']}", use_container_width=True):
                        db.actualizar_estado(row['id'], "AUTORIZADO")
                        st.rerun()
                st.divider() # Línea separadora entre registros
        else:
            st.success("No hay vehículos en fila de espera.")
            
        st.markdown("---")
        st.subheader("✅ Vehículos Autorizados (Ingresados)")
        df_autorizados = db.obtener_turnos("AUTORIZADO")
        
        if not df_autorizados.empty:
            # Mostrar tabla simplificada
            st.dataframe(df_autorizados[['id', 'placa', 'hora_registro']], hide_index=True, use_container_width=True)
        else:
            st.info("No hay vehículos autorizados recientemente.")
