import streamlit as st
from datetime import datetime, date
import pandas as pd
from openai import OpenAI
import sqlite3
import bcrypt
import json

st.set_page_config(
    page_title="VitaSalud",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Ocultar menú
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

DB_PATH = "vitasalud.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            nombre TEXT,
            sexo TEXT,
            edad INTEGER,
            peso REAL,
            altura INTEGER,
            objetivo TEXT,
            nivel_actividad TEXT,
            experiencia TEXT,
            lugar_entrenamiento TEXT,
            restricciones TEXT,
            alergias TEXT,
            limitaciones TEXT,
            fecha_inicio TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fecha TEXT,
            tipo TEXT,
            hora TEXT,
            descripcion TEXT,
            calorias INTEGER,
            sensacion TEXT,
            hambre TEXT,
            notas TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fecha TEXT,
            tipo TEXT,
            duracion INTEGER,
            intensidad TEXT,
            sensacion TEXT,
            notas TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS weight_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fecha TEXT,
            peso REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def update_db_schema():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE profiles ADD COLUMN sexo TEXT")
        conn.commit()
    except:
        pass  # La columna ya existe
    conn.close()

update_db_schema()

# ======================
# FUNCIONES DE AUTENTICACIÓN
# ======================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_user(email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        password_hash = hash_password(password)
        c.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.lower().strip(), password_hash, str(datetime.now()))
        )
        conn.commit()
        return True, "Cuenta creada exitosamente"
    except sqlite3.IntegrityError:
        return False, "Este email ya está registrado"
    finally:
        conn.close()

