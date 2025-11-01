import streamlit as st
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="MyBarrioYa 🛒", layout="wide")

# ---------------- ESTILO ----------------
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

# ---------------- ARCHIVOS ----------------
USER_FILE = "usuarios.json"
TIENDAS_FILE = "tiendas.json"
PEDIDOS_FILE = "pedidos.json"
NOTIFS_FILE = "notificaciones.json"

# ---------------- FUNCIONES JSON ----------------
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

# ---------------- ASEGURAR ARCHIVOS ----------------
for fname, default in [
    (USER_FILE, {}),
    (TIENDAS_FILE, []),
    (PEDIDOS_FILE, []),
    (NOTIFS_FILE, [])
]:
    if not os.path.exists(fname):
        save_json(fname, default)

# ---------------- ADMIN ----------------
def ensure_admin():
    users = load_json(USER_FILE, {})
    if "briamCeo" not in users:
        users["briamCeo"] = {"password": "12345", "rol": "admin"}
        save_json(USER_FILE, users)
ensure_admin()

# ---------------- NOTIFICACIONES ----------------
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

# ---------------- USUARIOS ----------------
def register_user(username, password, rol):
    users = load_json(USER_FILE, {})
    if not username or not password or username in users:
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

# ---------------- PEDIDOS ----------------
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

    add_notification("admin", "nuevo_pedido", f"Pedido de {usuario} a {tienda}")
    add_notification(tienda, "nuevo_pedido", f"Nuevo pedido de {usuario}: {producto} x{cantidad}")
    return True

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

# ---------------- UI ----------------
st.markdown("<h1 class='main-title'>MyBarrioYa 🛒</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Tu tienda del barrio ahora en tu celular</p>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    opcion = st.radio("Selecciona una opción:", ["Iniciar sesión", "Registrarse"])

    if opcion == "Iniciar sesión":
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            rol = login_user(username, password)
            if rol:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.rol = rol
                st.success(f"Bienvenido {username} 👋")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    elif opcion == "Registrarse":
        username = st.text_input("Nuevo usuario")
        password = st.text_input("Contraseña", type="password")
        rol = st.selectbox("Rol", ["cliente", "tendero"])
        if st.button("Crear cuenta"):
            if register_user(username, password, rol):
                st.success("✅ Usuario creado con éxito. Ya puedes iniciar sesión.")
            else:
                st.error("❌ Error: usuario ya existe o datos inválidos.")

else:
    notif_count = get_unread_count_for("admin" if st.session_state.rol == "admin" else st.session_state.username)
    badge = f"<span class='badge'>{notif_count}</span>" if notif_count > 0 else ""
    st.sidebar.markdown(f"### 👤 {st.session_state.username} ({st.session_state.rol}) {badge}", unsafe_allow_html=True)

    if st.sidebar.button("🔔 Ver notificaciones"):
        mark_all_read_for("admin" if st.session_state.rol == "admin" else st.session_state.username)
        for n in list_notifications_for("admin" if st.session_state.rol == "admin" else st.session_state.username):
            st.markdown(f"<div class='notif'>🔔 {n['mensaje']}<br><span class='small'>{n['fecha']}</span></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.rol = ""
        st.rerun()

    # -------- PANELES --------
    if st.session_state.rol == "admin":
        st.subheader("📊 Panel de administrador")
        users = load_json(USER_FILE, {})
        st.write("**Usuarios registrados:**")
        st.table([{"Usuario": u, "Rol": data["rol"]} for u, data in users.items()])

    elif st.session_state.rol == "tendero":
        st.subheader("🛍 Panel del Tendero")
        st.info("Aquí aparecerán los pedidos de tus clientes próximamente.")

    elif st.session_state.rol == "cliente":
        st.subheader("🛒 Realizar pedido")
        tienda = st.text_input("Nombre de la tienda")
        producto = st.text_input("Producto")
        cantidad = st.number_input("Cantidad", 1, 100, 1)
        direccion = st.text_input("Dirección de entrega")
        if st.button("Enviar pedido"):
            if create_order(st.session_state.username, tienda, producto, cantidad, direccion):
                st.success("✅ Pedido enviado con éxito.")






