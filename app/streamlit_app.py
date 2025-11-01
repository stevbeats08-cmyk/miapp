# streamlit_app.py (versión robusta con debugging)
import streamlit as st
import json
import os
from datetime import datetime
import traceback

# ---------------- Compatibilidad rerun ----------------
def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

# ---------------- Paths seguros (relativos al archivo) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # carpeta 'app'
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
LOGO_FILENAME = "logo1.png"
LOGO_PATH = os.path.join(STATIC_DIR, LOGO_FILENAME)

# ---------------- Archivos de datos ----------------
USER_FILE = os.path.join(BASE_DIR, "usuarios.json")
TIENDAS_FILE = os.path.join(BASE_DIR, "tiendas.json")
PEDIDOS_FILE = os.path.join(BASE_DIR, "pedidos.json")
NOTIFS_FILE = os.path.join(BASE_DIR, "notificaciones.json")

# ---------------- Helpers JSON con manejo de errores ----------------
def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # archivo corrupto: mostrar aviso y devolver default para no romper la app
        st.sidebar.error(f"⚠️ JSON corrupto: {os.path.basename(filename)} (se usará valor por defecto).")
        return default
    except Exception as e:
        st.sidebar.error(f"⚠️ Error leyendo {os.path.basename(filename)}: {e}")
        return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.sidebar.error(f"⚠️ Error guardando {os.path.basename(filename)}: {e}")

# ---------------- Asegurar existencia de archivos y carpeta static ----------------
os.makedirs(STATIC_DIR, exist_ok=True)
for fname, default in [
    (USER_FILE, {}),
    (TIENDAS_FILE, []),
    (PEDIDOS_FILE, []),
    (NOTIFS_FILE, [])
]:
    if not os.path.exists(fname):
        try:
            save_json(fname, default)
        except Exception:
            pass  # save_json muestra error en sidebar si falla

# ---------------- Funciones principales (sin cambios lógicos) ----------------
def ensure_admin():
    users = load_json(USER_FILE, {})
    if "briamCeo" not in users:
        users["briamCeo"] = {"password": "12345", "rol": "admin"}
        save_json(USER_FILE, users)
ensure_admin()

def add_notification(para, tipo, mensaje, meta=None):
    notifs = load_json(NOTIFS_FILE, [])
    entry = {
        "para": para,
        "tipo": tipo,
        "mensaje": mensaje,
        "meta": meta or {},
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leido": False
    }
    notifs.append(entry)
    save_json(NOTIFS_FILE, notifs)

def get_unread_count_for(user):
    notifs = load_json(NOTIFS_FILE, [])
    return sum(1 for n in notifs if not n.get("leido", False) and n.get("para") == user)

def list_notifications_for(user):
    notifs = load_json(NOTIFS_FILE, [])
    return sorted([n for n in notifs if n.get("para") == user], key=lambda x: x.get("fecha",""), reverse=True)

def mark_all_read_for(user):
    notifs = load_json(NOTIFS_FILE, [])
    changed = False
    for n in notifs:
        if n.get("para") == user and not n.get("leido", False):
            n["leido"] = True
            changed = True
    if changed:
        save_json(NOTIFS_FILE, notifs)

def register_user(username, password, rol):
    users = load_json(USER_FILE, {})
    if not username or not password or username in users:
        return False
    if rol == "admin":
        return False
    users[username] = {"password": password, "rol": rol}
    save_json(USER_FILE, users)
    add_notification("admin", "nuevo_usuario", f"Nuevo usuario registrado: {username} ({rol})")
    return True

def login_user(username, password):
    users = load_json(USER_FILE, {})
    if username in users and users[username].get("password") == password:
        return users[username].get("rol")
    return None

