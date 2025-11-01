# streamlit_app.py
import streamlit as st
import json
import os
from datetime import datetime
import base64

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

# ---------------- Helpers: load/save JSON with safety ----------------
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
        "para": para,            # "admin" or username of tendero or username of client
        "tipo": tipo,            # nuevo_usuario | nuevo_pedido | pedido_enviado
        "mensaje": mensaje,
        "meta": meta or {},
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leido": False
    }
    notifs.append(entry)
    save_json(NOTIFS_FILE, notifs)

def get_unread_count_for(user):
    # admin sees para == "admin" notifications (we'll also store para equal admin)
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
    # return only those for this user (admin sees para == "admin")
    filtered = []
    for n in notifs:
        if user == "admin" and n.get("para") == "admin":
            filtered.append(n)
        elif n.get("para") == user:
            filtered.append(n)
    # newest first
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
    # notify admin of new user
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
    # notify admin
    add_notification("admin", "nuevo_pedido", f"Pedido de {usuario} a {tienda}: {producto} x{cantidad}", {"usuario": usuario, "tienda": tienda})
    # notify tendero (find tendero username)
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

# ---------------- Session state defaults ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""
# to avoid repeating sounds many times
if "last_notif_count" not in st.session_state:
    st.session_state.last_notif_count = 0
if "notif_sound_played_for" not in st.session_state:
    st.session_state.notif_sound_played_for = set()

# ---------------- Simple beep sound (short base64 wav) ----------------
# small 0.05s beep wav (monophonic) encoded base64 (generated offline, embedded)
beep_wav_b64 = (
    "UklGRiQAAABXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YQAAAAAAgD8AAP//"
    "AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA"
)
# decode to bytes when needed
try:
    beep_bytes = base64.b64decode(beep_wav_b64)
except Exception:
    beep_bytes = None

# ---------------- UI: Logo and header ----------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div class='main-title'>MyBarrioYa 🛒</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Tu tienda del barrio, en la palma de tu mano.</div>", unsafe_allow_html=True)

# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 Iniciar sesión", "🆕 Registrarse"])

    with tab1:
        login_user_input = st.text_input("Usuario", key="login_user")
        login_pass_input = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("Entrar"):
            rol = login_user(login_user_input, login_pass_input)
            if rol:
                st.session_state.logged_in = True
                st.session_state.username = login_user_input
                st.session_state.rol = rol
                st.success(f"¡Bienvenido {login_user_input}! Rol: {rol}")
                st.experimental_rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with tab2:
        reg_user = st.text_input("Nuevo usuario", key="reg_user")
        reg_pass = st.text_input("Nueva contraseña", type="password", key="reg_pass")
        reg_role = st.selectbox("Selecciona tu rol", ["cliente", "tendero"], key="reg_role")  # admin removed
        if st.button("Registrar"):
            ok = register_user(reg_user, reg_pass, reg_role)
            if ok:
                st.success("Usuario creado. Inicia sesión.")
            else:
                st.warning("El usuario ya existe o datos inválidos.")
    st.stop()

# ---------------- Sidebar with badges ----------------
# compute notification count for current user
current = st.session_state.username
role = st.session_state.rol
if role == "admin":
    user_key_for_notif = "admin"
else:
    user_key_for_notif = current

unread = get_unread_count_for(user_key_for_notif)
badge = f" <span class='badge'>{unread}</span>" if unread else ""

# Sidebar menu labels with badges (only show badge on Notifications item for admin)
if role == "admin":
    side_items = [
        ("🏠 Inicio", "home"),
        (f"🔔 Notificaciones {badge}", "notifs"),
        ("👥 Usuarios", "users"),
        ("🏪 Tiendas", "stores"),
        ("📦 Pedidos", "orders"),
    ]
else:
    # tendero and cliente
    if role == "tendero":
        side_items = [
            ("🏠 Inicio", "home"),
            (f"🔔 Notificaciones {badge}", "notifs"),
            ("🏪 Mi Tienda", "store"),
            ("📦 Pedidos Recibidos", "received"),
        ]
    else:
        side_items = [
            ("🏠 Inicio", "home"),
            (f"🔔 Notificaciones {badge}", "notifs"),
            ("🛒 Hacer Pedido", "make"),
            ("📦 Mis Pedidos", "myorders"),
        ]

# render sidebar and capture selection
st.sidebar.header(f"👤 {st.session_state.username} ({st.session_state.rol})")
# display items in sidebar (we can't render raw HTML easily inside radio, so build custom)
selected = st.sidebar.radio("Navegación", [label for label, key in side_items], index=0)

