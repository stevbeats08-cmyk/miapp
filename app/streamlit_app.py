# streamlit_app.py
import streamlit as st
import json
import os
from datetime import datetime

# ---------------- CONFIGURACIÓN DE PÁGINA ----------------
st.set_page_config(page_title="MyBarrioYa", page_icon="🛒", layout="wide")

# ---------------- ESTILOS ----------------
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

# ---------------- ARCHIVOS ----------------
USER_FILE = "usuarios.json"
TIENDAS_FILE = "tiendas.json"
PEDIDOS_FILE = "pedidos.json"
NOTIFS_FILE = "notificaciones.json"

# ---------------- FUNCIONES AUXILIARES ----------------
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

# ---------------- ARCHIVOS BASE ----------------
for fname, default in [
    (USER_FILE, {}),
    (TIENDAS_FILE, []),
    (PEDIDOS_FILE, []),
    (NOTIFS_FILE, [])
]:
    if not os.path.exists(fname):
        save_json(fname, default)

# ---------------- ADMIN UNICO ----------------
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
    if rol == "admin":
        return False  # no permitir nuevos admin
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
    add_notification("admin", "nuevo_pedido", f"Pedido de {usuario}: {producto} x{cantidad}")
    add_notification(tienda, "nuevo_pedido", f"Tienes un nuevo pedido de {usuario}: {producto} x{cantidad}")
    return pedido

def update_order_status(pedido_index, new_status):
    pedidos = load_json(PEDIDOS_FILE, [])
    if 0 <= pedido_index < len(pedidos):
        pedido = pedidos[pedido_index]
        pedido["estado"] = new_status
        save_json(PEDIDOS_FILE, pedidos)
        add_notification(pedido["usuario"], "pedido_enviado", f"Tu pedido de {pedido['producto']} ha sido enviado ✅")
        return pedido
    return None

# ---------------- SESIÓN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:
    st.image("logo.png", width=180)
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
            st.rerun()
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
    unread = get_unread_count_for("admin" if rol == "admin" else username)
    badge = f"<span class='badge'>{unread}</span>" if unread > 0 else ""

    # LOGO EN EL SIDEBAR
    st.sidebar.image("logo.png", width=120)
    st.sidebar.markdown(f"👤 **{username}** ({rol}) {badge}", unsafe_allow_html=True)
    st.sidebar.divider()

    if rol == "admin":
        menu = st.sidebar.radio("Menú", ["Inicio", "Usuarios", "Notificaciones"])
    elif rol == "tendero":
        menu = st.sidebar.radio("Menú", ["Inicio", "Ver pedidos", "Notificaciones"])
    else:
        menu = st.sidebar.radio("Menú", ["Inicio", "Hacer pedido", "Notificaciones"])

    st.sidebar.divider()
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.rol = ""
        st.rerun()

    # ---------------- PANEL ADMIN ----------------
    if rol == "admin":
        st.image("logo.png", width=160)
        if menu == "Inicio":
            st.title("Panel de administrador")
            st.write("👋 Bienvenido, Briam. Aquí puedes supervisar toda la actividad.")
        elif menu == "Usuarios":
            st.subheader("Usuarios registrados")
            users = load_json(USER_FILE, {})
            st.table([{"Usuario": u, "Rol": info["rol"]} for u, info in users.items()])
        elif menu == "Notificaciones":
            st.subheader("Notificaciones 🔔")
            notifs = list_notifications_for("admin")
            for n in notifs:
                st.markdown(f"<div class='notif'><b>{n['mensaje']}</b><div class='small'>{n['fecha']}</div></div>", unsafe_allow_html=True)
            mark_all_read_for("admin")

    # ---------------- PANEL TENDERO ----------------
    elif rol == "tendero":
        st.image("logo.png", width=160)
        if menu == "Inicio":
            st.title(f"Bienvenido My Barrio YApp {username} 👋")
            st.write("Aquí puedes gestionar los pedidos de tus clientes.")
        elif menu == "Ver pedidos":
            st.subheader("Pedidos recibidos")
            pedidos = load_json(PEDIDOS_FILE, [])
            for i, p in enumerate(pedidos):
                if p["tienda"] == username:
                    st.markdown(f"**{p['usuario']}** pidió **{p['producto']} x{p['cantidad']}**")
                    if p["estado"] == "pendiente":
                        if st.button(f"Marcar como enviado #{i}"):
                            update_order_status(i, "enviado")
                            st.success("Pedido marcado como enviado ✅")
                            st.rerun()
        elif menu == "Notificaciones":
            st.subheader("Notificaciones 🔔")
            notifs = list_notifications_for(username)
            for n in notifs:
                st.markdown(f"<div class='notif'><b>{n['mensaje']}</b><div class='small'>{n['fecha']}</div></div>", unsafe_allow_html=True)
            mark_all_read_for(username)

    # ---------------- PANEL CLIENTE ----------------
    else:
        st.image("logo.png", width=160)
        if menu == "Inicio":
            st.title(f"Bienvenido a My Barrio YApp {username} 👋")
            st.write("Haz tus pedidos fácilmente desde aquí.")
        elif menu == "Hacer pedido":
            st.subheader("Nuevo pedido 🛍️")
            tiendas = load_json(TIENDAS_FILE, [])
            if tiendas:
                tienda = st.selectbox("Selecciona tienda", [t.get("nombre") for t in tiendas])
            else:
                tienda = st.text_input("Nombre de la tienda (temporal)")
            producto = st.text_input("Producto")
            cantidad = st.number_input("Cantidad", 1, 50, 1)
            direccion = st.text_area("Dirección de entrega")
            if st.button("Enviar pedido"):
                create_order(username, tienda, producto, cantidad, direccion)
                st.success("Pedido enviado correctamente ✅")
        elif menu == "Notificaciones":
            st.subheader("Notificaciones 🔔")
            notifs = list_notifications_for(username)
            for n in notifs:
                st.markdown(f"<div class='notif'><b>{n['mensaje']}</b><div class='small'>{n['fecha']}</div></div>", unsafe_allow_html=True)
            mark_all_read_for(username)







