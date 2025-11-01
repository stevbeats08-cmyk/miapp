import streamlit as st
import json
import os

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

        /* --- Ajustes para móviles --- */
        @media (max-width: 600px) {
            .main-title { font-size: 28px !important; }
            .sub-title { font-size: 16px !important; }
            .stButton>button { font-size: 16px !important; height: 2.8em !important; }
        }

        /* --- Cards tipo Rappi --- */
        .product-card {
            background-color: #1e1e1e;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: transform 0.2s ease;
        }
        .product-card:hover { transform: scale(1.02); }
        .product-title { font-size: 18px; color: #4CAF50; font-weight: bold; }
        .product-price { color: #ccc; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# ---------------- ARCHIVOS USADOS ----------------
USER_FILE = "usuarios.json"
TIENDAS_FILE = "tiendas.json"
PEDIDOS_FILE = "pedidos.json"

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
    # asegúrate de crear carpeta si es necesario (aquí asumimos la misma carpeta)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- FUNCIONES DE USUARIOS ----------------
def register_user(username, password, rol):
    users = load_json(USER_FILE, {})
    if not username:
        return False
    if username in users:
        return False
    users[username] = {"password": password, "rol": rol}
    save_json(USER_FILE, users)
    return True

def login_user(username, password):
    users = load_json(USER_FILE, {})
    if username in users and users[username].get("password") == password:
        return users[username].get("rol")
    return None

# ---------------- SESIÓN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

# --- Logo y título ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # si no tienes logo1.png, quita o comenta la línea siguiente
    if os.path.exists("logo1.png"):
        st.image("logo1.png", width=160)

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
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with tab2:
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva contraseña", type="password")
        rol = st.selectbox("Selecciona tu rol", ["cliente", "tendero", "admin"])
        if st.button("Registrar"):
            if not new_user or not new_pass:
                st.error("Debes ingresar usuario y contraseña.")
            else:
                if register_user(new_user, new_pass, rol):
                    st.success("✅ Usuario registrado correctamente. Ahora inicia sesión.")
                else:
                    st.warning("⚠️ El usuario ya existe o los datos no son válidos.")
    st.stop()

# ---------------- CERRAR SESIÓN ----------------
st.sidebar.header(f"👤 {st.session_state.username} ({st.session_state.rol})")
if st.sidebar.button("🚪 Cerrar sesión"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.rol = ""
    st.rerun()

# ---------------- MENÚS SEGÚN ROL ----------------
if st.session_state.rol == "cliente":
    page = st.sidebar.radio("Navegación", ["🏠 Inicio", "🛒 Hacer Pedido", "📦 Mis Pedidos"])

    if page == "🏠 Inicio":
        st.markdown("<h1 class='main-title'>Bienvenido a MyBarrioYa 🏘️</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Encuentra y pide en tus tiendas favoritas.</p>", unsafe_allow_html=True)

    elif page == "🛒 Hacer Pedido":
        tiendas = load_json(TIENDAS_FILE, [])
        if tiendas:
            tienda = st.selectbox("Selecciona una tienda:", [t.get("nombre", "Sin nombre") for t in tiendas])
            tienda_obj = next((t for t in tiendas if t.get("nombre") == tienda), None)
            productos = tienda_obj.get("productos", []) if tienda_obj else []
            if productos:
                producto = st.selectbox("Selecciona producto:", productos)
            else:
                producto = st.text_input("Producto:")
            cantidad = st.number_input("Cantidad:", min_value=1, step=1)
            direccion = st.text_input("Dirección de entrega:")
            if st.button("🚀 Hacer pedido"):
                if producto and direccion:
                    pedidos = load_json(PEDIDOS_FILE, [])
                    pedidos.append({
                        "usuario": st.session_state.username,
                        "tienda": tienda,
                        "producto": producto,
                        "cantidad": cantidad,
                        "direccion": direccion,
                        "estado": "pendiente"
                    })
                    save_json(PEDIDOS_FILE, pedidos)
                    st.success("✅ Pedido enviado correctamente.")
                else:
                    st.error("Por favor completa todos los campos.")
        else:
            st.info("Aún no hay tiendas registradas.")

    elif page == "📦 Mis Pedidos":
        pedidos = load_json(PEDIDOS_FILE, [])
        user_pedidos = [p for p in pedidos if p.get("usuario") == st.session_state.username]
        if user_pedidos:
            for p in user_pedidos:
                st.markdown(f"- **{p.get('cantidad')} x {p.get('producto')}** en **{p.get('tienda')}** → {p.get('direccion')} (Estado: {p.get('estado')})")
        else:
            st.info("No tienes pedidos todavía.")

elif st.session_state.rol == "tendero":
    page = st.sidebar.radio("Panel de tienda", ["🏪 Mi Tienda", "📦 Pedidos Recibidos"])

    if page == "🏪 Mi Tienda":
        tiendas = load_json(TIENDAS_FILE, [])
        tienda = next((t for t in tiendas if t.get("dueno") == st.session_state.username), None)
        if tienda:
            st.success(f"Tienda registrada: {tienda.get('nombre')}")
            actuales = tienda.get("productos", [])
            nuevos_prod = st.text_area("Productos (separados por comas):", ",".join(actuales))
            if st.button("Actualizar productos"):
                tienda["productos"] = [p.strip() for p in nuevos_prod.split(",") if p.strip()]
                save_json(TIENDAS_FILE, tiendas)
                st.success("Productos actualizados.")
        else:
            tiendas = load_json(TIENDAS_FILE, [])
            nombre_tienda = st.text_input("Nombre de tu tienda:")
            productos = st.text_area("Productos que vendes (separados por comas):")
            if st.button("Registrar tienda"):
                if not nombre_tienda:
                    st.error("Debes ingresar nombre de la tienda.")
                else:
                    tiendas.append({
                        "nombre": nombre_tienda,
                        "dueno": st.session_state.username,
                        "productos": [p.strip() for p in productos.split(",") if p.strip()]
                    })
                    save_json(TIENDAS_FILE, tiendas)
                    st.success("Tienda registrada correctamente.")

    elif page == "📦 Pedidos Recibidos":
        pedidos = load_json(PEDIDOS_FILE, [])
        mis_tiendas = [t.get("nombre") for t in load_json(TIENDAS_FILE, []) if t.get("dueno") == st.session_state.username]
        recibidos = [p for p in pedidos if p.get("tienda") in mis_tiendas]
        if recibidos:
            for i, p in enumerate(recibidos):
                st.markdown(f"**Pedido #{i+1}** - {p.get('cantidad')} x {p.get('producto')} para {p.get('direccion')} (Usuario: {p.get('usuario')})")
                # botón para marcar como entregado (actualiza el archivo)
                if st.button(f"Marcar entregado #{i+1}"):
                    # buscamos en pedidos globales y actualizamos el primer match
                    all_pedidos = load_json(PEDIDOS_FILE, [])
                    for ap in all_pedidos:
                        if ap == p:
                            ap["estado"] = "entregado"
                            break
                    save_json(PEDIDOS_FILE, all_pedidos)
                    st.success("Pedido marcado como entregado.")
                    st.experimental_rerun()
        else:
            st.info("Aún no has recibido pedidos.")

elif st.session_state.rol == "admin":
    page = st.sidebar.radio("Panel Admin", ["👥 Usuarios", "🏪 Tiendas", "📦 Pedidos"])

    if page == "👥 Usuarios":
        st.header("👥 Lista de usuarios")
        users = load_json(USER_FILE, {})
        st.json(users)

    elif page == "🏪 Tiendas":
        st.header("🏪 Tiendas registradas")
        tiendas = load_json(TIENDAS_FILE, [])
        st.json(tiendas)

    elif page == "📦 Pedidos":
        st.header("📦 Todos los pedidos")
        pedidos = load_json(PEDIDOS_FILE, [])
        st.json(pedidos)

else:
    st.warning("Rol no reconocido. Inicia sesión nuevamente.")