def login_user(email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE email = ?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    
    if row is None:
        return False, "Email o contraseña incorrectos", None
    
    user_id, password_hash = row
    if check_password(password, password_hash):
        return True, "Inicio de sesión exitoso", user_id
    return False, "Email o contraseña incorrectos", None

def get_user_profile(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return {
        "nombre": row[1],
        "sexo": row[2],
        "edad": row[3],
        "peso": row[4],
        "altura": row[5],
        "objetivo": row[6],
        "nivel_actividad": row[7],
        "experiencia": row[8],
        "lugar_entrenamiento": row[9],
        "restricciones": json.loads(row[10]) if row[10] else [],
        "alergias": row[11] or "",
        "limitaciones": row[12] or "",
        "fecha_inicio": row[13]
    }

def save_user_profile(user_id: int, profile: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM profiles WHERE user_id = ?", (user_id,))
    exists = c.fetchone()
    
    data = (
        profile.get("nombre"),
        profile.get("sexo"),
        profile.get("edad"),
        profile.get("peso"),
        profile.get("altura"),
        profile.get("objetivo"),
        profile.get("nivel_actividad"),
        profile.get("experiencia"),
        profile.get("lugar_entrenamiento"),
        json.dumps(profile.get("restricciones", [])),
        profile.get("alergias", ""),
        profile.get("limitaciones", ""),
        profile.get("fecha_inicio"),
        user_id
    )
    
    if exists:
        c.execute('''
            UPDATE profiles SET 
                nombre=?, sexo=?, edad=?, peso=?, altura=?, objetivo=?, nivel_actividad=?,
                experiencia=?, lugar_entrenamiento=?, restricciones=?, alergias=?,
                limitaciones=?, fecha_inicio=?
            WHERE user_id=?
        ''', data)
    else:
        c.execute('''
            INSERT INTO profiles (
                nombre, sexo, edad, peso, altura, objetivo, nivel_actividad,
                experiencia, lugar_entrenamiento, restricciones, alergias,
                limitaciones, fecha_inicio, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    conn.commit()
    conn.close()

# ======================
# RESTO DEL CÓDIGO (login, chat, etc.)
# ======================
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "meals" not in st.session_state:
    st.session_state.meals = []
if "exercises" not in st.session_state:
    st.session_state.exercises = []
if "weight_log" not in st.session_state:
    st.session_state.weight_log = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "Chat"
if "last_recipe" not in st.session_state:
    st.session_state.last_recipe = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

def get_coach_response(user_input: str, profile: dict, chat_history: list) -> str:
    perfil_texto = f"""
Nombre: {profile.get('nombre', 'Usuario')}
Sexo: {profile.get('sexo', 'No especificado')}
Edad: {profile.get('edad', 'No especificada')}
Peso: {profile.get('peso', 'No especificado')} kg
Altura: {profile.get('altura', 'No especificada')} cm
Objetivo: {profile.get('objetivo', 'Mejorar hábitos')}
Nivel de actividad: {profile.get('nivel_actividad', 'No especificado')}
Experiencia con ejercicio: {profile.get('experiencia', 'Principiante')}
Prefiere entrenar en: {profile.get('lugar_entrenamiento', 'Casa')}
Condiciones de salud: {', '.join(profile.get('restricciones', ['Ninguna']))}
Alergias o alimentos que no come: {profile.get('alergias', 'Ninguna')}
Limitaciones físicas: {profile.get('limitaciones', 'Ninguna')}
"""

    system_prompt = f"""Eres VitaSalud, un coach de nutrición y ejercicio profesional, amable, motivador, empático y muy proactivo. 
Hablas en español latinoamericano de forma clara, cercana y natural.

Tu objetivo es ayudar al usuario a mejorar sus hábitos de alimentación y ejercicio de forma **segura, progresiva y realista**.

INFORMACIÓN DEL USUARIO:
{perfil_texto}

### REGLAS DE SEGURIDAD Y PROGRESIÓN (MUY IMPORTANTES):

1. **Usuarios sedentarios o principiantes**:
   - NUNCA empieces con sentadillas, planchas, flexiones o ejercicios de impacto el primer día.
   - La primera semana debe ser MUY suave: caminata, movilidad articular, estiramientos suaves y ejercicios de activación.
   - Siempre pregunta cómo se sintió después de cada sesión para ajustar.

2. **Recomendación médica**:
   - Recomienda consultar a un médico cuando sea relevante (sedentarismo, limitaciones, etc.).

3. **Nutrición y ejercicio**:
   - Adapta recomendaciones según sexo, edad y condiciones.
   - Sé concreto y práctico.

Responde siempre como el coach de VitaSalud."""

    messages_for_api = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history[-10:]:
        messages_for_api.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    messages_for_api.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Lo siento, tuve un problema al conectar con la IA. Error: {str(e)}\n\nPor favor intenta de nuevo en un momento."

# ======================
# PANTALLA DE LOGIN / REGISTRO
# ======================
if st.session_state.user_id is None:
    st.markdown('<div class="main-header">🌱 VitaSalud</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tu asistente personal de nutrición y ejercicio</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_mode == "login":
            st.subheader("Iniciar sesión")
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="tu@email.com")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.error("Por favor completa todos los campos")
                    else:
                        success, msg, user_id = login_user(email, password)
                        if success:
                            st.session_state.user_id = user_id
                            st.session_state.user_email = email.lower().strip()
                            profile = get_user_profile(user_id)
                            st.session_state.profile = profile
                            st.session_state.meals = load_user_meals(user_id)
                            st.session_state.exercises = load_user_exercises(user_id)
                            st.session_state.weight_log = load_weight_log(user_id)
                            st.session_state.messages = []
                            st.session_state.current_page = "Chat"
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            st.markdown("---")
            if st.button("¿No tienes cuenta? Regístrate aquí", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
        
        else:
            st.subheader("Crear cuenta")
            
            with st.form("register_form"):
                email = st.text_input("Email", placeholder="tu@email.com")
                password = st.text_input("Contraseña", type="password")
                password2 = st.text_input("Confirmar contraseña", type="password")
                submitted = st.form_submit_button("Crear cuenta", use_container_width=True)
                
                if submitted:
                    if not email or not password or not password2:
                        st.error("Por favor completa todos los campos")
                    elif password != password2:
                        st.error("Las contraseñas no coinciden")
                    elif len(password) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                    else:
                        success, msg = register_user(email, password)
                        if success:
                            st.success(msg + ". Ahora puedes iniciar sesión.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        else:
                            st.error(msg)
            
            st.markdown("---")
            if st.button("¿Ya tienes cuenta? Inicia sesión", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
    
    st.stop()

# ======================
# APP PRINCIPAL
# ======================
user_id = st.session_state.user_id

with st.sidebar:
    st.markdown("## 🌱 VitaSalud")
    st.caption(f"Sesión: {st.session_state.user_email}")
    st.divider()

    if st.session_state.profile is None:
        st.subheader("Completa tu perfil")

        with st.form("profile_form"):
            nombre = st.text_input("¿Cómo te llamas?", placeholder="Ej: Carlos")
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
            edad = st.number_input("Edad", min_value=15, max_value=90, value=35)
            peso = st.number_input("Peso actual (kg)", min_value=40.0, max_value=250.0, value=85.0, step=0.1)
            altura = st.number_input("Altura (cm)", min_value=140, max_value=220, value=170)

            objetivo = st.selectbox("Objetivo principal", [
                "Bajar de peso", "Mantener peso", "Ganar músculo", "Mejorar hábitos generales"
            ])

            nivel_actividad = st.selectbox("Nivel de actividad actual", [
                "Sedentario (poco o nada de ejercicio)",
                "Ligero (1-2 días por semana)",
                "Moderado (3-4 días por semana)",
                "Activo (5+ días por semana)"
            ])

            experiencia = st.selectbox("Experiencia con el ejercicio", [
                "Principiante", "Intermedio", "Avanzado"
            ])

            lugar_entrenamiento = st.selectbox("¿Dónde prefieres entrenar?", [
                "Casa", "Gimnasio", "Ambos"
            ])

            restricciones = st.multiselect(
                "Condiciones de salud / Restricciones",
                ["Ninguna", "Diabetes / prediabetes", "Hipertensión", "Sin gluten", "Sin lactosa", "Vegetariano", "Vegano"],
                default=["Ninguna"]
            )

            alergias = st.text_area("Alergias o alimentos que NO comes", placeholder="Ej: maní, mariscos...")
            limitaciones = st.text_area("Afecciones o limitaciones físicas", placeholder="Ej: escoliosis...")

            submitted = st.form_submit_button("Guardar perfil", use_container_width=True)

            if submitted:
                if not nombre or nombre.strip() == "":
                    st.error("Por favor escribe tu nombre.")
                else:
                    profile = {
                        "nombre": nombre.strip(),
                        "sexo": sexo,
                        "edad": edad,
                        "peso": peso,
                        "altura": altura,
                        "objetivo": objetivo,
                        "nivel_actividad": nivel_actividad,
                        "experiencia": experiencia,
                        "lugar_entrenamiento": lugar_entrenamiento,
                        "restricciones": restricciones,
                        "alergias": alergias.strip() if alergias else "",
                        "limitaciones": limitaciones.strip() if limitaciones else "",
                        "fecha_inicio": str(date.today())
                    }
                    save_user_profile(user_id, profile)
                    save_weight(user_id, peso)
                    st.session_state.profile = profile
                    st.session_state.weight_log = load_weight_log(user_id)
                    st.session_state.current_page = "Chat"
                    st.success("¡Perfil guardado!")
                    st.rerun()
    else:
        profile = st.session_state.profile
        st.markdown(f"### Hola, **{profile['nombre']}** 👋")
        st.write(f"**Sexo:** {profile.get('sexo', 'No especificado')}")
        st.write(f"**Objetivo:** {profile['objetivo']}")
        st.write(f"**Peso:** {profile['peso']} kg")
        st.write(f"**Experiencia:** {profile.get('experiencia', 'No definida')}")

        if st.button("✏️ Editar perfil", use_container_width=True):
            st.session_state.profile = None
            st.rerun()

        st.divider()

        pages = {
            "Chat": "💬 Chat con el Coach",
            "Comida": "🍽️ Registrar Comida",
            "Ejercicio": "💪 Registrar Ejercicio",
            "Progreso": "📊 Mi Progreso"
        }

        selected = st.radio(
            "Navegación",
            list(pages.keys()),
            format_func=lambda x: pages[x],
            index=list(pages.keys()).index(st.session_state.current_page) if st.session_state.current_page in pages else 0,
            label_visibility="collapsed"
        )
        st.session_state.current_page = selected

        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# El resto del código (chat, comida, ejercicio, progreso) se mantiene igual
# (puedes copiarlo del código anterior si es necesario)

st.divider()
st.caption("VitaSalud · Versión MVP · Conectado a DeepSeek AI")
st.caption("⚠️ Esta herramienta no sustituye el consejo de un médico o nutricionista profesional.")
