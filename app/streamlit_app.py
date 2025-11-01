import streamlit as st
import json
import os
import time

# ---------------- CONFIGURACIÓN DE LA PÁGINA ----------------
st.set_page_config(
    page_title="MyBarrioYa",
    page_icon="🛒",
    layout="wide",
)

# ---------------- ESTILOS ----------------
st.markdown("""
    <style>
        body { background-color: #121212; }
        .main-title { text-align: center; font-size: 45px; color: #4CAF50; font-weight: bold; }
        .sub-title { text-align: center; font-size: 22px; color: #a1a1a1; margin-bottom: 30px; }
        .stButton>button {
            background-color: #4CAF50; color: white; border-radius: 10px;
            height: 3em; width: 100%; font-size: 18px;
        }
        .stButton>button:hover { background-color: #66bb6a; }
        .notification {
            background-color: #333;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            margin: 10px 0;
            text-align: center;
            animation: fadein 0.5s;
        }
        @keyframes fadein {
            from {opacity: 0;}
            to {opacity: 1;}
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- FUNCIONES DE ARCHIVOS ----------------
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- ARCHIVOS ----------------
USER_FILE = "usuarios.json"
TIENDAS_FILE = "tiendas.json"
PEDIDOS_FILE = "pedidos.json"

# ---------------- USUARIOS ----------------
def register_user(username, password, rol):
    users = load_json(USER_FILE, {})
    if username in users:
        return False
    users[username] = {"password": password, "rol": rol}
    save_json(USER_FILE, users)
    return True

def login_user(username, password):
    users = load_json(USER_FILE, {})
    if username in users and users[username]["password"] == password:
        return users[username]["rol"]
    return None

# ---------------- SESIÓN ----------------
for key in ["logged_in", "username", "rol"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ""

# ---------------- LOGIN / REGISTRO ----------------
if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>MyBarrioYa 🛒</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Tu tienda del barrio, en la palma de tu mano.</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Iniciar sesión", "🆕 Registrarse"])

    with tab1:
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            rol = login_user(username, password)
            if rol:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.rol = rol
                st.success(f"¡Bienvenido {username}! Has ingresado como {rol}.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with tab2:
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva contraseña", type="password")
        rol = st.selectbox("Selecciona tu rol", ["cliente", "tendero", "admin"])
        if st.button("Registrar"):
            if register_user(new_user, new_pass, rol):
                st.success("✅ Usuario registrado correctamente. Ahora inicia sesión.")
            else:
                st.warning("⚠️ El usuario ya existe.")
    st.stop()

# ---------------- CERRAR SESIÓN ----------------
st.sidebar.header(f"👤 {st.session_state.username} ({st.session_state.rol})")
if st.sidebar.button("🚪 Cerrar sesión"):
    for key in ["logged_in", "username", "rol"]:
        st.session_state[key] = False if key == "logged_in" else ""
    st.rerun()

# ---------------- CLIENTE ----------------
if st.session_state.rol == "cliente":
    page = st.sidebar.radio("Navegación", ["🏠 Inicio", "🛒 Hacer Pedido", "📦 Mis Pedidos"])
    
    if page == "🏠 Inicio":
        st.markdown("<h1 class='main-title'>Bienvenido a MyBarrioYa 🏘️</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Encuentra y pide en tus tiendas favoritas.</p>", unsafe_allow_html=True)
    
    elif page == "🛒 Hacer Pedido":
        tiendas = load_json(TIENDAS_FILE, [])
        if tiendas:
            tienda = st.selectbox("Selecciona una tienda:", [t["nombre"] for t in tiendas])
            producto = st.text_input("Producto:")
            cantidad = st.number_input("Cantidad:", min_value=1, step=1)
            direccion = st.text_input("Dirección de entrega:")
            if st.button("🚀 Enviar pedido"):
                if producto and direccion:
                    pedidos = load_json(PEDIDOS_FILE, [])
                    pedido = {
                        "usuario": st.session_state.username,
                        "tienda": tienda,
                        "producto": producto,
                        "cantidad": cantidad,
                        "direccion": direccion,
                        "estado": "Enviado"
                    }
                    pedidos.append(pedido)
                    save_json(PEDIDOS_FILE, pedidos)
                    st.success(f"✅ Pedido enviado a {tienda} correctamente.")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Por favor completa todos los campos.")
        else:
            st.info("Aún no hay tiendas registradas.")
    
    elif page == "📦 Mis Pedidos":
        pedidos = load_json(PEDIDOS_FILE, [])
        user_pedidos = [p for p in pedidos if p["usuario"] == st.session_state.username]
        if user_pedidos:
            for p in user_pedidos:
                st.markdown(f"""
                    <div class='notification'>
                        🛍️ <b>{p['producto']}</b> x {p['cantidad']} — {p['tienda']}<br>
                        📦 Estado: <b style='color:#4CAF50'>{p['estado']}</b><br>
                        📍 {p['direccion']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No tienes pedidos todavía.")

# ---------------- TENDERO ----------------
elif st.session_state.rol == "tendero":
    page = st.sidebar.radio("Panel de tienda", ["🏪 Mi Tienda", "📦 Pedidos Recibidos"])
    
    if page == "🏪 Mi Tienda":
        tiendas = load_json(TIENDAS_FILE, [])
        tienda = next((t for t in tiendas if t["dueno"] == st.session_state.username), None)
        if tienda:
            st.success(f"Tienda registrada: {tienda['nombre']}")
            nuevos_prod = st.text_area("Productos (separados por comas):", ",".join(tienda["productos"]))
            if st.button("Actualizar"):
                tienda["productos"] = [p.strip() for p in nuevos_prod.split(",") if p.strip()]
                save_json(TIENDAS_FILE, tiendas)
                st.success("Productos actualizados.")
        else:
            nombre_tienda = st.text_input("Nombre de tu tienda:")
            productos = st.text_area("Productos que vendes (separados por comas):")
            if st.button("Registrar tienda"):
                tiendas.append({
                    "nombre": nombre_tienda,
                    "dueno": st.session_state.username,
                    "productos": [p.strip() for p in productos.split(",") if p.strip()]
                })
                save_json(TIENDAS_FILE, tiendas)
                st.success("Tienda registrada correctamente.")

    elif page == "📦 Pedidos Recibidos":
        pedidos = load_json(PEDIDOS_FILE, [])
        mis_tiendas = [t["nombre"] for t in load_json(TIENDAS_FILE, []) if t["dueno"] == st.session_state.username]
        recibidos = [p for p in pedidos if p["tienda"] in mis_tiendas]
        
        if recibidos:
            st.info(f"📬 Tienes {len(recibidos)} pedidos nuevos.")
            for i, p in enumerate(recibidos):
                st.markdown(f"""
                    <div class='notification'>
                        🛒 Pedido de <b>{p['usuario']}</b><br>
                        Producto: <b>{p['producto']}</b> x {p['cantidad']}<br>
                        📍 {p['direccion']}<br>
                        Estado: <b style='color:#ffb300'>{p['estado']}</b>
                    </div>
                """, unsafe_allow_html=True)

                if st.button(f"✅ Marcar como entregado #{i+1}"):
                    p["estado"] = "Entregado"
                    save_json(PEDIDOS_FILE, pedidos)
                    st.success("Pedido marcado como entregado ✅")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Aún no has recibido pedidos.")

# ---------------- ADMIN ----------------
elif st.session_state.rol == "admin":
    page = st.sidebar.radio("Panel Admin", ["👥 Usuarios", "🏪 Tiendas", "📦 Pedidos"])
    
    if page == "👥 Usuarios":
        st.header("👥 Lista de usuarios")
        st.json(load_json(USER_FILE, {}))
    
    elif page == "🏪 Tiendas":
        st.header("🏪 Tiendas registradas")
        st.json(load_json(TIENDAS_FILE, []))
    
    elif page == "📦 Pedidos":
        st.header("📦 Todos los pedidos")
        st.json(load_json(PEDIDOS_FILE, []))






