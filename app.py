# -*- coding: utf-8 -*-
"""
Sistema de Gestión de Turnos y Control de Accesos
Zona Franca Santander — Cúcuta
=================================================
Portales: Conductor | Vigilante | Operador | Pantalla Pública
Acceso vía query param: ?modo=conductor|vigilante|operador|pantalla
"""
import os
import json
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import streamlit as st

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

# ==========================================================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================================================
st.set_page_config(
    page_title="Turnos y Accesos | Zona Franca Santander",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================================================
# CSS CORPORATIVO
# ==========================================================================
st.markdown("""
<style>
    :root {
        --zfc-green-dark:  #12402A;
        --zfc-green-main:  #1B4D3E;
        --zfc-green-mid:   #2C6B56;
        --zfc-bg:          #F5F7F6;
        --zfc-card:        #FFFFFF;
        --zfc-text:        #2C3E50;
        --zfc-text-soft:   #6B7280;
        --zfc-border:      #E1E8E5;
        --zfc-danger:      #9B1C1C;
    }

    .stApp { background-color: var(--zfc-bg); }

    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: var(--zfc-text) !important;
    }

    h1, h2, h3, h4 {
        color: var(--zfc-green-dark) !important;
        font-weight: 700;
        letter-spacing: -0.3px;
    }

    .stTextInput label,
    .stSelectbox label,
    .stTextArea label,
    .stNumberInput label {
        color: #2C3E50 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background-color: #FFFFFF !important;
        color: #1B1B1B !important;
        border: 1.5px solid #C9D1CC !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 12px 14px !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder,
    .stNumberInput > div > div > input::placeholder {
        color: #9CA3AF !important;
        opacity: 1 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1B4D3E !important;
        box-shadow: 0 0 0 2px rgba(27,77,62,0.15) !important;
    }

    .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #C9D1CC !important;
        border-radius: 8px !important;
        color: #1B1B1B !important;
    }
    .stSelectbox > div > div > div { color: #1B1B1B !important; }

    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"] ul { background-color: #FFFFFF !important; }
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li {
        color: #1B1B1B !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] li:hover {
        background-color: #E6F0EB !important;
        color: #12402A !important;
    }

    .stButton>button {
        background-color: var(--zfc-green-main) !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        border: none;
        font-weight: 700;
        font-size: 16px;
        padding: 0.8rem 1.2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .stButton>button:hover {
        background-color: var(--zfc-green-mid) !important;
        color: #FFFFFF !important;
    }

    .stFormSubmitButton > button {
        background-color: var(--zfc-green-main) !important;
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 17px;
        padding: 0.9rem 1.5rem;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #EDF1EE;
        border-radius: 6px 6px 0 0;
        padding: 10px 18px;
        font-weight: 600;
        color: #2C3E50;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--zfc-green-main) !important;
        color: #FFFFFF !important;
    }

    .ticket-card {
        background: linear-gradient(135deg, #12402A 0%, #1B4D3E 100%);
        color: #FFFFFF;
        padding: 32px 24px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(18,64,42,0.25);
        margin: 18px 0;
        border: 1px solid #0D2F1E;
    }
    .ticket-label {
        font-size: 11px;
        letter-spacing: 3px;
        color: #C7D5CD;
        font-weight: 600;
        text-transform: uppercase;
    }
    .ticket-placa {
        color: #FFD966;
        font-size: 44px;
        font-weight: 900;
        letter-spacing: 4px;
        margin: 6px 0;
        font-family: 'Courier New', monospace;
    }
    .ticket-turno {
        color: #FFFFFF;
        font-size: 52px;
        font-weight: 900;
        margin: 4px 0;
        font-family: 'Courier New', monospace;
    }
    .ticket-info { font-size: 14px; color: #D8E3DC; margin: 4px 0; }
    .ticket-divider { border-color: rgba(255,255,255,0.18); margin: 14px 0; }
    .ticket-mensaje {
        background: rgba(255,255,255,0.10);
        padding: 12px;
        border-radius: 8px;
        margin-top: 14px;
        border-left: 3px solid #FFD966;
    }

    .badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .badge-espera     { background: #FBF3D9; color: #8A6A00; border: 1px solid #E5D7A0; }
    .badge-ingresar   { background: #E6F0EB; color: #12402A; border: 1px solid #B8D4C5; }
    .badge-salir      { background: #FCE9E9; color: #9B1C1C; border: 1px solid #E8BFBF; }
    .badge-zf         { background: #E0E7FF; color: #233876; border: 1px solid #B4C0E8; }
    .badge-finalizado { background: #EDEDED; color: #4B5563; border: 1px solid #D5D5D5; }

    .col-header-ing {
        background: var(--zfc-green-main);
        color: #FFFFFF;
        padding: 14px 16px;
        border-radius: 8px 8px 0 0;
        text-align: center;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .col-header-sal {
        background: var(--zfc-danger);
        color: #FFFFFF;
        padding: 14px 16px;
        border-radius: 8px 8px 0 0;
        text-align: center;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .empty-state {
        background: #EFEFEF;
        padding: 22px;
        text-align: center;
        color: #6B7280;
        border-radius: 0 0 8px 8px;
        font-style: italic;
        font-size: 14px;
    }

    .card-ingreso {
        background: #FFFFFF;
        border: 1px solid #B8D4C5;
        border-left: 4px solid var(--zfc-green-main);
        padding: 16px;
        border-radius: 0 0 8px 8px;
        margin-bottom: 10px;
        text-align: center;
    }
    .card-salida {
        background: #FFFFFF;
        border: 1px solid #E8BFBF;
        border-left: 4px solid var(--zfc-danger);
        padding: 16px;
        border-radius: 0 0 8px 8px;
        margin-bottom: 10px;
        text-align: center;
    }
    .card-placa {
        font-size: 30px;
        font-weight: 900;
        letter-spacing: 3px;
        font-family: 'Courier New', monospace;
        color: var(--zfc-green-dark);
        margin: 4px 0;
    }
    .card-placa-sal {
        font-size: 30px;
        font-weight: 900;
        letter-spacing: 3px;
        font-family: 'Courier New', monospace;
        color: var(--zfc-danger);
        margin: 4px 0;
    }
    .card-ficho {
        font-size: 12px;
        font-weight: 700;
        color: var(--zfc-text-soft);
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .card-detalle { font-size: 13px; color: #333; margin-top: 4px; }
    .card-aviso {
        display: inline-block;
        font-size: 12px;
        background: #F5F7F6;
        padding: 4px 10px;
        border-radius: 4px;
        margin-top: 6px;
        color: #2C3E50;
        font-weight: 600;
    }

    .role-card {
        background: #FFFFFF;
        border: 1px solid var(--zfc-border);
        border-top: 4px solid var(--zfc-green-main);
        border-radius: 10px;
        padding: 28px 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        height: 100%;
    }
    .role-titulo {
        font-size: 18px;
        font-weight: 700;
        color: var(--zfc-green-dark);
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .role-desc { font-size: 13px; color: var(--zfc-text-soft); line-height: 1.5; }

    .inst-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid var(--zfc-green-main);
        padding-bottom: 12px;
        margin-bottom: 20px;
    }
    .inst-title {
        color: var(--zfc-green-dark);
        font-size: 22px;
        font-weight: 700;
        margin: 0;
    }
    .inst-sub {
        color: var(--zfc-text-soft);
        font-size: 12px;
        margin-top: 2px;
        letter-spacing: 0.5px;
    }

    div[data-testid="stMetricValue"] { color: var(--zfc-green-dark) !important; font-weight: 700; }
    div[data-testid="stMetricLabel"] { color: #556B2F !important; font-weight: 600; }
    div[data-testid="stAlert"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ==========================================================================
# CAPA DE DATOS
# ==========================================================================
DATA_FILE = "turnos_zfc.json"
CONFIG_FILE = "config_zfc.json"

DEFAULT_CONFIG = {
    "tiempo_en_pantalla_min": 30,
    "usuario_admin": "Zona Franca Santander",
    "contrasena_admin": "ZONAFRANCA123",
    "usuario_vigilante": "Vigilante",
    "contrasena_vigilante": "VIGILANTE2026",
    "url_base": "",
    "bodegas": [
        "Bodega Principal / Generica",
        "Alfranca Cucuta S.A.S.",
        "Inversiones Cargamax HYJ S.A.S.",
        "Logistica Aduanera J.H. Ltda.",
        "Setracomex S.A.S.",
        "Otra Bodega / Operador",
    ],
}

def _migrar_campos(item):
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
        "telefono": "",
    }
    for k, v in defaults.items():
        item.setdefault(k, v)

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

def fecha_legible(s):
    if not s:
        return "—"
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return s

def parse_fecha(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def debe_ocultar_por_tiempo(turno, cfg):
    if not turno.get("mostrar_en_pantalla"):
        return True
    fa = parse_fecha(turno.get("fecha_autorizacion"))
    if fa is None:
        return False
    limite = timedelta(minutes=cfg.get("tiempo_en_pantalla_min", 30))
    return (datetime.now() - fa) > limite

def badge_html(estado_raw):
    e = (estado_raw or "").upper()
    if "INGRESAR" in e and "ZONA" not in e and "FINALIZADO" not in e:
        return '<span class="badge badge-ingresar">Autorizado para Ingresar</span>'
    if "SALIR" in e and "ZONA" not in e and "FINALIZADO" not in e:
        return '<span class="badge badge-salir">Autorizado para Salir</span>'
    if "ZONA FRANCA" in e:
        return '<span class="badge badge-zf">En Zona Franca</span>'
    if "FINALIZADO" in e:
        return '<span class="badge badge-finalizado">Finalizado</span>'
    return '<span class="badge badge-espera">En Espera</span>'

def buscar_turno(turnos, id_turno):
    return next((t for t in turnos if t.get("id_turno") == id_turno), None)

def generar_qr_png(url: str):
    if not HAS_QR or not url:
        return None
    try:
        qr = qrcode.QRCode(version=None, box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#12402A", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None

def render_header_institucional():
    c1, c2, c3 = st.columns([1.5, 3, 1.5])
    with c1:
        for fn in ["LOGO ZFS-ZFC.jpeg", "LOGO ZFS-ZFC.jpg", "LOGO ZFS-ZFC.png"]:
            if os.path.exists(fn):
                st.image(fn, use_container_width=True)
                break
    with c2:
        st.markdown("""
        <div style="text-align:center;">
            <div class="inst-title">Sistema de Enturnamiento y Control de Accesos</div>
            <div class="inst-sub">ZONA FRANCA DE CÚCUTA · OPERADA POR ZONA FRANCA SANTANDER</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        for fn in ["LOGO SANTANDER.jpg", "LOGO SANTANDER.png", "logo.jpeg"]:
            if os.path.exists(fn):
                st.image(fn, use_container_width=True)
                break

# ==========================================================================
# SESSION STATE
# ==========================================================================
if "auth_operador" not in st.session_state:
    st.session_state.auth_operador = False
if "auth_vigilante" not in st.session_state:
    st.session_state.auth_vigilante = False
if "mi_turno_id" not in st.session_state:
    st.session_state.mi_turno_id = None

try:
    qp = st.query_params
    modo_qp = (qp.get("modo") or "").strip().lower()
    if st.session_state.mi_turno_id is None and "t" in qp:
        st.session_state.mi_turno_id = qp.get("t")
except Exception:
    qp = {}
    modo_qp = ""

CONFIG = cargar_config()

# ==========================================================================
# MODO: PANTALLA TV
# ==========================================================================
if modo_qp == "pantalla":
    @st.fragment(run_every=4)
    def pantalla_publica():
        turnos = cargar_datos()
        cfg = cargar_config()

        def visible(t):
            if not t.get("mostrar_en_pantalla"):
                return False
            if debe_ocultar_por_tiempo(t, cfg):
                return False
            est = (t.get("estado") or "").upper()
            return ("INGRESAR" in est or "SALIR" in est) and "ZONA" not in est

        autorizados = [t for t in turnos if visible(t)]
        ingresos = [t for t in autorizados if "INGRESAR" in (t.get("estado") or "").upper()]
        salidas = [t for t in autorizados if "SALIR" in (t.get("estado") or "").upper()]

        c1, c2, c3 = st.columns([1, 3, 1])
        with c1:
            for fn in ["LOGO ZFS-ZFC.jpeg", "LOGO ZFS-ZFC.png"]:
                if os.path.exists(fn):
                    st.image(fn, use_container_width=True)
                    break
        with c2:
            st.markdown("""
            <div style="text-align:center; padding: 8px 0;">
                <div style="color:#12402A; font-size:32px; font-weight:900;">
                    CONTROL DE ACCESOS EN TIEMPO REAL
                </div>
                <div style="color:#6B7280; font-size:14px; letter-spacing:3px; margin-top:6px;">
                    ZONA FRANCA DE CÚCUTA · ZONA FRANCA SANTANDER
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            for fn in ["LOGO SANTANDER.jpg", "LOGO SANTANDER.png"]:
                if os.path.exists(fn):
                    st.image(fn, use_container_width=True)
                    break

        st.markdown("<br>", unsafe_allow_html=True)
        col_i, col_s = st.columns(2)

        with col_i:
            st.markdown('<div class="col-header-ing">AUTORIZADOS PARA INGRESAR</div>', unsafe_allow_html=True)
            if not ingresos:
                st.markdown('<div class="empty-state">No hay vehículos autorizados para ingresar.</div>', unsafe_allow_html=True)
            else:
                for t in ingresos:
                    st.markdown(f"""
                    <div class="card-ingreso">
                        <div class="card-ficho">Ficho {t['id_turno']}</div>
                        <div class="card-placa">{t['placa']}</div>
                        <div class="card-detalle"><b>Destino:</b> {t['bodega']}</div>
                        <div class="card-aviso">{t.get('mensaje_admin','') or 'Sin mensaje'}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_s:
            st.markdown('<div class="col-header-sal">AUTORIZADOS PARA SALIR</div>', unsafe_allow_html=True)
            if not salidas:
                st.markdown('<div class="empty-state">No hay vehículos autorizados para salir.</div>', unsafe_allow_html=True)
            else:
                for t in salidas:
                    st.markdown(f"""
                    <div class="card-salida">
                        <div class="card-ficho">Ficho {t['id_turno']}</div>
                        <div class="card-placa-sal">{t['placa']}</div>
                        <div class="card-detalle"><b>Destino:</b> {t['bodega']}</div>
                        <div class="card-aviso">{t.get('mensaje_admin','') or 'Sin mensaje'}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            f"<div style='text-align:center; color:#6B7280; font-size:12px;'>"
            f"Última actualización: {ahora_str()}</div>",
            unsafe_allow_html=True,
        )

    pantalla_publica()
    st.stop()

# ==========================================================================
# MODO: CONDUCTOR
# ==========================================================================
if modo_qp == "conductor":
    render_header_institucional()
    st.markdown("<h3 style='text-align:center;'>Portal del Conductor</h3>", unsafe_allow_html=True)

    left, center, right = st.columns([1, 2, 1])
    with center:
        turnos = cargar_datos()

        mi_turno = None
        if st.session_state.mi_turno_id:
            mi_turno = buscar_turno(turnos, st.session_state.mi_turno_id)

        if mi_turno and "FINALIZADO" not in (mi_turno.get("estado") or "").upper():

            @st.fragment(run_every=5)
            def tiquet_vivo():
                tv = cargar_datos()
                actual = buscar_turno(tv, st.session_state.mi_turno_id)
                if not actual:
                    st.warning("Tu turno ya no está disponible.")
                    return
                msg = actual.get("mensaje_admin") or "En espera de autorización"

                st.markdown(f"""
                <div class="ticket-card">
                    <div class="ticket-label">Turno Asignado</div>
                    <hr class="ticket-divider">
                    <div class="ticket-label">Placa del Vehículo</div>
                    <div class="ticket-placa">{actual['placa']}</div>
                    <div class="ticket-label" style="margin-top:18px;">Número de Ficho</div>
                    <div class="ticket-turno">{actual['id_turno']}</div>
                    <hr class="ticket-divider">
                    <div class="ticket-info"><b>Destino:</b> {actual.get('bodega','—')}</div>
                    <div class="ticket-info"><b>Movimiento:</b> {actual.get('tipo_movimiento','Ingresar')}</div>
                    <div class="ticket-info" style="font-size:12px; color:#A9BCB2; margin-top:6px;">
                        Registrado: {fecha_legible(actual.get('fecha_hora',''))}
                    </div>
                    <div style="margin-top:16px;">{badge_html(actual.get('estado',''))}</div>
                    <div class="ticket-mensaje">
                        <div class="ticket-label" style="font-size:10px;">Mensaje del Operador</div>
                        <div style="color:#FFD966; font-weight:700; font-size:15px; margin-top:4px;">{msg}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if actual.get("fecha_ingreso_zf"):
                    st.markdown(
                        f"<div style='text-align:center; color:#1B4D3E; font-weight:600; "
                        f"padding:10px; background:#E6F0EB; border-radius:6px; margin-top:10px;'>"
                        f"<b>Ingreso confirmado por vigilante:</b> {fecha_legible(actual['fecha_ingreso_zf'])}</div>",
                        unsafe_allow_html=True,
                    )
                if actual.get("fecha_salida_zf"):
                    st.markdown(
                        f"<div style='text-align:center; color:#9B1C1C; font-weight:600; "
                        f"padding:10px; background:#FCE9E9; border-radius:6px; margin-top:10px;'>"
                        f"<b>Salida confirmada por vigilante:</b> {fecha_legible(actual['fecha_salida_zf'])}</div>",
                        unsafe_allow_html=True,
                    )

            tiquet_vivo()

            st.markdown("<br>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Actualizar Estado", use_container_width=True):
                    st.rerun()
            with col_b:
                if st.button("Registrar otro vehículo", use_container_width=True):
                    st.session_state.mi_turno_id = None
                    try:
                        st.query_params.clear()
                        st.query_params["modo"] = "conductor"
                    except Exception:
                        pass
                    st.rerun()

        else:
            st.markdown("Completa tus datos para asignarte un turno.")
            st.caption("Todos los campos con (*) son obligatorios")

            with st.form("form_conductor", clear_on_submit=False):
                placa = st.text_input("Placa del Vehículo *", placeholder="Ej: ABC123").upper().strip()
                nombre = st.text_input("Nombre Completo del Conductor *", placeholder="Ej: Juan Pérez").title().strip()
                cedula = st.text_input("Número de Cédula *", placeholder="Ej: 1234567890").strip()
                telefono = st.text_input("Teléfono de Contacto *", placeholder="Ej: 3001234567").strip()
                bodega = st.selectbox(
                    "Bodega de Destino *",
                    ["Seleccione una bodega..."] + CONFIG.get("bodegas", []),
                )
                submitted = st.form_submit_button("Obtener Turno", use_container_width=True)

                if submitted:
                    errores = []
                    if not placa:
                        errores.append("La placa del vehículo es obligatoria.")
                    if not nombre:
                        errores.append("El nombre del conductor es obligatorio.")
                    if not cedula:
                        errores.append("El número de cédula es obligatorio.")
                    if not telefono:
                        errores.append("El teléfono de contacto es obligatorio.")
                    if bodega == "Seleccione una bodega...":
                        errores.append("Debes seleccionar una bodega de destino.")
                    if cedula and not cedula.isdigit():
                        errores.append("La cédula debe contener solo números.")
                    if telefono and not telefono.isdigit():
                        errores.append("El teléfono debe contener solo números.")
                    if telefono and len(telefono) < 7:
                        errores.append("El teléfono debe tener al menos 7 dígitos.")
                    if placa and len(placa) < 5:
                        errores.append("La placa debe tener al menos 5 caracteres.")

                    if errores:
                        st.error("⚠️ Corrige los siguientes errores:\n\n" + "\n".join(f"• {e}" for e in errores))
                    else:
                        actuales = cargar_datos()
                        activo = next(
                            (t for t in actuales
                             if t["placa"] == placa and "FINALIZADO" not in (t.get("estado") or "").upper()),
                            None,
                        )
                        if activo:
                            st.warning(f"La placa {placa} ya tiene turno activo: {activo['id_turno']}")
                            st.session_state.mi_turno_id = activo["id_turno"]
                            try:
                                st.query_params["t"] = activo["id_turno"]
                            except Exception:
                                pass
                            st.rerun()
                        else:
                            nuevo_id = len(actuales) + 1
                            turno_str = f"T-{nuevo_id:03d}"
                            nuevo = {
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
                            actuales.append(nuevo)
                            guardar_datos(actuales)
                            st.session_state.mi_turno_id = turno_str
                            try:
                                st.query_params["t"] = turno_str
                            except Exception:
                                pass
                            st.rerun()

        st.markdown("---")
        with st.expander("Recuperar mi turno por placa"):
            p_buscar = st.text_input("Ingresa tu placa", key="rec_placa").upper().strip()
            if st.button("Buscar", key="btn_rec"):
                if not p_buscar:
                    st.error("Ingresa una placa.")
                else:
                    tb = cargar_datos()
                    encontrado = next(
                        (t for
