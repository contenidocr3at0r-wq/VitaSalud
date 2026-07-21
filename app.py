import streamlit as st
from datetime import datetime, date
import pandas as pd
from openai import OpenAI
import sqlite3
import bcrypt
import json

# ======================
# CONFIGURACIÓN DE LA APP
# ======================
st.set_page_config(
    page_title="VitaSalud",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# CONFIGURACIÓN DEEPSEEK
# ======================
DEEPSEEK_API_KEY = "sk-16ba57fd0440454c848c268a55153fd1"
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ======================
# BASE DE DATOS
# ======================
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
        "edad": row[2],
        "peso": row[3],
        "altura": row[4],
        "objetivo": row[5],
        "nivel_actividad": row[6],
        "experiencia": row[7],
        "lugar_entrenamiento": row[8],
        "restricciones": json.loads(row[9]) if row[9] else [],
        "alergias": row[10] or "",
        "limitaciones": row[11] or "",
        "fecha_inicio": row[12]
    }

def save_user_profile(user_id: int, profile: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM profiles WHERE user_id = ?", (user_id,))
    exists = c.fetchone()
    
    data = (
        profile.get("nombre"),
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
                nombre=?, edad=?, peso=?, altura=?, objetivo=?, nivel_actividad=?,
                experiencia=?, lugar_entrenamiento=?, restricciones=?, alergias=?,
                limitaciones=?, fecha_inicio=?
            WHERE user_id=?
        ''', data)
    else:
        c.execute('''
            INSERT INTO profiles (
                nombre, edad, peso, altura, objetivo, nivel_actividad,
                experiencia, lugar_entrenamiento, restricciones, alergias,
                limitaciones, fecha_inicio, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    conn.commit()
    conn.close()

def load_user_meals(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT fecha, tipo, hora, descripcion, calorias, sensacion, hambre, notas FROM meals WHERE user_id = ? ORDER BY id DESC LIMIT 50", (user_id,))
    rows = c.fetchallAquí tienes el **código completo** con el sistema de Login. Cópialo todo:

```python
import streamlit as st
from datetime import datetime, date
import pandas as pd
from openai import OpenAI
import sqlite3
import bcrypt
import json

# ======================
# CONFIGURACIÓN DE LA APP
# ======================
st.set_page_config(
    page_title="VitaSalud",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# CONFIGURACIÓN DEEPSEEK
# ======================
DEEPSEEK_API_KEY = "sk-16ba57fd0440454c848c268a55153fd1"
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ======================
# BASE DE DATOS
# ======================
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
        "edad": row[2],
        "peso": row[3],
        "altura": row[4],
        "objetivo": row[5],
        "nivel_actividad": row[6],
        "experiencia": row[7],
        "lugar_entrenamiento": row[8],
        "restricciones": json.loads(row[9]) if row[9] else [],
        "alergias": row[10] or "",
        "limitaciones": row[11] or "",
        "fecha_inicio": row[12]
    }

def save_user_profile(user_id: int, profile: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM profiles WHERE user_id = ?", (user_id,))
    exists = c.fetchone()
    
    data = (
        profile.get("nombre"),
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
                nombre=?, edad=?, peso=?, altura=?, objetivo=?, nivel_actividad=?,
                experiencia=?, lugar_entrenamiento=?, restricciones=?, alergias=?,
                limitaciones=?, fecha_inicio=?
            WHERE user_id=?
        ''', data)
    else:
        c.execute('''
            INSERT INTO profiles (
                nombre, edad, peso, altura, objetivo, nivel_actividad,
                experiencia, lugar_entrenamiento, restricciones, alergias,
                limitaciones, fecha_inicio, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    conn.commit()
    conn.close()

def load_user_meals(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT fecha, tipo, hora, descripcion, calorias, sensacion, hambre, notas FROM meals WHERE user_id = ? ORDER BY id DESC LIMIT 50", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    return [{
        "fecha": r[0], "tipo": r[1], "hora": r[2], "descripcion": r[3],
        "calorias": r[4], "sensacion": r[5], "hambre": r[6], "notas": r[7]
    } for r in rows]

def save_meal(user_id: int, meal: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO meals (user_id, fecha, tipo, hora, descripcion, calorias, sensacion, hambre, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, meal["fecha"], meal["tipo"], meal["hora"], meal["descripcion"],
        meal.get("calorias"), meal["sensacion"], meal.get("hambre"), meal.get("notas", "")
    ))
    conn.commit()
    conn.close()

def load_user_exercises(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT fecha, tipo, duracion, intensidad, sensacion, notas FROM exercises WHERE user_id = ? ORDER BY id DESC LIMIT 50", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    return [{
        "fecha": r[0], "tipo": r[1], "duracion": r[2], "intensidad": r[3],
        "sensacion": r[4], "notas": r[5]
    } for r in rows]

def save_exercise(user_id: int, exercise: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO exercises (user_id, fecha, tipo, duracion, intensidad, sensacion, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, exercise["fecha"], exercise["tipo"], exercise["duracion"],
        exercise["intensidad"], exercise.get("sensacion"), exercise.get("notas", "")
    ))
    conn.commit()
    conn.close()

def load_weight_log(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT fecha, peso FROM weight_log WHERE user_id = ? ORDER BY id", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"fecha": r[0], "peso": r[1]} for r in rows]

def save_weight(user_id: int, peso: float, fecha: str = None):
    if fecha is None:
        fecha = str(date.today())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO weight_log (user_id, fecha, peso) VALUES (?, ?, ?)", (user_id, fecha, peso))
    conn.commit()
    conn.close()

# ======================
# ESTADO DE LA SESIÓN
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

# ======================
# ESTILOS
# ======================
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        text-align: center;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)
