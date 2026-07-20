import streamlit as st
from datetime import datetime, date
import pandas as pd
from openai import OpenAI

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

# ======================
# ESTADO DE LA SESIÓN
# ======================
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

# ======================
# FUNCIÓN DEL COACH CON DEEPSEEK
# ======================
def get_coach_response(user_input: str, profile: dict, chat_history: list) -> str:
    """Llama a DeepSeek para generar una respuesta personalizada."""
    
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

    system_prompt = f"""Eres VitaSalud, un coach de nutrición y ejercicio profesional, amable, motivador y proactivo. 
Hablas en español latinoamericano de forma clara y cercana.

Tu objetivo es ayudar al usuario a mejorar sus hábitos de alimentación y ejercicio de forma segura y personalizada.

INFORMACIÓN DEL USUARIO:
{perfil_texto}

REGLAS IMPORTANTES:
1. Siempre ten en cuenta las alergias, restricciones y limitaciones físicas del usuario. Nunca recomiendes algo que las contradiga.
2. Sé proactivo: haz preguntas útiles, ofrece opciones y guía al usuario.
3. Cuando des recomendaciones de comida, sé concreto (porciones aproximadas, cómo prepararlo).
4. Cuando el usuario diga qué ingredientes tiene, crea una receta práctica y saludable.
5. Adapta las rutinas de ejercicio según si entrena en casa o gimnasio y según su experiencia.
6. Si hay limitaciones físicas, prioriza seguridad y sugiere alternativas.
7. No diagnostiques enfermedades ni sustituyas a un médico. Si es necesario, recomienda consultar a un profesional.
8. Mantén las respuestas claras, organizadas y motivadoras. Usa listas y negritas cuando ayude a la lectura.
9. Al final de tus respuestas importantes, ofrece un siguiente paso o pregunta.

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
# SIDEBAR
# ======================
with st.sidebar:
    st.markdown("## 🌱 VitaSalud")
    st.caption("Tu coach de nutrición y ejercicio")
    st.divider()

    if st.session_state.profile is None:
        st.subheader("Completa tu perfil")

        with st.form("profile_form"):
            nombre = st.text_input("¿Cómo te llamas?", placeholder="Ej: Carlos")
            edad = st.number_input("Edad", min_value=15, max_value=90, value=35)
            peso = st.number_input("Peso actual (kg)", min_value=40.0, max_value=250.0, value=85.0, step=0.1)
            altura = st.number_input("Altura (cm)", min_value=140, max_value=220, value=170)

            objetivo = st.selectbox("Objetivo principal", [
                "Bajar de peso",
                "Mantener peso",
                "Ganar músculo",
                "Mejorar hábitos generales"
            ])

            nivel_actividad = st.selectbox("Nivel de actividad actual", [
                "Sedentario (poco o nada de ejercicio)",
                "Ligero (1-2 días por semana)",
                "Moderado (3-4 días por semana)",
                "Activo (5+ días por semana)"
            ])

            experiencia = st.selectbox("Experiencia con el ejercicio", [
                "Principiante",
                "Intermedio",
                "Avanzado"
            ])

            lugar_entrenamiento = st.selectbox("¿Dónde prefieres entrenar?", [
                "Casa",
                "Gimnasio",
                "Ambos"
            ])

            restricciones = st.multiselect(
                "Condiciones de salud / Restricciones",
                ["Ninguna", "Diabetes / prediabetes", "Hipertensión", "Sin gluten", "Sin lactosa", "Vegetariano", "Vegano"],
                default=["Ninguna"]
            )

            alergias = st.text_area(
                "Alergias o alimentos que NO comes",
                placeholder="Ej: maní, mariscos, huevo, lácteos..."
            )

            limitaciones = st.text_area(
                "Afecciones o limitaciones físicas",
                placeholder="Ej: escoliosis, problemas de cervical, rodilla operada, dolor de espalda baja..."
            )

            submitted = st.form_submit_button("Guardar perfil", use_container_width=True)

            if submitted:
                if not nombre or nombre.strip() == "":
                    st.error("Por favor escribe tu nombre.")
                else:
                    st.session_state.profile = {
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
                    st.session_state.weight_log.append({
                        "fecha": str(date.today()),
                        "peso": peso
                    })
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

# ======================
# CONTENIDO PRINCIPAL
# ======================
if st.session_state.profile is None:
    st.markdown('<div class="main-header">🌱 VitaSalud</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tu asistente personal de nutrición y ejercicio</div>', unsafe_allow_html=True)

    st.info("👈 Completa tu perfil en la barra lateral para comenzar.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🍽️ Nutrición")
        st.write("Recomendaciones personalizadas de comidas según tu objetivo.")
    with col2:
        st.markdown("### 💪 Ejercicio")
        st.write("Rutinas adaptadas a tu nivel, en casa o gimnasio.")
    with col3:
        st.markdown("### 📈 Seguimiento")
        st.write("Registra comidas, ejercicios y peso. Ve tu progreso.")

else:
    profile = st.session_state.profile
    page = st.session_state.current_page

    # ========== CHAT ==========
    if page == "Chat":
        st.markdown("### 💬 Chat con tu Coach")
        st.caption(f"Hola {profile['nombre']}, ahora estoy conectado a una IA real. ¿En qué te ayudo?")

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

    # ========== REGISTRAR COMIDA ==========
    elif page == "Comida":
        st.markdown("### 🍽️ Registrar Comida")

        with st.form("meal_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                meal_type = st.selectbox("Tipo de comida", ["Desayuno", "Almuerzo", "Cena", "Snack / Merienda"])
                meal_time = st.time_input("Hora aproximada", value=datetime.now().time())
            with col2:
                meal_date = st.date_input("Fecha", value=date.today())

            description = st.text_area("¿Qué comiste?", placeholder="Ej: 1 pechuga de pollo + ensalada + ½ taza de arroz")
            feeling = st.select_slider("¿Cómo te sentiste después?", options=["Muy mal", "Mal", "Regular", "Bien", "Muy bien"], value="Bien")

            if st.form_submit_button("Guardar comida", use_container_width=True):
                if description and description.strip():
                    st.session_state.meals.append({
                        "fecha": str(meal_date),
                        "tipo": meal_type,
                        "hora": str(meal_time)[:5],
                        "descripcion": description.strip(),
                        "sensacion": feeling
                    })
                    st.success("¡Comida registrada!")
                else:
                    st.warning("Por favor escribe qué comiste.")

        if st.session_state.meals:
            st.markdown("#### Últimas comidas registradas")
            for meal in reversed(st.session_state.meals[-5:]):
                st.markdown(f"**{meal['fecha']} · {meal['tipo']}** ({meal['hora']})")
                st.write(meal["descripcion"])
                st.caption(f"Sensación: {meal['sensacion']}")
                st.divider()

    # ========== REGISTRAR EJERCICIO ==========
    elif page == "Ejercicio":
        st.markdown("### 💪 Registrar Ejercicio")

        with st.form("exercise_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                exercise_type = st.selectbox("Tipo de ejercicio", [
                    "Caminata", "Rutina en casa", "Gimnasio", "Cardio", "Yoga / Estiramientos", "Otro"
                ])
                duration = st.number_input("Duración (minutos)", min_value=5, max_value=180, value=30)
            with col2:
                exercise_date = st.date_input("Fecha", value=date.today(), key="ex_date")
                intensity = st.select_slider("Intensidad", options=["Muy suave", "Suave", "Moderada", "Intensa", "Muy intensa"], value="Moderada")

            notes = st.text_area("Notas (opcional)", placeholder="Ej: Hice la rutina de sentadillas y plancha")

            if st.form_submit_button("Guardar ejercicio", use_container_width=True):
                st.session_state.exercises.append({
                    "fecha": str(exercise_date),
                    "tipo": exercise_type,
                    "duracion": duration,
                    "intensidad": intensity,
                    "notas": notes.strip() if notes else ""
                })
                st.success("¡Ejercicio registrado!")

        if st.session_state.exercises:
            st.markdown("#### Últimos ejercicios registrados")
            for ex in reversed(st.session_state.exercises[-5:]):
                st.markdown(f"**{ex['fecha']} · {ex['tipo']}** ({ex['duracion']} min)")
                st.write(f"Intensidad: {ex['intensidad']}")
                if ex.get("notas"):
                    st.caption(ex["notas"])
                st.divider()

    # ========== PROGRESO ==========
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
                st.session_state.weight_log.append({
                    "fecha": str(date.today()),
                    "peso": new_weight
                })
                st.session_state.profile["peso"] = new_weight
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
                for m in reversed(st.session_state.meals[-5:]):
                    st.caption(f"{m['fecha']} · {m['tipo']}: {m['descripcion'][:45]}...")
            else:
                st.caption("Aún no hay comidas registradas.")
        with col_b:
            st.write("**Últimos ejercicios:**")
            if st.session_state.exercises:
                for e in reversed(st.session_state.exercises[-5:]):
                    st.caption(f"{e['fecha']} · {e['tipo']} ({e['duracion']} min)")
            else:
                st.caption("Aún no hay ejercicios registrados.")

# ======================
# FOOTER
# ======================
st.divider()
st.caption("VitaSalud · Versión MVP · Conectado a DeepSeek AI")
st.caption("⚠️ Esta herramienta no sustituye el consejo de un médico o nutricionista profesional.")