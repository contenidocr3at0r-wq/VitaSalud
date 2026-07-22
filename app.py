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

# Ocultar completamente el menú superior
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
        "sexo": row[13]
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
        sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
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

def get_coach_response(user_input: str, profile: dict, chat_history: list) -> str:
    perfil_texto = f"""
Nombre: {profile.get('nombre', 'Usuario')}
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
Hablas en español latinoamericano de forma clara, cercana y natural (como un buen entrenador personal y nutricionista práctico).

Tu objetivo es ayudar al usuario a mejorar sus hábitos de alimentación y ejercicio de forma **segura, progresiva y realista**.

INFORMACIÓN DEL USUARIO:
{perfil_texto}

### REGLAS DE SEGURIDAD Y PROGRESIÓN (MUY IMPORTANTES):

1. **Usuarios sedentarios o principiantes**:
   - NUNCA empieces con sentadillas, planchas, flexiones o ejercicios de impacto el primer día.
   - La primera semana debe ser MUY suave: caminata, movilidad articular, estiramientos suaves y ejercicios de activación (ej. marcha en el lugar, círculos de brazos, elevaciones de talones suaves).
   - Explica por qué empezamos suave: "Tu cuerpo necesita adaptarse para evitar lesiones".
   - Siempre pregunta cómo se sintió después de cada sesión para ajustar.

2. **Recomendación médica**:
   - Si el usuario es sedentario, tiene sobrepeso importante, limitaciones físicas o es principiante, recomienda de forma natural y no pesada consultar a un médico antes de empezar un programa de ejercicio.
   - Ejemplo: "Antes de comenzar, te recomiendo que consultes con tu médico, especialmente si hace tiempo que no haces ejercicio. Es una medida de seguridad."
   - No lo repitas en cada mensaje. Solo cuando sea relevante (inicio de plan de ejercicio, síntomas, etc.).

3. **Nutrición**:
   - Sé concreto con porciones y preparaciones.
   - Si el usuario pide recetas, sé creativo y práctico.
   - Ocasionalmente (no en cada respuesta) sugiere que una consulta con un nutricionista puede ayudar a personalizar aún más su plan.
   - Nunca ignores alergias o restricciones alimentarias.

4. **Recomendaciones de especialistas**:
   - Si la conversación lo amerita (dolor, síntomas, condiciones específicas), puedes sugerir suavemente consultar a un médico general, nutricionista, fisioterapeuta o especialista.
   - Sé eventual y no insistente. No lo conviertas en un discurso médico.

5. **Estilo de comunicación**:
   - Sé proactivo: haz preguntas útiles, ofrece opciones claras y guía el siguiente paso.
   - Usa un tono motivador pero realista. Evita el "todo o nada".
   - Organiza las respuestas con listas y negritas cuando sea útil.
   - Al final de respuestas importantes, siempre ofrece un siguiente paso o pregunta.

6. **Límites**:
   - Nunca diagnostiques enfermedades.
   - Nunca sustituyas el consejo de un profesional de la salud.
   - Prioriza siempre la seguridad sobre resultados rápidos.

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

user_id = st.session_state.user_id

with st.sidebar:
    st.markdown("## 🌱 VitaSalud")
    st.caption(f"Sesión: {st.session_state.user_email}")
    st.divider()

    if st.session_state.profile is None:
        st.subheader("Completa tu perfil")

        with st.form("profile_form"):
            nombre = st.text_input("¿Cómo te llamas?", placeholder="Ej: Carlos")
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

            alergias = st.text_area("Alergias o alimentos que NO comes", placeholder="Ej: maní, mariscos, huevo...")
            limitaciones = st.text_area("Afecciones o limitaciones físicas", placeholder="Ej: escoliosis, rodilla operada...")

            submitted = st.form_submit_button("Guardar perfil", use_container_width=True)

            if submitted:
                if not nombre or nombre.strip() == "":
                    st.error("Por favor escribe tu nombre.")
                else:
                    profile = {
                        "nombre": nombre.strip(),
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
        st.write(f"**Objetivo:** {profile['objetivo']}")
        st.write(f"**Peso:** {profile['peso']} kg")
        st.write(f"**Experiencia:** {profile.get('experiencia', 'No definida')}")
        st.write(f"**Entrena en:** {profile.get('lugar_entrenamiento', 'No definido')}")

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

if st.session_state.profile is None:
    st.markdown('<div class="main-header">🌱 VitaSalud</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tu asistente personal de nutrición y ejercicio</div>', unsafe_allow_html=True)
    st.info("👈 Completa tu perfil en la barra lateral para comenzar.")
else:
    profile = st.session_state.profile
    page = st.session_state.current_page

    if page == "Chat":
        st.markdown("### 💬 Chat con tu Coach")
        st.caption(f"Hola {profile['nombre']}, ¿en qué te ayudo hoy?")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Escribe tu mensaje aquí..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    response = get_coach_response(prompt, profile, st.session_state.messages)
                st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})

            food_keywords = ["comida", "comer", "almuerzo", "cena", "desayuno", "receta", "ingredientes", "dieta", "alimentación", "menu", "menú"]
            if any(w in prompt.lower() for w in food_keywords) or any(w in response.lower() for w in ["receta", "desayuno", "almuerzo", "cena", "ingredientes"]):
                st.session_state.last_recipe = response

            st.rerun()

        if st.session_state.last_recipe:
            st.divider()
            st.download_button(
                label="📄 Descargar última receta / recomendación",
                data=st.session_state.last_recipe,
                file_name=f"receta_vitasalud_{date.today()}.txt",
                mime="text/plain",
                use_container_width=True
            )

    elif page == "Comida":
        st.markdown("### 🍽️ Registrar Comida")
        st.caption("Registra lo que comiste para que el coach pueda darte mejores recomendaciones.")

        with st.form("meal_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                meal_type = st.selectbox("Tipo de comida", ["Desayuno", "Almuerzo", "Cena", "Snack / Merienda", "Otro"])
                meal_time = st.time_input("Hora aproximada", value=datetime.now().time())
            with col2:
                meal_date = st.date_input("Fecha", value=date.today())
                estimated_calories = st.number_input("Calorías aproximadas (opcional)", min_value=0, max_value=3000, value=0, step=50)

            description = st.text_area("¿Qué comiste?", placeholder="Ej: 1 pechuga de pollo + ensalada + ½ taza de arroz")

            col3, col4 = st.columns(2)
            with col3:
                feeling = st.select_slider("¿Cómo te sentiste después?", options=["Muy mal", "Mal", "Regular", "Bien", "Muy bien"], value="Bien")
            with col4:
                hunger_level = st.select_slider("Nivel de hambre después de comer", options=["Muy lleno", "Satisfecho", "Normal", "Todavía con hambre", "Muy hambriento"], value="Satisfecho")

            notes = st.text_area("Notas adicionales (opcional)", placeholder="Ej: Comí fuera, me sentí hinchado...")

            if st.form_submit_button("Guardar comida", use_container_width=True):
                if description and description.strip():
                    meal = {
                        "fecha": str(meal_date),
                        "tipo": meal_type,
                        "hora": str(meal_time)[:5],
                        "descripcion": description.strip(),
                        "calorias": estimated_calories if estimated_calories > 0 else None,
                        "sensacion": feeling,
                        "hambre": hunger_level,
                        "notas": notes.strip() if notes else ""
                    }
                    save_meal(user_id, meal)
                    st.session_state.meals = load_user_meals(user_id)
                    st.success("¡Comida registrada correctamente!")
                else:
                    st.warning("Por favor escribe qué comiste.")

        if st.session_state.meals:
            st.markdown("#### Últimas comidas registradas")
            for meal in st.session_state.meals[:8]:
                st.markdown(f"**{meal['fecha']} · {meal['tipo']}** ({meal['hora']})")
                st.write(meal["descripcion"])
                extra = f"Sensación: {meal['sensacion']} | Hambre: {meal.get('hambre', 'No registrada')}"
                if meal.get("calorias"):
                    extra += f" | ≈ {meal['calorias']} kcal"
                st.caption(extra)
                if meal.get("notas"):
                    st.caption(f"Notas: {meal['notas']}")
                st.divider()

    elif page == "Ejercicio":
        st.markdown("### 💪 Registrar Ejercicio")
        st.caption("Registra tu actividad para que el coach pueda ajustar tus rutinas de forma segura y progresiva.")

        with st.form("exercise_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                exercise_type = st.selectbox("Tipo de ejercicio", [
                    "Caminata", "Movilidad / Estiramientos", "Rutina en casa", "Gimnasio",
                    "Cardio suave", "Yoga", "Otro"
                ])
                duration = st.number_input("Duración (minutos)", min_value=5, max_value=180, value=20)
            with col2:
                exercise_date = st.date_input("Fecha", value=date.today(), key="ex_date")
                intensity = st.select_slider("Intensidad", options=["Muy suave", "Suave", "Moderada", "Intensa", "Muy intensa"], value="Suave")

            how_felt = st.select_slider("¿Cómo te sentiste durante/después?", options=["Muy mal / dolor", "Incómodo", "Regular", "Bien", "Excelente"], value="Bien")
            notes = st.text_area("Notas (opcional)", placeholder="Ej: Hice movilidad de cadera y caminata suave.")

            if st.form_submit_button("Guardar ejercicio", use_container_width=True):
                exercise = {
                    "fecha": str(exercise_date),
                    "tipo": exercise_type,
                    "duracion": duration,
                    "intensidad": intensity,
                    "sensacion": how_felt,
                    "notas": notes.strip() if notes else ""
                }
                save_exercise(user_id, exercise)
                st.session_state.exercises = load_user_exercises(user_id)
                st.success("¡Ejercicio registrado!")

        if st.session_state.exercises:
            st.markdown("#### Últimos ejercicios registrados")
            for ex in st.session_state.exercises[:8]:
                st.markdown(f"**{ex['fecha']} · {ex['tipo']}** ({ex['duracion']} min)")
                st.write(f"Intensidad: {ex['intensidad']} | Sensación: {ex.get('sensacion', 'No registrada')}")
                if ex.get("notas"):
                    st.caption(ex["notas"])
                st.divider()

    elif page == "Progreso":
        st.markdown("### 📊 Mi Progreso")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Peso actual", f"{profile['peso']} kg")
        with col2:
            st.metric("Comidas registradas", len(st.session_state.meals))
        with col3:
            st.metric("Ejercicios registrados", len(st.session_state.exercises))
        with col4:
            try:
                inicio = datetime.strptime(profile["fecha_inicio"], "%Y-%m-%d").date()
                dias = (date.today() - inicio).days
                st.metric("Días en VitaSalud", max(dias, 0))
            except Exception:
                st.metric("Días en VitaSalud", 0)

        st.divider()

        with st.expander("➕ Registrar nuevo peso"):
            new_weight = st.number_input("Peso (kg)", min_value=40.0, max_value=250.0, value=float(profile["peso"]), step=0.1)
            if st.button("Guardar peso"):
                save_weight(user_id, new_weight)
                st.session_state.profile["peso"] = new_weight
                save_user_profile(user_id, st.session_state.profile)
                st.session_state.weight_log = load_weight_log(user_id)
                st.success("Peso actualizado")
                st.rerun()

        if len(st.session_state.weight_log) > 1:
            st.markdown("#### Evolución del peso")
            try:
                df_weight = pd.DataFrame(st.session_state.weight_log)
                df_weight["fecha"] = pd.to_datetime(df_weight["fecha"])
                st.line_chart(df_weight.set_index("fecha")["peso"])
            except Exception:
                st.info("No se pudo generar el gráfico todavía.")
        else:
            st.info("Registra tu peso al menos dos veces para ver la evolución.")

        st.divider()
        st.markdown("#### Resumen de actividad reciente")

        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Últimas comidas:**")
            if st.session_state.meals:
                for m in st.session_state.meals[:5]:
                    st.caption(f"{m['fecha']} · {m['tipo']}: {m['descripcion'][:45]}...")
            else:
                st.caption("Aún no hay comidas registradas.")
        with col_b:
            st.write("**Últimos ejercicios:**")
            if st.session_state.exercises:
                for e in st.session_state.exercises[:5]:
                    st.caption(f"{e['fecha']} · {e['tipo']} ({e['duracion']} min)")
            else:
                st.caption("Aún no hay ejercicios registrados.")

st.divider()
st.caption("VitaSalud · Versión MVP · Conectado a DeepSeek AI")
st.caption("⚠️ Esta herramienta no sustituye el consejo de un médico o nutricionista profesional.")
