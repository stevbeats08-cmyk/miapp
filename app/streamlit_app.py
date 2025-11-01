import streamlit as st
import json
import os

# ---------------- CONFIGURACIÓN ----------------
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
    </style>
""", unsafe_allow_html=True)

# ---------------- FUNCIONES DE ARCHIVOS ----------------
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- ARCHIVOS ----------------
USER_FILE = "usuarios.json"
TIENDAS_FILE = "tiendas.json"
PEDIDOS_FILE = "pedidos.json"

# ---------------- ASEGURAR ADMIN ----------------
def ensure_admin():
    users = load_json(USER_FILE, {})
    if "briamCeo" not in users:
        users["briamCeo"] = {"password": "12345", "rol": "admin"}
        save_json(USER_FILE, users)
ensure_admin()

# ---------------- FUNCIONES DE USUARIOS ----------------
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
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

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