# logout
if st.sidebar.button("🚪 Cerrar sesión"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.rol = ""
    st.experimental_rerun()

# ---------------- Play sound once if there are new notifications ----------------
# We'll play when unread > last_notif_count for this user_key
session_key = f"notif_count_{user_key_for_notif}"
prev_cnt = st.session_state.get(session_key, 0)
if unread > prev_cnt:
    # play beep
    if beep_bytes:
        st.audio(beep_bytes, format="audio/wav")
    # mark that we've played sound in this session for this user
    st.session_state[session_key] = unread

# ---------------- Pages ----------------
def page_home():
    st.markdown("### 🏠 Inicio")
    st.write("Bienvenido — usa el menú lateral para navegar.")

def page_notifications():
    st.markdown("### 🔔 Notificaciones")
    notifs = list_notifications_for(user_key_for_notif)
    if notifs:
        for i, n in enumerate(notifs):
            status = "🔴 NUEVO" if not n.get("leido", False) else "✓ leído"
            st.markdown(f"<div class='notif'><b>{n.get('mensaje')}</b><div class='small'>{n.get('fecha')} — {status}</div></div>", unsafe_allow_html=True)
        if st.button("✅ Marcar todas como leídas"):
            mark_all_read_for(user_key_for_notif)
            st.success("Notificaciones marcadas como leídas.")
            st.experimental_rerun()
    else:
        st.info("No hay notificaciones para ti.")

def page_admin_users():
    st.markdown("### 👥 Usuarios (Admin)")
    users = load_json(USER_FILE, {})
    rows = []
    for u, d in users.items():
        rows.append({"usuario": u, "rol": d.get("rol")})
    st.table(rows)

def page_admin_stores():
    st.markdown("### 🏪 Tiendas (Admin)")
    st.json(load_json(TIENDAS_FILE, []))

def page_admin_orders():
    st.markdown("### 📦 Pedidos (Admin)")
    st.json(load_json(PEDIDOS_FILE, []))

def page_tendero_store():
    st.markdown("### 🏪 Mi Tienda")
    tiendas = load_json(TIENDAS_FILE, [])
    tienda = next((t for t in tiendas if t.get("dueno") == current), None)
    if tienda:
        st.success(f"Tienda: {tienda.get('nombre')}")
        nuevos_prod = st.text_area("Editar productos (separados por coma):", ",".join(tienda.get("productos", [])))
        if st.button("Actualizar productos"):
            tienda["productos"] = [p.strip() for p in nuevos_prod.split(",") if p.strip()]
            save_json(TIENDAS_FILE, tiendas)
            st.success("Productos actualizados.")
    else:
        nombre = st.text_input("Nombre de tu tienda:")
        productos = st.text_area("Productos (separados por coma):")
        if st.button("Registrar tienda"):
            tiendas.append({"nombre": nombre, "dueno": current, "productos": [p.strip() for p in productos.split(",") if p.strip()]})
            save_json(TIENDAS_FILE, tiendas)
            st.success("Tienda registrada.")

def page_tendero_received():
    st.markdown("### 📦 Pedidos recibidos")
    pedidos = load_json(PEDIDOS_FILE, [])
    tiendas = load_json(TIENDAS_FILE, [])
    mis_tiendas = [t.get("nombre") for t in tiendas if t.get("dueno") == current]
    recibidos = [p for p in pedidos if p.get("tienda") in mis_tiendas]
    if not recibidos:
        st.info("No hay pedidos para tus tiendas.")
        return
    for idx, p in enumerate(recibidos):
        st.markdown(f"**Pedido #{idx+1}** — {p.get('producto')} x{p.get('cantidad')} — {p.get('usuario')} — {p.get('direccion')} — Estado: {p.get('estado')}")
        if p.get("estado") == "pendiente":
            if st.button(f"📤 Marcar como ENVIADO #{idx+1}", key=f"send_{idx}"):
                # find and update in global pedidos (match by exact dict)
                all_pedidos = load_json(PEDIDOS_FILE, [])
                for j, ap in enumerate(all_pedidos):
                    if ap == p:
                        all_pedidos[j]["estado"] = "enviado"
                        save_json(PEDIDOS_FILE, all_pedidos)
                        # notify client and admin
                        add_notification(p.get("usuario"), "pedido_enviado", f"Tu pedido {p.get('producto')} en {p.get('tienda')} ha sido ENVIADO", {"tienda": p.get("tienda")})
                        add_notification("admin", "pedido_enviado", f"Pedido enviado: {p.get('producto')} de {p.get('usuario')}", {"tienda": p.get("tienda")})
                        st.success("Pedido marcado como enviado.")
                        st.experimental_rerun()
                        break

def page_client_make():
    st.markdown("### 🛒 Hacer pedido")
    tiendas = load_json(TIENDAS_FILE, [])
    if not tiendas:
        st.info("No hay tiendas registradas todavía.")
        return
    tienda_sel = st.selectbox("Selecciona tienda:", [t.get("nombre") for t in tiendas])
    # show products if available
    tienda_obj = next((t for t in tiendas if t.get("nombre") == tienda_sel), None)
    products = tienda_obj.get("productos", []) if tienda_obj else []
    if products:
        product = st.selectbox("Selecciona producto:", products)
    else:
        product = st.text_input("Producto (libre):")
    cantidad = st.number_input("Cantidad:", min_value=1, step=1)
    direccion = st.text_input("Dirección de entrega:")
    if st.button("🚀 Enviar pedido"):
        if product and direccion:
            create_order(current, tienda_sel, product, cantidad, direccion)
            st.success("Pedido creado correctamente.")
            st.experimental_rerun()
        else:
            st.error("Completa producto y dirección.")

def page_client_myorders():
    st.markdown("### 📦 Mis pedidos")
    pedidos = load_json(PEDIDOS_FILE, [])
    my = [p for p in pedidos if p.get("usuario") == current]
    if not my:
        st.info("No tienes pedidos.")
        return
    for i, p in enumerate(my):
        st.markdown(f"**Pedido #{i+1}** — {p.get('producto')} x{p.get('cantidad')} — {p.get('tienda')} — Estado: {p.get('estado')} — {p.get('fecha')}")

# ---------------- Routing based on selection ----------------
# Map the selected label back to the key
label_to_key = {label: key for label, key in side_items}
sel_key = label_to_key.get(selected, "home")

# Render page
if sel_key == "home":
    page_home()
elif sel_key == "notifs":
    page_notifications()
elif sel_key == "users":
    page_admin_users()
elif sel_key == "stores":
    page_admin_stores()
elif sel_key == "orders":
    page_admin_orders()
elif sel_key == "store":
    page_tendero_store()
elif sel_key == "received":
    page_tendero_received()
elif sel_key == "make":
    page_client_make()
elif sel_key == "myorders":
    page_client_myorders()
else:
    page_home()







