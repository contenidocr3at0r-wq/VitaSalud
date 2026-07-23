import streamlit as st
from datetime import datetime, date
import pandas as pd
from openai import OpenAI
from supabase import create_client, Client
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

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ======================
# CONFIGURACIÓN
# ======================
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ======================
# FUNCIONES DE AUTENTICACIÓN Y DATOS
# ======================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_user(email: str, password: str):
    try:
        password_hash = hash_password(password)
        result = supabase.table("users").insert({
            "email": email.lower().strip(),
            "password_hash": password_hash
        }).execute()
        return True, "Cuenta creada exitosamente"
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False, "Este email ya está registrado"
        return False, f"Error al crear cuenta: {str(e)}"

def login_user(email: str, password: str):
    try:
        result = supabase.table("users").select("id, password_hash").eq("email", email.lower().strip()).execute()
        if not result.data:
            return False, "Email o contraseña incorrectos", None
        
        user = result.data[0]
        if check_password(password, user["password_hash"]):
            return True, "Inicio de sesión exitoso", user["id"]
        return False, "Email o contraseña incorrectos", None
    except Exception as e:
        return False, f"Error: {str(e)}", None

def get_user_profile(user_id: int):
    try:
        result = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if not result.data:
            return None
        
        row = result.data[0]
        return {
            "nombre": row.get("nombre"),
            "sexo": row.get("sexo"),
            "edad": row.get("edad"),
            "peso": row.get("peso"),
            "altura": row.get("altura"),
            "objetivo": row.get("objetivo"),
            "nivel_actividad": row.get("nivel_actividad"),
            "experiencia": row.get("experiencia"),
            "lugar_entrenamiento": row.get("lugar_entrenamiento"),
            "restricciones": row.get("restricciones") or [],
            "alergias": row.get("alergias") or "",
            "limitaciones": row.get("limitaciones") or "",
            "fecha_inicio": row.get("fecha_inicio")
        }
    except Exception:
        return None

def save_user_profile(user_id: int, profile: dict):
    data = {
        "user_id": user_id,
        "nombre": profile.get("nombre"),
        "sexo": profile.get("sexo"),
        "edad": profile.get("edad"),
        "peso": profile.get("peso"),
        "altura": profile.get("altura"),
        "objetivo": profile.get("objetivo"),
        "nivel_actividad": profile.get("nivel_actividad"),
        "experiencia": profile.get("experiencia"),
        "lugar_entrenamiento": profile.get("lugar_entrenamiento"),
        "restricciones": profile.get("restricciones", []),
        "alergias": profile.get("alergias", ""),
        "limitaciones": profile.get("limitaciones", ""),
        "fecha_inicio": profile.get("fecha_inicio")
    }
    
    # Verificar si existe
    existing = supabase.table("profiles").select("user_id").eq("user_id", user_id).execute()
    if existing.data:
        supabase.table("profiles").update(data).eq("user_id", user_id).execute()
    else:
        supabase.table("profiles").insert(data).execute()