def create_order(usuario, tienda, producto, cantidad, direccion):
    pedidos = load_json(PEDIDOS_FILE, [])
    pedido = {
        "usuario": usuario,
        "tienda": tienda,
        "producto": producto,
        "cantidad": cantidad,
        "direccion": direccion,
        "estado": "pendiente",
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    pedidos.append(pedido)
    save_json(PEDIDOS_FILE, pedidos)
    add_notification("admin", "nuevo_pedido", f"Pedido de {usuario}: {producto} x{cantidad}")
    add_notification(tienda, "nuevo_pedido", f"Tienes un nuevo pedido de {usuario}: {producto} x{cantidad}")
    return pedido

def update_order_status(pedido_index, new_status):
    pedidos = load_json(PEDIDOS_FILE, [])
    if 0 <= pedido_index < len(pedidos):
        pedido = pedidos[pedido_index]
        pedido["estado"] = new_status
        save_json(PEDIDOS_FILE, pedidos)
        add_notification(pedido["usuario"], "pedido_enviado", f"Tu pedido de {pedido['producto']} ha sido {new_status}")
        return pedido
    return None

# ---------------- UI: robusta con captura de errores generales ----------------
try:
    st.set_page_config(page_title="MyBarrioYa", page_icon="🛒", layout="wide")

    # estilos (conserva los tuyos)
    st.markdown("""
        <style>
            body { background-color: #121212; color: #ddd; }
            .main-title { text-align: center; font-size: 38px; color: #4CAF50; font-weight: bold; margin-bottom: 4px; }
            .sub-title { text-align: center; font-size: 16px; color: #a1a1a1; margin-bottom: 18px; }
            .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; height: 2.6em; font-size:16px; }
            .stButton>button:hover { background-color: #66bb6a; }
            .badge { background:#ff3b3b; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; }
            .notif { background:#1f1f1f; padding:10px; border-radius:8px; margin-bottom:8px; }
            .small { font-size:12px; color:#bbb; }
        </style>
    """, unsafe_allow_html=True)

    # show debug panel collapsed in sidebar so you can inspect file statuses
    with st.sidebar.expander("🔧 Diagnóstico (útil si la app no carga)", expanded=False):
        st.write("Base dir:", BASE_DIR)
        st.write("STATIC_DIR:", STATIC_DIR)
        st.write("Logo path:", LOGO_PATH)
        st.write("Archivos de datos (existencia):")
        for p in [USER_FILE, TIENDAS_FILE, PEDIDOS_FILE, NOTIFS_FILE]:
            st.write(os.path.basename(p), "→", "✔️" if os.path.exists(p) else "❌")
        # Show small preview (first keys) to verify content quickly
        try:
            users_preview = load_json(USER_FILE, {})
            st.write("Usuarios (preview):", list(users_preview.keys())[:10])
        except Exception as ex:
            st.write("Usuarios preview error:", ex)

    # logo en login (si existe)
    if not os.path.exists(LOGO_PATH):
        st.sidebar.warning("⚠️ No se encontró logo en static/logo1.png (usa app/static/logo1.png en GitHub).")
    else:
        # también mostrable en sidebar principal
        st.sidebar.image(LOGO_PATH, width=120)

    # sesión
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "rol" not in st.session_state:
        st.session_state.rol = ""

    # login UI
    if not st.session_state.logged_in:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=160)
        st.markdown("<h1 class='main-title'>🛒 MyBarrioYa</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Tu app para pedidos en tu barrio</p>", unsafe_allow_html=True)

        st.subheader("Iniciar sesión")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            rol = login_user(username, password)
            if rol:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.rol = rol
                safe_rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

        st.divider()
        st.subheader("Registrarse")
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva contraseña", type="password")
        new_rol = st.selectbox("Rol", ["cliente", "tendero"])
        if st.button("Crear cuenta"):
            if register_user(new_user, new_pass, new_rol):
                st.success("Usuario registrado correctamente ✅")
            else:
                st.warning("El usuario ya existe o no es válido")

    else:
        rol = st.session_state.rol
        username = st.session_state.username
        notif_key = "admin" if rol == "admin" else username
        unread = get_unread_count_for(notif_key)
        badge = f"<span class='badge'>{unread}</span>" if unread > 0 else ""

        if os.path.exists(LOGO_PATH):
            st.sidebar.image(LOGO_PATH, width=120)
        st.sidebar.markdown(f"👤 **{username}** ({rol}) {badge}", unsafe_allow_html=True)
        st.sidebar.divider()

        # menu
        if rol == "admin":
            menu = st.sidebar.radio("Menú", ["Inicio", "Usuarios", "Notificaciones", "Estadísticas"])
        elif rol == "tendero":
            menu = st.sidebar.radio("Menú", ["Inicio", "Ver pedidos", "Notificaciones"])
        else:
            menu = st.sidebar.radio("Menú", ["Inicio", "Hacer pedido", "Mis pedidos", "Notificaciones"])

        if st.sidebar.button("Cerrar sesión"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.rol = ""
            safe_rerun()

        # Simple routing (mantén tu lógica aquí)
        if rol == "admin":
            if menu == "Inicio":
                st.subheader("Panel admin")
                users = load_json(USER_FILE, {})
                st.metric("Usuarios", len(users))
            elif menu == "Usuarios":
                st.subheader("Usuarios")
                st.write(load_json(USER_FILE, {}))
            elif menu == "Notificaciones":
                st.subheader("Notificaciones")
                for n in list_notifications_for("admin"):
                    st.write(n)
                if st.button("Marcar todas leídas"):
                    mark_all_read_for("admin")
                    safe_rerun()
            elif menu == "Estadísticas":
                st.subheader("Estadísticas")
                st.write("Pedidos:", load_json(PEDIDOS_FILE, []))

        elif rol == "tendero":
            if menu == "Inicio":
                st.subheader(f"Tendero: {username}")
            elif menu == "Ver pedidos":
                st.subheader("Pedidos recibidos")
                pedidos = load_json(PEDIDOS_FILE, [])
                mis = [ (i,p) for i,p in enumerate(pedidos) if p.get("tienda")==username ]
                if not mis:
                    st.info("No hay pedidos para tus tiendas.")
                else:
                    for idx,p in mis:
                        st.write(idx, p)
                        if p.get("estado")=="pendiente" and st.button(f"Marcar enviado {idx}", key=f"send_{idx}"):
                            update_order_status(idx, "enviado")
                            safe_rerun()
            elif menu == "Notificaciones":
                st.subheader("Notificaciones")
                for n in list_notifications_for(username):
                    st.write(n)
                if st.button("Marcar todas leídas"):
                    mark_all_read_for(username)
                    safe_rerun()

        else:  # cliente
            if menu == "Inicio":
                st.subheader(f"Bienvenido a My barrio YApp {username}")
                st.write("Resumen rápido:")
                pedidos = load_json(PEDIDOS_FILE, [])
                my = [p for p in pedidos if p.get("usuario")==username]
                st.write("Total pedidos:", len(my))
            elif menu == "Hacer pedido":
                st.subheader("Hacer pedido")
                tiendas = load_json(TIENDAS_FILE, [])
                if tiendas:
                    tienda = st.selectbox("Selecciona tienda", [t.get("nombre") for t in tiendas])
                else:
                    tienda = st.text_input("Nombre de la tienda (temporal)")
                producto = st.text_input("Producto")
                cantidad = st.number_input("Cantidad", 1, step=1)
                direccion = st.text_input("Dirección")
                if st.button("Enviar pedido"):
                    if not producto or not direccion:
                        st.error("Completa producto y dirección")
                    else:
                        create_order(username, tienda, producto, cantidad, direccion)
                        st.success("Pedido creado")
                        safe_rerun()
            elif menu == "Mis pedidos":
                st.subheader("Mis pedidos")
                pedidos = load_json(PEDIDOS_FILE, [])
                my = [p for p in pedidos if p.get("usuario")==username]
                st.write(my)
            elif menu == "Notificaciones":
                st.subheader("Notificaciones")
                for n in list_notifications_for(username):
                    st.write(n)
                if st.button("Marcar todas leídas"):
                    mark_all_read_for(username)
                    safe_rerun()

except Exception as e:
    # Si algo falla fuera del flujo normal, mostrar stacktrace en la app para depuración
    st.error("La app encontró un error inesperado. Mira el detalle abajo.")
    st.code(traceback.format_exc())
    # además imprimimos en sidebar información básica de entorno
    with st.sidebar.expander("⚠️ Info de depuración", expanded=True):
        st.write("BASE_DIR:", BASE_DIR)
        st.write("LOGO_PATH:", LOGO_PATH)
        st.write("Archivos existentes:", { os.path.basename(p): os.path.exists(p) for p in [USER_FILE, TIENDAS_FILE, PEDIDOS_FILE, NOTIFS_FILE] })








