# streamlit_app.py
import streamlit as st
import json
import os
from datetime import datetime

# ---------------- Page config ----------------
st.set_page_config(page_title="MyBarrioYa", page_icon="🛒", layout="wide")

# ---------------- Styles ----------------
st.markdown("""
    <style>
        body { background-color: #121212; color: #ddd; }
        .main-title { text-align: center; font-size: 40px; color: #4CAF50; font-weight: bold; margin-bottom: 4px; }
        .sub-title { text-align: center; font-size: 16px; color: #a1a1a1; margin-bottom: 18px; }
        .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; height: 2.6em; font-size:16px; }
        .stButton>button:hover { background-color: #66bb6a; }
        .badge { background:#ff3b3b; color:white; padding:2px 8px; border-radius:12px; font-weight:bold; }
        .notif { background:#1f1f1f; padding:10px; border-radius:8px; margin-bottom:8px; }
        .small { font-size:12px; color:#bbb; }
    </style>
""", unsafe_allow_html=True)

# ---------------- Files ----------------
USER_FILE = "usuarios.json"
TIENDAS_FILE = "tiendas.json"
PEDIDOS_FILE = "pedidos.json"
NOTIFS_FILE = "notificaciones.json"

# ---------------- Helpers: load/save JSON ----------------
def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- Ensure files exist ----------------
for fname, default in [
    (USER_FILE, {}),
    (TIENDAS_FILE, []),
    (PEDIDOS_FILE, []),
    (NOTIFS_FILE, [])
]:
    if not os.path.exists(fname):
        save_json(fname, default)

# ---------------- Ensure single admin ----------------
def ensure_admin():
    users = load_json(USER_FILE, {})
    if "briamCeo" not in users:
        users["briamCeo"] = {"password": "12345", "rol": "admin"}
        save_json(USER_FILE, users)
ensure_admin()

# ---------------- Notification helpers ----------------
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
    count = 0
    for n in notifs:
        if not n.get("leido", False):
            if user == "admin" and n.get("para") == "admin":
                count += 1
            elif n.get("para") == user:
                count += 1
    return count

def list_notifications_for(user):
    notifs = load_json(NOTIFS_FILE, [])
    filtered = []
    for n in notifs:
        if user == "admin" and n.get("para") == "admin":
            filtered.append(n)
        elif n.get("para") == user:
            filtered.append(n)
    return sorted(filtered, key=lambda x: x.get("fecha",""), reverse=True)

def mark_all_read_for(user):
    notifs = load_json(NOTIFS_FILE, [])
    changed = False
    for n in notifs:
        if user == "admin" and n.get("para") == "admin" and not n.get("leido", False):
            n["leido"] = True
            changed = True
        elif n.get("para") == user and not n.get("leido", False):
            n["leido"] = True
            changed = True
    if changed:
        save_json(NOTIFS_FILE, notifs)

# ---------------- User functions ----------------
def register_user(username, password, rol):
    users = load_json(USER_FILE, {})
    if not username or not password or username in users:
        return False
    users[username] = {"password": password, "rol": rol}
    save_json(USER_FILE, users)
    add_notification("admin", "nuevo_usuario", f"Nuevo usuario: {username} ({rol})", {"usuario": username, "rol": rol})
    return True

def login_user(username, password):
    users = load_json(USER_FILE, {})
    if username in users and users[username].get("password") == password:
        return users[username].get("rol")
    return None

# ---------------- Pedido functions ----------------
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
    add_notification("admin", "nuevo_pedido", f"Pedido de {usuario} a {tienda}: {producto} x{cantidad}", {"usuario": usuario, "tienda": tienda})
    tiendas = load_json(TIENDAS_FILE, [])
    tienda_obj = next((t for t in tiendas if t.get("nombre") == tienda), None)
    if tienda_obj:
        dueno = tienda_obj.get("dueno")
        if dueno:
            add_notification(dueno, "nuevo_pedido", f"NUEVO pedido: {producto} x{cantidad} de {usuario}", {"usuario": usuario, "tienda": tienda})
    return pedido

def update_order_status(pedido_index, new_status):
    pedidos = load_json(PEDIDOS_FILE, [])
    if 0 <= pedido_index < len(pedidos):
        pedidos[pedido_index]["estado"] = new_status
        save_json(PEDIDOS_FILE, pedidos)
        return pedidos[pedido_index]
    return None

# ---------------- Session defaults ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

# ---------------- Sidebar ----------------
if st.session_state.logged_in:
    notif_count = get_unread_count_for(
        "admin" if st.session_state.rol == "admin" else st.session_state.username
    )
    badge = f"<span class='badge'>{notif_count}</span>" if notif_count > 0 else ""

    st.sidebar.markdown(
        f"### 👤 {st.session_state.username} ({st.session_state.rol}) {badge}",
        unsafe_allow_html=True
    )

    if st.sidebar.button("🔔 Ver notificaciones"):
        mark_all_read_for("admin" if st.session_state.rol == "admin" else st.session_state.username)
        st.session_state.show_notifs = True

    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.rol = ""

# Aquí seguiría tu lógica principal (login, registro, menús, etc.)





