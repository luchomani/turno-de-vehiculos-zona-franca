# --- CONEXIÓN A BASE DE DATOS (NEON BLINDADO) ---
# La URL ahora incluye timeout y keepalives
DATABASE_URL = st.secrets.get("DATABASE_URL", "postgresql://neondb_owner:npg_heCBkPc0r5Qx@ep-weathered-art-b74v5gzj-pooler.c-13.us-east-1.aws.neon.tech/neondb?sslmode=require&keepalives=1&keepalives_idle=30&connect_timeout=30")

def obtener_conexion_segura(max_intentos=3):
    """Intenta conectar hasta 3 veces si la base de datos está dormida."""
    for intento in range(max_intentos):
        try:
            # Intentamos conectar con un timeout de 30 segundos
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.OperationalError as e:
            if intento == max_intentos - 1:
                st.error(f"Error crítico de conexión después de {max_intentos} intentos: {e}")
                return None
            # Espera 3 segundos antes de reintentar
            time.sleep(3)
    return None

@st.cache_data(ttl=30)
def cargar_datos():
    if DATABASE_URL:
        conn = obtener_conexion_segura()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM turnos ORDER BY fecha_hora DESC LIMIT 300") 
            datos = cursor.fetchall()
            
            if not datos: return []
                
            for item in datos:
                item["mostrar_en_pantalla"] = bool(item.get("mostrar_en_pantalla", False))
                for k, v in item.items():
                    if v is None:
                        item[k] = ""
                _migrar_campos(item)
                
            return datos
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return []
        finally:
            # SIEMPRE cerramos la conexión al terminar
            cursor.close()
            conn.close()
    else:
        # Fallback local
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    for item in datos: _migrar_campos(item)
                    return datos
            except Exception: return []
        return []

def guardar_datos(datos):
    if DATABASE_URL:
        conn = obtener_conexion_segura()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE turnos")
            
            if datos:
                values = [(
                    t.get("uid"), t.get("id_turno"), t.get("placa"), t.get("nombre"), 
                    t.get("cedula"), t.get("telefono"), t.get("bodega"), t.get("tipo_movimiento"), 
                    t.get("estado"), t.get("fecha_hora"), t.get("mensaje_admin"), 
                    bool(t.get("mostrar_en_pantalla", False)), t.get("fecha_autorizacion"), 
                    t.get("fecha_ingreso_zf"), t.get("fecha_salida_zf"), t.get("observaciones_conductor")
                ) for t in datos]
                
                execute_values(cursor, """
                    INSERT INTO turnos (
                        uid, id_turno, placa, nombre, cedula, telefono, bodega, 
                        tipo_movimiento, estado, fecha_hora, mensaje_admin, 
                        mostrar_en_pantalla, fecha_autorizacion, fecha_ingreso_zf, 
                        fecha_salida_zf, observaciones_conductor
                    ) VALUES %s
                """, values)
                
            conn.commit()
            cargar_datos.clear() 
            gc.collect()
            return True
        except Exception as e:
            st.error(f"Error al guardar en la base de datos: {e}")
            return False
        finally:
            # SIEMPRE cerramos la conexión al terminar
            cursor.close()
            conn.close()
    else:
        # Fallback local
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        cargar_datos.clear()
        gc.collect()
        return True