def load_user_meals(user_id: int):
    try:
        result = supabase.table("meals").select("*").eq("user_id", user_id).order("id", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []

def save_meal(user_id: int, meal: dict):
    supabase.table("meals").insert({
        "user_id": user_id,
        "fecha": meal["fecha"],
        "tipo": meal["tipo"],
        "hora": meal["hora"],
        "descripcion": meal["descripcion"],
        "calorias": meal.get("calorias"),
        "sensacion": meal["sensacion"],
        "hambre": meal.get("hambre"),
        "notas": meal.get("notas", "")
    }).execute()

def load_user_exercises(user_id: int):
    try:
        result = supabase.table("exercises").select("*").eq("user_id", user_id).order("id", desc=True).limit(50).execute()
        return result.data or []
    except Exception:
        return []

def save_exercise(user_id: int, exercise: dict):
    supabase.table("exercises").insert({
        "user_id": user_id,
        "fecha": exercise["fecha"],
        "tipo": exercise["tipo"],
        "duracion": exercise["duracion"],
        "intensidad": exercise["intensidad"],
        "sensacion": exercise.get("sensacion"),
        "notas": exercise.get("notas", "")
    }).execute()

def load_weight_log(user_id: int):
    try:
        result = supabase.table("weight_log").select("*").eq("user_id", user_id).order("id").execute()
        return result.data or []
    except Exception:
        return []

def save_weight(user_id: int, peso: float, fecha: str = None):
    if fecha is None:
        fecha = str(date.today())
    supabase.table("weight_log").insert({
        "user_id": user_id,
        "fecha": fecha,
        "peso": peso
    }).execute()

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
# FUNCIÓN DEL COACH
# ======================
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

Tu objetivo es ayudar al usuario a mejorar sus hábitos de alimentación y ejercicio de forma **segura, progresiva y realista**, usando feedback constante.

INFORMACIÓN DEL USUARIO:
{perfil_texto}

### REGLAS IMPORTANTES:

1. **Usuarios sedentarios o principiantes**:
   - NUNCA empieces con ejercicios de impacto el primer día.
   - La primera semana debe ser MUY suave: caminata, movilidad y estiramientos.
   
2. **Feedback de EJERCICIOS**:
   - Antes: pregunta cómo se siente.
   - Después: SIEMPRE pide feedback detallado (cómo se sintió, dolor, intensidad, energía).
   - Usa ese feedback para ajustar la siguiente sesión.

3. **Feedback de COMIDAS**:
   - Pregunta de forma natural cómo se sintió después de comer.

4. **Recomendación médica**:
   - Recomienda consultar a un médico cuando sea relevante (sedentarismo, limitaciones, etc.).

5. Sé proactivo, claro y motivador. Prioriza siempre la seguridad.

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
        return f"Lo siento, tuve un problema al conectar con la IA. Error: {str(e)}"

# ======================
# PANTALLA DE LOGIN
# ======================
if st.session_state.user_id is None:
    st.markdown('<div style="text-align:center; font-size:2.4rem; font-weight:700; color:#2E7D32;">🌱 VitaSalud</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; color:#555; margin-bottom:1.5rem;">Tu asistente personal de nutrición y ejercicio</div>', unsafe_allow_html=True)
    
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

# ======================
# CONTENIDO PRINCIPAL
# ======================
if st.session_state.profile is None:
    st.markdown('<div style="text-align:center; font-size:2.4rem; font-weight:700; color:#2E7D32;">🌱 VitaSalud</div>', unsafe_allow_html=True)
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

            food_keywords = ["comida", "comer", "almuerzo", "cena", "desayuno", "receta", "ingredientes", "dieta"]
            if any(w in prompt.lower() for w in food_keywords) or any(w in response.lower() for w in ["receta", "desayuno", "almuerzo", "cena"]):
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
        
        with st.form("meal_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                meal_type = st.selectbox("Tipo de comida", ["Desayuno", "Almuerzo", "Cena", "Snack / Merienda", "Otro"])
                meal_time = st.time_input("Hora aproximada", value=datetime.now().time())
            with col2:
                meal_date = st.date_input("Fecha", value=date.today())
                estimated_calories = st.number_input("Calorías aproximadas (opcional)", min_value=0, max_value=3000, value=0, step=50)

            description = st.text_area("¿Qué comiste?", placeholder="Ej: 1 pechuga de pollo + ensalada")
            
            col3, col4 = st.columns(2)
            with col3:
                feeling = st.select_slider("¿Cómo te sentiste después?", options=["Muy mal", "Mal", "Regular", "Bien", "Muy bien"], value="Bien")
            with col4:
                hunger_level = st.select_slider("Nivel de hambre", options=["Muy lleno", "Satisfecho", "Normal", "Todavía con hambre", "Muy hambriento"], value="Satisfecho")

            notes = st.text_area("Notas adicionales (opcional)")

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
                    st.success("¡Comida registrada!")
                else:
                    st.warning("Por favor escribe qué comiste.")

        if st.session_state.meals:
            st.markdown("#### Últimas comidas")
            for meal in st.session_state.meals[:8]:
                st.markdown(f"**{meal['fecha']} · {meal['tipo']}** ({meal.get('hora', '')})")
                st.write(meal["descripcion"])
                st.caption(f"Sensación: {meal.get('sensacion')} | Hambre: {meal.get('hambre')}")
                st.divider()

    elif page == "Ejercicio":
        st.markdown("### 💪 Registrar Ejercicio")
        
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

            how_felt = st.select_slider("¿Cómo te sentiste?", options=["Muy mal / dolor", "Incómodo", "Regular", "Bien", "Excelente"], value="Bien")
            notes = st.text_area("Notas (opcional)")

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
            st.markdown("#### Últimos ejercicios")
            for ex in st.session_state.exercises[:8]:
                st.markdown(f"**{ex['fecha']} · {ex['tipo']}** ({ex['duracion']} min)")
                st.write(f"Intensidad: {ex['intensidad']} | Sensación: {ex.get('sensacion')}")
                st.divider()

    elif page == "Progreso":
        st.markdown("### 📊 Mi Progreso")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Peso actual", f"{profile['peso']} kg")
        with col2:
            st.metric("Comidas", len(st.session_state.meals))
        with col3:
            st.metric("Ejercicios", len(st.session_state.exercises))
        with col4:
            try:
                inicio = datetime.strptime(str(profile["fecha_inicio"]), "%Y-%m-%d").date()
                dias = (date.today() - inicio).days
                st.metric("Días", max(dias, 0))
            except:
                st.metric("Días", 0)

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
            except:
                st.info("No se pudo generar el gráfico.")
        else:
            st.info("Registra tu peso al menos dos veces para ver la evolución.")

st.divider()
st.caption("VitaSalud · Versión MVP ·")
st.caption("⚠️ Esta herramienta no sustituye el consejo de un médico o nutricionista profesional.")
