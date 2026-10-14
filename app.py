# -*- coding: utf-8 -*-
"""
Sistema de Gestión de Turnos y Control de Accesos — Zona Franca Santander
=========================================================================
Roles: Conductor | Vigilante | Operador (Admin)
"""
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# ==========================================================================
# CONFIGURACIÓN
# ==========================================================================
st.set_page_config(
    page_title="Turnos y Accesos | Zona Franca Santander",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================================================
# CSS GLOBAL
# ==========================================================================
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3, h4 { color: #1B4D3E !important; font-family: Arial, sans-serif; }

    input, select, textarea { font-size: 17px !important; padding: 10px !important; }

    .stButton>button {
        background-color: #1B4D3E; color: white; border-radius: 8px;
        border: none; font-weight: bold; font-size: 16px;
        padding: 0.7rem 1.2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background-color: #2C6B56; color: white; }

    .ficho-card {
        background: linear-gradient(135deg, #1B4D3E 0%, #2C6B56 100%);
        color: #FFFFFF; padding: 28px 20px; border-radius: 14px;
        text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        margin: 18px 0;
    }
    .ficho-card h3 { color: #FFFFFF !important; }
    .ficho-card .placa {
        color: #FFD700; font-size: 46px; font-weight: 900;
        letter-spacing: 3px; margin: 8px 0;
    }
    .ficho-card .turno {
        color: #FFFFFF; font-size: 54px; font-weight: 900; margin: 5px 0;
    }
    .ficho-card .info { font-size: 15px; color: #E0E0E0; margin: 4px 0; }

    .estado-badge {
        display: inline-block; padding: 8px 16px; border-radius: 20px;
        font-weight: bold; font-size: 15px;
    }
    .badge-espera { background: #FFF3CD; color: #856404; }
    .badge-autorizado { background: #D4EDDA; color: #155724; }
    .badge-salir { background: #F8D7DA; color: #721C24; }
    .badge-finalizado { background: #E2E3E5; color: #383D41; }

    .tarjeta-ingreso {
        background: #E8F5E9; border: 2px solid #2E7D32;
        padding: 16px; border-radius: 10px; margin-bottom: 12px; text-align: center;
    }
    .tarjeta-salida {
        background: #FFEBEE; border: 2px solid #C62828;
        padding: 16px; border-radius: 10px; margin-bottom: 12px; text-align: center;
    }
    .col-header-ing {
        background: #1B4D3E; color: white; padding: 14px;
        border-radius: 8px 8px 0 0; text-align: center; font-weight: bold;
        font-size: 15px;
    }
    .col-header-sal {
        background: #B71C1C; color: white; padding: 14px;
        border-radius: 8px 8px 0 0; text-align: center; font-weight: bold;
        font-size: 15px;
    }
    .empty-state {
        background: #EFEFEF; padding: 20px; text-align: center; color: #666;
        border-radius: 0 0 8px 8px; font-style: italic;
    }
    .role-card {
        background: white; border: 2px solid #E1E8E5; border-radius: 12px;
        padding: 30px 20px; text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .role-card .icon { font-size: 48px; margin-bottom: 10px; }
    .role-card .titulo { font-size: 20px; font-weight: bold; color: #1B4D3E; }
    .role-card .desc { font-size: 13px; color: #666; margin-top: 6px; }

    div[data-testid="stMetricValue"] { color: #1B4D3E; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ==========================================================================
# CAPA DE DATOS (JSON persistente)
# ==========================================================================
DATA_FILE = "turnos_zfc.json"
CONFIG_FILE = "config_zfc.json"

DEFAULT_CONFIG = {
    "tiempo_en_pantalla_min": 30,
    "usuario_admin": "Zona Franca Santander",
    "contrasena_admin": "ZONAFRANCA123",
    "usuario_vigilante": "Vigilante",
    "contrasena_vigilante": "VIGILANTE2026",
    "bodegas": [
        "Bodega Principal / Generica",
        "Alfranca Cucuta S.A.S.",
        "Inversiones Cargamax HYJ S.A.S.",
        "Logistica Aduanera J.H. Ltda.",
        "Setracomex S.A.S.",
        "Otra Bodega / Operador",
    ],
}

def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                for item in datos:
                    _migrar_campos(item)
                return datos
        except Exception:
            return []
    return []

def _migrar_campos(item):
    """Garantiza que todos los registros tengan los campos actuales."""
    defaults = {
        "tipo_movimiento": "Ingresar",
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mostrar_en_pantalla": False,
        "fecha_autorizacion": None,
        "fecha_ingreso_zf": None,
        "fecha_salida_zf": None,
        "checklist_ingreso": {},
        "checklist_salida": {},
        "observaciones_vigilante": "",
    }
    for k, v in defaults.items():
        item.setdefault(k, v)

def guardar_datos(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def guardar_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ==========================================================================
# HELPERS
# ==========================================================================
def ahora_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_fecha(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def debe_ocultar_por_tiempo(turno, cfg):
    """Determina si un turno autorizado debe ocultarse por tiempo."""
    if not turno.get("mostrar_en_pantalla"):
        return True
    fa = parse_fecha(turno.get("fecha_autorizacion"))
    if fa is None:
        return False
    limite = timedelta(minutes=cfg.get("tiempo_en_pantalla_min", 30))
    return (datetime.now() - fa) > limite

def badge_estado(estado_raw):
    e = (estado_raw or "").upper()
    if "INGRESAR" in e and "ZONA" not in e:
        return "badge-autorizado", "AUTORIZADO PARA INGRESAR"
    if "SALIR" in e and "ZONA" not in e:
        return "badge-salir", "AUTORIZADO PARA SALIR"
    if "ZONA FRANCA" in e:
        return "badge-finalizado", "EN ZONA FRANCA"
    if "FINALIZADO" in e:
        return "badge-finalizado", "FINALIZADO"
    return "badge-espera", "EN ESPERA"

def render_ticket(turno):
    """Renderiza la tarjeta del tiquet para el conductor."""
    badge_cls, badge_txt = badge_estado(turno.get("estado", ""))
    mensaje = turno.get("mensaje_admin", "") or "—"

    st.markdown(f"""
    <div class="ficho-card">
        <div class="info" style="font-size:12px; letter-spacing:2px;">TURNO ASIGNADO</div>
        <div class="info" style="font-size:13px; margin-top:10px;">PLACA DEL VEHÍCULO</div>
        <div class="placa">{turno.get('placa','—')}</div>
        <hr style="border-color: rgba(255,255,255,0.25); margin: 16px 0;">
        <div class="info" style="font-size:13px;">NÚMERO DE FICHO</div>
        <div class="turno">{turno.get('id_turno','—')}</div>
        <div class="info" style="margin-top:16px;"><b>Destino:</b> {turno.get('bodega','—')}</div>
        <div class="info"><b>Movimiento:</b> {turno.get('tipo_movimiento','Ingresar')}</div>
        <div class="info" style="font-size:12px; color:#CCCCCC; margin-top:8px;">
            Registrado: {turno.get('fecha_hora','—')}
        </div>
        <div style="margin-top:16px;">
            <span class="estado-badge {badge_cls}">{badge_txt}</span>
        </div>
        <div style="background: rgba(255,255,255,0.12); padding:10px; border-radius:8px; margin-top:14px;">
            <div class="info" style="font-size:11px; letter-spacing:1px;">MENSAJE DEL OPERADOR</div>
            <div style="color:#FFD700; font-weight:bold; font-size:15px; margin-top:4px;">{mensaje}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def buscar_turno(turnos, id_turno):
    return next((t for t in turnos if t.get("id_turno") == id_turno), None)

# ==========================================================================
# SESSION STATE
# ==========================================================================
if "rol" not in st.session_state:
    st.session_state.rol = None
if "auth_operador" not in st.session_state:
    st.session_state.auth_operador = False
if "auth_vigilante" not in st.session_state:
    st.session_state.auth_vigilante = False
if "mi_turno_id" not in st.session_state:
    st.session_state.mi_turno_id = None

# Persistencia del turno vía query params (sobrevive refresh)
try:
    qp = st.query_params
    if st.session_state.mi_turno_id is None and "t" in qp:
        st.session_state.mi_turno_id = qp.get("t")
except Exception:
    pass

CONFIG = cargar_config()

# ==========================================================================
# HEADER + BOTÓN CAMBIAR ROL
# ==========================================================================
col_head_l, col_head_r = st.columns([4, 1])
with col_head_l:
    st.markdown("## 🚛 Zona Franca Santander")
    st.caption("Sistema de Enturnamiento y Control de Accesos — Cúcuta")
with col_head_r:
    if st.session_state.rol is not None:
        if st.button("🔄 Cambiar Rol", use_container_width=True):
            st.session_state.rol = None
            st.session_state.auth_operador = False
            st.session_state.auth_vigilante = False
            st.session_state.mi_turno_id = None
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

st.divider()

# ==========================================================================
# SELECTOR DE ROL
# ==========================================================================
if st.session_state.rol is None:
    st.markdown("### 👋 Selecciona tu Portal de Acceso")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="role-card">
            <div class="icon">👤</div>
            <div class="titulo">Conductor</div>
            <div class="desc">Regístrate, obtén tu turno y consulta tu estado</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Ingresar como Conductor", use_container_width=True, key="btn_rol_cond"):
            st.session_state.rol = "conductor"
            st.rerun()

    with c2:
        st.markdown("""
        <div class="role-card">
            <div class="icon">🛡️</div>
            <div class="titulo">Vigilante</div>
            <div class="desc">Verifica el ingreso y salida de vehículos con checklist</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Ingresar como Vigilante", use_container_width=True, key="btn_rol_vig"):
            st.session_state.rol = "vigilante"
            st.rerun()

    with c3:
        st.markdown("""
        <div class="role-card">
            <div class="icon">⚙️</div>
            <div class="titulo">Operador</div>
            <div class="desc">Autoriza turnos, controla la pantalla y gestiona todo</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Ingresar como Operador", use_container_width=True, key="btn_rol_op"):
            st.session_state.rol = "operador"
            st.rerun()

    st.stop()


# ==========================================================================
# PORTAL DEL CONDUCTOR
# ==========================================================================
if st.session_state.rol == "conductor":

    # Vista centrada tipo móvil
    left, center, right = st.columns([1, 2, 1])

    with center:
        st.markdown("### 👤 Portal del Conductor")

        # Refrescar datos
        turnos = cargar_datos()

        # Verificar si el conductor ya tiene un turno activo
        mi_turno = None
        if st.session_state.mi_turno_id:
            mi_turno = buscar_turno(turnos, st.session_state.mi_turno_id)
            # Si el turno fue finalizado, ofrecer nuevo registro
            if mi_turno and "FINALIZADO" in (mi_turno.get("estado", "").upper()):
                st.info("✅ Tu turno anterior fue finalizado. Puedes registrar un nuevo vehículo.")

        # -------- SI TIENE TURNO ACTIVO --------
        if mi_turno and "FINALIZADO" not in mi_turno.get("estado", "").upper():
            st.markdown("#### 🎫 Tu Tiquet")

            # Auto-refresh cada 5 segundos
            @st.fragment(run_every=5)
            def mostrar_tiquet_vivo():
                turnos_vivos = cargar_datos()
                actual = buscar_turno(turnos_vivos, st.session_state.mi_turno_id)
                if actual:
                    render_ticket(actual)
                else:
                    st.warning("Tu turno ya no está disponible.")

            mostrar_tiquet_vivo()

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Actualizar Estado", use_container_width=True):
                    st.rerun()
            with col_b:
                if st.button("➕ Registrar otro vehículo", use_container_width=True):
                    st.session_state.mi_turno_id = None
                    try:
                        st.query_params.clear()
                    except Exception:
                        pass
                    st.rerun()

            # Tablero reducido (solo vehículos autorizados en pantalla)
            st.markdown("---")
            st.markdown("#### 📺 Vehículos Autorizados en Pantalla")

            @st.fragment(run_every=4)
            def tablero_publico_conductor():
                turnos_v = cargar_datos()
                cfg = cargar_config()

                def visible(t):
                    if not t.get("mostrar_en_pantalla"):
                        return False
                    if debe_ocultar_por_tiempo(t, cfg):
                        return False
                    est = (t.get("estado") or "").upper()
                    return "INGRESAR" in est or "SALIR" in est

                autorizados = [t for t in turnos_v if visible(t)]
                ingresos = [t for t in autorizados if "INGRESAR" in (t.get("estado") or "").upper()]
                salidas = [t for t in autorizados if "SALIR" in (t.get("estado") or "").upper()]

                col_i, col_s = st.columns(2)

                with col_i:
                    st.markdown('<div class="col-header-ing">AUTORIZADOS PARA INGRESAR</div>', unsafe_allow_html=True)
                    if not ingresos:
                        st.markdown('<div class="empty-state">No hay vehículos para ingresar.</div>', unsafe_allow_html=True)
                    else:
                        for t in ingresos:
                            st.markdown(f"""
                            <div class="tarjeta-ingreso">
                                <div style="font-size:13px; font-weight:bold; color:#2E7D32;">Ficho: {t['id_turno']}</div>
                                <div style="font-size:28px; font-weight:900; color:#1B4D3E; letter-spacing:2px;">{t['placa']}</div>
                                <div style="font-size:13px; color:#333;"><b>Destino:</b> {t['bodega']}</div>
                                <div style="font-size:12px; background:#C8E6C9; color:#000; padding:2px 8px; border-radius:4px; display:inline-block; margin-top:6px;">
                                    <b>{t.get('mensaje_admin','') or '—'}</b>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                with col_s:
                    st.markdown('<div class="col-header-sal">AUTORIZADOS PARA SALIR</div>', unsafe_allow_html=True)
                    if not salidas:
                        st.markdown('<div class="empty-state">No hay vehículos para salir.</div>', unsafe_allow_html=True)
                    else:
                        for t in salidas:
                            st.markdown(f"""
                            <div class="tarjeta-salida">
                                <div style="font-size:13px; font-weight:bold; color:#C62828;">Ficho: {t['id_turno']}</div>
                                <div style="font-size:28px; font-weight:900; color:#B71C1C; letter-spacing:2px;">{t['placa']}</div>
                                <div style="font-size:13px; color:#333;"><b>Destino:</b> {t['bodega']}</div>
                                <div style="font-size:12px; background:#FFCDD2; color:#000; padding:2px 8px; border-radius:4px; display:inline-block; margin-top:6px;">
                                    <b>{t.get('mensaje_admin','') or '—'}</b>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            tablero_publico_conductor()

        # -------- SI NO TIENE TURNO: FORMULARIO --------
        else:
            st.markdown("Por favor ingresa tus datos para asignarte un turno.")
            st.caption("💡 Los campos con (*) son obligatorios")

            with st.form("form_conductor", clear_on_submit=False):
                placa = st.text_input("Placa del Vehículo * (Ej: ABC123)").upper().strip()
                nombre = st.text_input("Nombre Completo del Conductor *").title().strip()
                cedula = st.text_input("Número de Cédula *").strip()
                telefono = st.text_input("Teléfono de contacto (opcional)").strip()

                bodega = st.selectbox(
                    "Bodega de Destino *",
                    ["Seleccione una bodega..."] + CONFIG.get("bodegas", []),
                )

                submitted = st.form_submit_button("🎫 Obtener mi Turno")

                if submitted:
                    if not placa or not nombre or not cedula or bodega == "Seleccione una bodega...":
                        st.error("⚠️ Por favor complete todos los campos obligatorios (*).")
                    else:
                        turnos_actuales = cargar_datos()

                        # Evitar duplicados activos de la misma placa
                        activo = next(
                            (t for t in turnos_actuales
                             if t["placa"] == placa and "FINALIZADO" not in (t.get("estado") or "").upper()),
                            None,
                        )
                        if activo:
                            st.warning(f"⚠️ La placa {placa} ya tiene un turno activo: {activo['id_turno']}.")
                            st.session_state.mi_turno_id = activo["id_turno"]
                            st.rerun()
                        else:
                            nuevo_id = len(turnos_actuales) + 1
                            turno_str = f"T-{nuevo_id:03d}"

                            nuevo_registro = {
                                "id_turno": turno_str,
                                "placa": placa,
                                "nombre": nombre,
                                "cedula": cedula,
                                "telefono": telefono,
                                "bodega": bodega,
                                "tipo_movimiento": "Ingresar",
                                "estado": "En Espera",
                                "fecha_hora": ahora_str(),
                                "mensaje_admin": "En espera de autorización",
                                "mostrar_en_pantalla": False,
                                "fecha_autorizacion": None,
                                "fecha_ingreso_zf": None,
                                "fecha_salida_zf": None,
                                "checklist_ingreso": {},
                                "checklist_salida": {},
                                "observaciones_vigilante": "",
                            }

                            turnos_actuales.append(nuevo_registro)
                            guardar_datos(turnos_actuales)

                            st.session_state.mi_turno_id = turno_str
                            try:
                                st.query_params["t"] = turno_str
                            except Exception:
                                pass

                            st.success("✅ Turno asignado correctamente.")
                            st.rerun()

        # Botón para recuperar turno por placa (si perdió el enlace)
        st.markdown("---")
        with st.expander("🔍 Recuperar mi turno por placa"):
            placa_buscar = st.text_input("Ingresa tu placa", key="recuperar_placa").upper().strip()
            if st.button("Buscar", key="btn_recuperar"):
                turnos_b = cargar_datos()
                encontrado = next(
                    (t for t in reversed(turnos_b)
                     if t["placa"] == placa_buscar and "FINALIZADO" not in (t.get("estado") or "").upper()),
                    None,
                )
                if encontrado:
                    st.session_state.mi_turno_id = encontrado["id_turno"]
                    try:
                        st.query_params["t"] = encontrado["id_turno"]
                    except Exception:
                        pass
                    st.rerun()
                else:
                    st.error("No se encontró un turno activo para esa placa.")


# ==========================================================================
# PORTAL DEL VIGILANTE
# ==========================================================================
elif st.session_state.rol == "vigilante":

    st.markdown("### 🛡️ Portal del Vigilante")

    if not st.session_state.auth_vigilante:
        st.markdown("#### Acceso Restringido")
        with st.form("form_vigilante"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar Sesión"):
                if (u == CONFIG.get("usuario_vigilante") and
                        p == CONFIG.get("contrasena_vigilante")):
                    st.session_state.auth_vigilante = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")
        st.stop()

    # --- Vigilante autenticado ---
    st.success("✅ Sesión de Vigilante Activa")

    @st.fragment(run_every=5)
    def panel_vigilante():
        turnos = cargar_datos()

        # Ingresos pendientes de check
        en_ingreso = [
            t for t in turnos
            if "INGRESAR" in (t.get("estado") or "").upper()
            and "ZONA" not in (t.get("estado") or "").upper()
            and not t.get("fecha_ingreso_zf")
        ]
        # Salidas pendientes de check
        en_salida = [
            t for t in turnos
            if "SALIR" in (t.get("estado") or "").upper()
            and "FINALIZADO" not in (t.get("estado") or "").upper()
            and not t.get("fecha_salida_zf")
        ]

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Pendientes de Ingreso", len(en_ingreso))
        m2.metric("Pendientes de Salida", len(en_salida))
        m3.metric("Total en Sistema", len(turnos))

        st.markdown("---")

        CHECKLIST_ING = [
            ("placa_correcta", "Placa del vehículo corresponde"),
            ("documentos", "Documentos del conductor verificados"),
            ("sellos", "Sellos/precintos intactos"),
            ("carga", "Carga coincide con manifiesto"),
            ("sin_novedad", "Sin novedades de seguridad"),
        ]
        CHECKLIST_SAL = [
            ("placa_correcta", "Placa del vehículo corresponde"),
            ("documentos", "Documentos del conductor verificados"),
            ("carga_completa", "Carga completa/sellada"),
            ("sin_novedad", "Sin novedades de seguridad"),
            ("salida_autorizada", "Salida autorizada por operador"),
        ]

        col_i, col_s = st.columns(2)

        with col_i:
            st.markdown('<div class="col-header-ing">CHECK IN — INGRESOS</div>', unsafe_allow_html=True)
            if not en_ingreso:
                st.markdown('<div class="empty-state">Sin vehículos pendientes de ingreso.</div>', unsafe_allow_html=True)
            else:
                for t in en_ingreso:
                    with st.expander(f"🚛 {t['placa']} — {t['id_turno']}", expanded=False):
                        st.markdown(f"**Conductor:** {t.get('nombre','')} — C.C. {t.get('cedula','')}")
                        st.markdown(f"**Bodega:** {t.get('bodega','')}")
                        st.caption(f"Registrado: {t.get('fecha_hora','')}")

                        with st.form(f"check_in_{t['id_turno']}"):
                            checks = {}
                            for k, label in CHECKLIST_ING:
                                checks[k] = st.checkbox(label, key=f"in_{t['id_turno']}_{k}")

                            obs = st.text_area("Observaciones (opcional)", key=f"obs_in_{t['id_turno']}")

                            if st.form_submit_button("✅ Confirmar Ingreso"):
                                if all(checks.values()):
                                    for x in turnos:
                                        if x["id_turno"] == t["id_turno"]:
                                            x["checklist_ingreso"] = checks
                                            x["observaciones_vigilante"] = obs
                                            x["fecha_ingreso_zf"] = ahora_str()
                                            x["estado"] = "EN ZONA FRANCA"
                                            x["mostrar_en_pantalla"] = False
                                            break
                                    guardar_datos(turnos)
                                    st.success(f"Ingreso confirmado para {t['placa']}")
                                    st.rerun()
                                else:
                                    st.error("⚠️ Debes marcar todos los items del checklist.")

        with col_s:
            st.markdown('<div class="col-header-sal">CHECK OUT — SALIDAS</div>', unsafe_allow_html=True)
            if not en_salida:
                st.markdown('<div class="empty-state">Sin vehículos pendientes de salida.</div>', unsafe_allow_html=True)
            else:
                for t in en_salida:
                    with st.expander(f"🚛 {t['placa']} — {t['id_turno']}", expanded=False):
                        st.markdown(f"**Conductor:** {t.get('nombre','')} — C.C. {t.get('cedula','')}")
                        st.markdown(f"**Bodega:** {t.get('bodega','')}")

                        with st.form(f"check_out_{t['id_turno']}"):
                            checks = {}
                            for k, label in CHECKLIST_SAL:
                                checks[k] = st.checkbox(label, key=f"out_{t['id_turno']}_{k}")

                            obs = st.text_area("Observaciones (opcional)", key=f"obs_out_{t['id_turno']}")

                            if st.form_submit_button("✅ Confirmar Salida"):
                                if all(checks.values()):
                                    for x in turnos:
                                        if x["id_turno"] == t["id_turno"]:
                                            x["checklist_salida"] = checks
                                            x["observaciones_vigilante"] = (
                                                (x.get("observaciones_vigilante") or "") + " | " + obs
                                            ).strip(" |")
                                            x["fecha_salida_zf"] = ahora_str()
                                            x["estado"] = "FINALIZADO"
                                            x["mostrar_en_pantalla"] = False
                                            break
                                    guardar_datos(turnos)
                                    st.success(f"Salida confirmada para {t['placa']}")
                                    st.rerun()
                                else:
                                    st.error("⚠️ Debes marcar todos los items del checklist.")

    panel_vigilante()


# ==========================================================================
# PORTAL DEL OPERADOR (ADMIN)
# ==========================================================================
elif st.session_state.rol == "operador":

    st.markdown("### ⚙️ Panel del Operador")

    if not st.session_state.auth_operador:
        st.markdown("#### Acceso Restringido")
        with st.form("form_operador"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar Sesión"):
                if (u == CONFIG.get("usuario_admin") and
                        p == CONFIG.get("contrasena_admin")):
                    st.session_state.auth_operador = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")
        st.stop()

    # --- Operador autenticado ---
    st.success("✅ Sesión de Operador Activa")

    tab_board, tab_gestion, tab_config, tab_historial = st.tabs([
        "📺 Pantalla Pública", "🎛️ Gestión de Turnos", "⚙️ Configuración", "📊 Historial"
    ])

    # ---------------------------------------------------------------
    # TAB 1: PANTALLA PÚBLICA
    # ---------------------------------------------------------------
    with tab_board:
        st.markdown("#### 📺 Control de Pantalla Pública")
        st.caption(
            f"Los vehículos mostrados se ocultan automáticamente después de "
            f"**{CONFIG.get('tiempo_en_pantalla_min', 30)} minutos** desde su autorización. "
            "Puedes activar/desactivar cada uno manualmente."
        )

        @st.fragment(run_every=5)
        def board_publico():
            turnos_b = cargar_datos()
            cfg = cargar_config()

            def visible(t):
                if not t.get("mostrar_en_pantalla"):
                    return False
                if debe_ocultar_por_tiempo(t, cfg):
                    return False
                est = (t.get("estado") or "").upper()
                return "INGRESAR" in est or "SALIR" in est

            autorizados = [t for t in turnos_b if visible(t)]
            ingresos = [t for t in autorizados if "INGRESAR" in (t.get("estado") or "").upper()]
            salidas = [t for t in autorizados if "SALIR" in (t.get("estado") or "").upper()]

            col_i, col_s = st.columns(2)

            with col_i:
                st.markdown('<div class="col-header-ing">AUTORIZADOS PARA INGRESAR</div>', unsafe_allow_html=True)
                if not ingresos:
                    st.markdown('<div class="empty-state">No hay vehículos visibles.</div>', unsafe_allow_html=True)
                else:
                    for t in ingresos:
                        st.markdown(f"""
                        <div class="tarjeta-ingreso">
                            <div style="font-size:13px; font-weight:bold; color:#2E7D32;">Ficho: {t['id_turno']}</div>
                            <div style="font-size:28px; font-weight:900; color:#1B4D3E; letter-spacing:2px;">{t['placa']}</div>
                            <div style="font-size:13px; color:#333;"><b>Destino:</b> {t['bodega']}</div>
                            <div style="font-size:12px; color:#333;"><b>Aviso:</b> {t.get('mensaje_admin','') or '—'}</div>
                        </div>
                        """, unsafe_allow_html=True)

            with col_s:
                st.markdown('<div class="col-header-sal">AUTORIZADOS PARA SALIR</div>', unsafe_allow_html=True)
                if not salidas:
                    st.markdown('<div class="empty-state">No hay vehículos visibles.</div>', unsafe_allow_html=True)
                else:
                    for t in salidas:
                        st.markdown(f"""
                        <div class="tarjeta-salida">
                            <div style="font-size:13px; font-weight:bold; color:#C62828;">Ficho: {t['id_turno']}</div>
                            <div style="font-size:28px; font-weight:900; color:#B71C1C; letter-spacing:2px;">{t['placa']}</div>
                            <div style="font-size:13px; color:#333;"><b>Destino:</b> {t['bodega']}</div>
                            <div style="font-size:12px; color:#333;"><b>Aviso:</b> {t.get('mensaje_admin','') or '—'}</div>
                        </div>
                        """, unsafe_allow_html=True)

        board_publico()

    # ---------------------------------------------------------------
    # TAB 2: GESTIÓN DE TURNOS
    # ---------------------------------------------------------------
    with tab_gestion:
        st.markdown("#### 🎛️ Gestión de Turnos")

        turnos_g = cargar_datos()
        if not turnos_g:
            st.info("No hay turnos registrados.")
        else:
            # Filtros rápidos
            filtro = st.selectbox(
                "Filtrar por estado:",
                ["Todos", "En Espera", "Autorizados", "En Zona Franca", "Finalizados"],
                key="filtro_estado_op",
            )

            def aplicar_filtro(lst):
                if filtro == "Todos":
                    return lst
                if filtro == "En Espera":
                    return [t for t in lst if "ESPERA" in (t.get("estado") or "").upper()]
                if filtro == "Autorizados":
                    return [t for t in lst if "AUTORIZADO" in (t.get("estado") or "").upper()]
                if filtro == "En Zona Franca":
                    return [t for t in lst if "ZONA FRANCA" in (t.get("estado") or "").upper()]
                if filtro == "Finalizados":
                    return [t for t in lst if "FINALIZADO" in (t.get("estado") or "").upper()]
                return lst

            lista = aplicar_filtro(turnos_g)

            # Selección de turno para editar
            if lista:
                opciones = [f"{t['id_turno']} — {t['placa']} — {t['estado']}" for t in lista]
                sel = st.selectbox("Selecciona un turno para gestionar:", opciones, key="sel_turno_op")
                id_sel = sel.split(" — ")[0]
                turno_sel = buscar_turno(turnos_g, id_sel)

                if turno_sel:
                    with st.form(f"form_gestion_{id_sel}"):
                        st.markdown(f"**Conductor:** {turno_sel.get('nombre','')} | C.C. {turno_sel.get('cedula','')}")
                        st.markdown(f"**Placa:** {turno_sel.get('placa','')} | **Bodega:** {turno_sel.get('bodega','')}")
                        st.markdown(f"**Registrado:** {turno_sel.get('fecha_hora','')}")

                        nuevo_tipo = st.selectbox(
                            "Tipo de movimiento",
                            ["Ingresar", "Salir"],
                            index=0 if turno_sel.get("tipo_movimiento") == "Ingresar" else 1,
                        )

                        nuevo_estado = st.selectbox(
                            "Estado",
                            [
                                "En Espera",
                                "AUTORIZADO PARA INGRESAR",
                                "AUTORIZADO PARA SALIR",
                                "EN ZONA FRANCA",
                                "FINALIZADO",
                            ],
                            index=[
                                "En Espera", "AUTORIZADO PARA INGRESAR",
                                "AUTORIZADO PARA SALIR", "EN ZONA FRANCA", "FINALIZADO"
                            ].index(turno_sel.get("estado", "En Espera"))
                            if turno_sel.get("estado", "En Espera") in [
                                "En Espera", "AUTORIZADO PARA INGRESAR",
                                "AUTORIZADO PARA SALIR", "EN ZONA FRANCA", "FINALIZADO"
                            ] else 0,
                        )

                        mensaje = st.text_input(
                            "Mensaje para el conductor (ej: Muelle 3)",
                            value=turno_sel.get("mensaje_admin", ""),
                        )

                        mostrar = st.checkbox(
                            "📺 Mostrar en pantalla pública",
                            value=bool(turno_sel.get("mostrar_en_pantalla", False)),
                            help="Desmarca para ocultar manualmente, o el sistema lo ocultará automáticamente por tiempo.",
                        )

                        eliminar = st.checkbox("🗑️ Eliminar este turno permanentemente")

                        if st.form_submit_button("💾 Guardar Cambios"):
                            if eliminar:
                                turnos_g = [t for t in turnos_g if t["id_turno"] != id_sel]
                                guardar_datos(turnos_g)
                                st.success(f"Turno {id_sel} eliminado.")
                                st.rerun()
                            else:
                                for t in turnos_g:
                                    if t["id_turno"] == id_sel:
                                        t["tipo_movimiento"] = nuevo_tipo
                                        # Si cambió a autorizado y antes no lo estaba, marcar fecha_autorizacion
                                        antes = t.get("estado", "")
                                        t["estado"] = nuevo_estado
                                        t["mensaje_admin"] = mensaje
                                        t["mostrar_en_pantalla"] = mostrar

                                        if ("AUTORIZADO" in nuevo_estado.upper() and
                                                "AUTORIZADO" not in antes.upper()):
                                            t["fecha_autorizacion"] = ahora_str()
                                        break
                                guardar_datos(turnos_g)
                                st.success("Cambios guardados.")
                                st.rerun()

                # Gestión rápida (toggle mostrar en pantalla en tabla)
                st.markdown("---")
                st.markdown("##### 📺 Alternar visibilidad en pantalla (rápido)")
                st.caption("Marca o desmarca para controlar qué vehículos aparecen en el tablero público.")

                df_quick = pd.DataFrame([
                    {
                        "Turno": t["id_turno"],
                        "Placa": t["placa"],
                        "Estado": t["estado"],
                        "Visible": bool(t.get("mostrar_en_pantalla", False)),
                    }
                    for t in turnos_g
                ])

                edited = st.data_editor(
                    df_quick,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["Turno", "Placa", "Estado"],
                    column_config={
                        "Visible": st.column_config.CheckboxColumn(
                            "📺 En pantalla",
                            help="Marcar para mostrar en el tablero público",
                        )
                    },
                    key="data_editor_visible",
                )

                if st.button("💾 Aplicar cambios de visibilidad", key="aplicar_vis"):
                    for _, row in edited.iterrows():
                        for t in turnos_g:
                            if t["id_turno"] == row["Turno"]:
                                t["mostrar_en_pantalla"] = bool(row["Visible"])
                                break
                    guardar_datos(turnos_g)
                    st.success("Visibilidad actualizada.")
                    st.rerun()

            else:
                st.info("No hay turnos que coincidan con el filtro.")

    # ---------------------------------------------------------------
    # TAB 3: CONFIGURACIÓN
    # ---------------------------------------------------------------
    with tab_config:
        st.markdown("#### ⚙️ Configuración del Sistema")

        with st.form("form_config"):
            st.markdown("**⏱️ Tiempo en pantalla**")
            tiempo = st.number_input(
                "Minutos que un vehículo permanece visible en pantalla tras su autorización",
                min_value=1, max_value=240,
                value=int(CONFIG.get("tiempo_en_pantalla_min", 30)),
            )

            st.markdown("---")
            st.markdown("**🔐 Credenciales Operador**")
            u_admin = st.text_input("Usuario Admin", value=CONFIG.get("usuario_admin", ""))
            p_admin = st.text_input("Contraseña Admin", value=CONFIG.get("contrasena_admin", ""), type="password")

            st.markdown("---")
            st.markdown("**🛡️ Credenciales Vigilante**")
            u_vig = st.text_input("Usuario Vigilante", value=CONFIG.get("usuario_vigilante", ""))
            p_vig = st.text_input("Contraseña Vigilante", value=CONFIG.get("contrasena_vigilante", ""), type="password")

            st.markdown("---")
            st.markdown("**🏢 Bodegas disponibles** (una por línea)")
            bodegas_txt = st.text_area(
                "Lista de bodegas",
                value="\n".join(CONFIG.get("bodegas", [])),
                height=150,
            )

            if st.form_submit_button("💾 Guardar Configuración"):
                cfg = {
                    "tiempo_en_pantalla_min": int(tiempo),
                    "usuario_admin": u_admin,
                    "contrasena_admin": p_admin,
                    "usuario_vigilante": u_vig,
                    "contrasena_vigilante": p_vig,
                    "bodegas": [l.strip() for l in bodegas_txt.split("\n") if l.strip()],
                }
                guardar_config(cfg)
                st.success("✅ Configuración guardada.")
                st.rerun()

        st.markdown("---")
        st.markdown("**🧹 Acciones peligrosas**")
        if st.button("🗑️ Reiniciar TODOS los turnos (irreversible)"):
            guardar_datos([])
            st.warning("Todos los turnos han sido eliminados.")
            st.rerun()

    # ---------------------------------------------------------------
    # TAB 4: HISTORIAL
    # ---------------------------------------------------------------
    with tab_historial:
        st.markdown("#### 📊 Historial General de Turnos")

        turnos_h = cargar_datos()
        if not turnos_h:
            st.info("No hay turnos registrados.")
        else:
            df = pd.DataFrame(turnos_h)

            # Métricas
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total", len(df))
            m2.metric("En Espera", len(df[df["estado"].astype(str).str.contains("Espera", case=False, na=False)]))
            m3.metric("Autorizados", len(df[df["estado"].astype(str).str.contains("AUTORIZADO", case=False, na=False)]))
            m4.metric("Finalizados", len(df[df["estado"].astype(str).str.contains("FINALIZADO", case=False, na=False)]))

            st.markdown("---")

            cols_mostrar = [
                "id_turno", "placa", "nombre", "cedula", "fecha_hora",
                "bodega", "tipo_movimiento", "estado", "mensaje_admin",
                "fecha_autorizacion", "fecha_ingreso_zf", "fecha_salida_zf",
                "observaciones_vigilante",
            ]
            cols_disponibles = [c for c in cols_mostrar if c in df.columns]

            df_vista = df[cols_disponibles].rename(columns={
                "id_turno": "Turno",
                "placa": "Placa",
                "nombre": "Conductor",
                "cedula": "Cédula",
                "fecha_hora": "Fecha Registro",
                "bodega": "Bodega",
                "tipo_movimiento": "Movimiento",
                "estado": "Estado",
                "mensaje_admin": "Mensaje",
                "fecha_autorizacion": "Autorizado",
                "fecha_ingreso_zf": "Ingreso ZF",
                "fecha_salida_zf": "Salida ZF",
                "observaciones_vigilante": "Observaciones",
            })

            st.dataframe(df_vista, use_container_width=True, hide_index=True, height=450)

            st.markdown("---")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                csv = df_vista.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Descargar CSV",
                    data=csv,
                    file_name=f"turnos_zfc_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with col_d2:
                if st.button("🔄 Actualizar Historial", use_container_width=True):
                    st.rerun()
