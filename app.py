
import json
import os
import streamlit as st

from PIL import Image
from bokeh.models import CustomJS
from bokeh.models.widgets import Button
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Voice Control | Panel de voz",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "voice_ctrl"


# =========================================================
# ESTILOS VISUALES
# =========================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top left, #172554 0%, transparent 40%),
        #080d19;
    color: #f8fafc;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background: #0c1322;
    border-right: 1px solid #1e293b;
}

section[data-testid="stSidebar"] * {
    color: #dbeafe;
}

/* ENCABEZADO */

.etiqueta {
    display: inline-block;
    padding: 7px 13px;
    border: 1px solid #1d4ed8;
    border-radius: 30px;
    background: #172554;
    color: #93c5fd;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
}

.hero {
    padding: 25px 0 20px 0;
}

.hero h1 {
    color: #f8fafc;
    font-size: clamp(32px, 5vw, 52px);
    font-weight: 850;
    letter-spacing: -1.5px;
    line-height: 1.15;
    margin: 18px 0 12px 0;
}

.hero h1 span {
    color: #60a5fa;
}

.hero p {
    color: #94a3b8;
    font-size: 17px;
    line-height: 1.7;
    max-width: 720px;
}

/* TARJETAS */

.panel {
    background: linear-gradient(145deg, #131e32, #0e1728);
    border: 1px solid #26364d;
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.16);
}

.panel h3 {
    color: #f8fafc;
    font-size: 20px;
    margin-top: 0;
    margin-bottom: 10px;
}

.panel p {
    color: #94a3b8;
    line-height: 1.65;
    font-size: 14px;
}

.icono {
    font-size: 35px;
    margin-bottom: 12px;
}

.seccion {
    font-size: 24px;
    font-weight: 750;
    color: #f8fafc;
    margin: 20px 0;
}

.tag {
    display: inline-block;
    border-radius: 8px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 700;
    color: #93c5fd;
    background: #172554;
    border: 1px solid #1e40af;
}

/* TEXTO RECONOCIDO */

.comando {
    background: #0b1424;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px;
    min-height: 105px;
    color: #e2e8f0;
    font-size: 17px;
    line-height: 1.6;
    overflow-wrap: anywhere;
}

/* BOTONES STREAMLIT */

.stButton > button {
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    color: white;
    border: 1px solid #60a5fa;
    border-radius: 12px;
    font-weight: 700;
    min-height: 45px;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #1d4ed8;
    color: white;
    border-color: #93c5fd;
}

/* INFORMACIÓN */

.info {
    background: #101c30;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 15px 18px;
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.7;
}

.footer {
    text-align: center;
    border-top: 1px solid #1e293b;
    padding-top: 25px;
    margin-top: 40px;
    color: #64748b;
    font-size: 13px;
}

div[data-testid="stImage"] img {
    border-radius: 14px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🎙️ Voice Control")
    st.caption("INTERFACES MULTIMODALES")

    st.markdown("---")

    st.markdown("### ¿Cómo funciona?")

    st.write(
        "Habla a través del micrófono, convierte tus instrucciones "
        "en texto y envíalas mediante MQTT a otro sistema."
    )

    st.markdown("---")

    st.markdown("### 🧩 Componentes")

    st.write("🎤 Reconocimiento de voz")
    st.write("🌐 Interfaz web")
    st.write("📡 Comunicación MQTT")
    st.write("⚙️ Sistema receptor")

    st.markdown("---")

    st.markdown("### 📡 Conexión")

    st.code(
        f"Broker: {BROKER}\n"
        f"Puerto: {PORT}\n"
        f"Tópico: {TOPIC}",
        language="text"
    )

    st.caption(
        "Proyecto académico · Diseño Interactivo"
    )


# =========================================================
# ENCABEZADO PRINCIPAL
# =========================================================

st.markdown("""
<div class="hero">
    <span class="etiqueta">VOICE INTERFACE / 01</span>
    <h1>Controla con tu <span>voz.</span></h1>
    <p>
        Una interfaz de interacción por voz que transforma tus palabras
        en mensajes digitales y los transmite a través de una conexión MQTT.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# ESTADO DE LA APLICACIÓN
# =========================================================

if "ultimo_comando" not in st.session_state:
    st.session_state.ultimo_comando = ""

if "ultimo_payload" not in st.session_state:
    st.session_state.ultimo_payload = ""

if "estado_envio" not in st.session_state:
    st.session_state.estado_envio = "Esperando instrucciones"


# =========================================================
# PANEL PRINCIPAL
# =========================================================

col_control, col_info = st.columns([1.35, 1], gap="large")

with col_control:

    st.markdown("""
    <div class="panel">
        <div class="icono">🎤</div>
        <span class="tag">ENTRADA DE VOZ</span>
        <h3 style="margin-top:15px;">Centro de control</h3>
        <p>
            Pulsa el botón de inicio y habla con claridad.
            Tu navegador reconocerá las palabras y las mostrará en pantalla.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Botón de reconocimiento de voz
    stt_button = Button(
        label="🎙️ Iniciar reconocimiento",
        width=320,
        height=55,
        button_type="primary"
    )

    stt_button.js_on_event(
        "button_click",
        CustomJS(code="""
            if (!('webkitSpeechRecognition' in window) &&
                !('SpeechRecognition' in window)) {
                document.dispatchEvent(
                    new CustomEvent("GET_TEXT", {
                        detail: "ERROR: Este navegador no admite reconocimiento de voz."
                    })
                );
            } else {
                var SpeechRecognition =
                    window.SpeechRecognition ||
                    window.webkitSpeechRecognition;

                var recognition = new SpeechRecognition();

                recognition.lang = 'es-CO';
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;

                recognition.onresult = function(event) {
                    var value =
                        event.results[0][0].transcript.trim();

                    document.dispatchEvent(
                        new CustomEvent("GET_TEXT", {
                            detail: value
                        })
                    );
                };

                recognition.onerror = function(event) {
                    document.dispatchEvent(
                        new CustomEvent("GET_TEXT", {
                            detail: "ERROR: " + event.error
                        })
                    );
                };

                recognition.start();
            }
        """)
    )

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="voice_listener",
        refresh_on_update=True,
        override_height=75,
        debounce_time=0
    )

    # Procesar la voz reconocida
    if result and "GET_TEXT" in result:

        texto = str(result["GET_TEXT"]).strip()

        if texto.startswith("ERROR:"):
            st.session_state.estado_envio = texto

        elif texto:

            st.session_state.ultimo_comando = texto

            payload = json.dumps(
                {"Act1": texto},
                ensure_ascii=False
            )

            st.session_state.ultimo_payload = payload

            try:
                client = paho.Client(
                    client_id="GIT-HUBC"
                )

                client.connect(BROKER, PORT, 60)

                info_mensaje = client.publish(
                    TOPIC,
                    payload,
                    qos=0
                )

                info_mensaje.wait_for_publish(
                    timeout=5
                )

                if info_mensaje.is_published():
                    st.session_state.estado_envio = (
                        "Mensaje publicado en MQTT."
                    )
                else:
                    st.session_state.estado_envio = (
                        "El envío no pudo confirmarse."
                    )

                client.disconnect()

            except Exception as e:
                st.session_state.estado_envio = (
                    f"Error de conexión: {e}"
                )

    st.markdown(
        '<div class="seccion">📝 Última instrucción</div>',
        unsafe_allow_html=True
    )

    comando = st.session_state.ultimo_comando

    if comando:
        st.markdown(
            f'<div class="comando">{comando}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="comando">'
            'Tu instrucción aparecerá aquí cuando hables...'
            '</div>',
            unsafe_allow_html=True
        )

    if st.button("🗑️ Limpiar instrucción", use_container_width=True):
        st.session_state.ultimo_comando = ""
        st.session_state.ultimo_payload = ""
        st.session_state.estado_envio = "Esperando instrucciones"
        st.rerun()


with col_info:

    st.markdown("""
    <div class="panel">
        <div class="icono">📡</div>
        <span class="tag">SALIDA DE DATOS</span>
        <h3 style="margin-top:15px;">Transmisión MQTT</h3>
        <p>
            El comando reconocido se organiza en formato JSON y se publica
            en el tópico configurado para que otro dispositivo o programa
            pueda recibirlo.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="seccion">📶 Estado del envío</div>',
        unsafe_allow_html=True
    )

    estado = st.session_state.estado_envio

    if estado == "Mensaje publicado en MQTT.":
        st.success(estado)
    elif estado.startswith("Error"):
        st.error(estado)
    elif estado.startswith("ERROR:"):
        st.warning(estado)
    elif estado == "El envío no pudo confirmarse.":
        st.warning(estado)
    else:
        st.info(estado)

    st.markdown("""
    <div class="info">
        <b>Flujo de información</b><br>
        01. Habla al micrófono.<br>
        02. El navegador reconoce la instrucción.<br>
        03. Python prepara el mensaje JSON.<br>
        04. MQTT publica el mensaje en el tópico de destino.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="seccion">📦 Mensaje JSON</div>',
        unsafe_allow_html=True
    )

    if st.session_state.ultimo_payload:
        st.code(
            st.session_state.ultimo_payload,
            language="json"
        )
    else:
        st.code(
            '{"Act1": "Tu instrucción aparecerá aquí"}',
            language="json"
        )


# =========================================================
# IMAGEN DEL PROYECTO
# =========================================================

st.markdown("---")

col_img, col_texto = st.columns([1, 2], gap="large")

with col_img:
    if os.path.exists("voice_ctrl.jpg"):
        imagen = Image.open("voice_ctrl.jpg")
        st.image(
            imagen,
            use_container_width=True
        )
    else:
        st.markdown("""
        <div class="panel" style="text-align:center;">
            <div style="font-size:60px;">🗣️</div>
            <p>Interacción por voz</p>
        </div>
        """, unsafe_allow_html=True)

with col_texto:
    st.markdown(
        '<div class="seccion">Sobre el proyecto</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Voice Control explora las interfaces multimodales y la "
        "interacción entre personas y sistemas digitales. Combina "
        "reconocimiento de voz, procesamiento de texto y comunicación "
        "mediante mensajería MQTT."
    )

    st.write(
        "La aplicación publica instrucciones, pero para que estas "
        "produzcan acciones físicas o digitales debe existir un "
        "dispositivo o programa receptor configurado para interpretarlas."
    )


# =========================================================
# PIE DE PÁGINA
# =========================================================

st.markdown("""
<div class="footer">
    <b>VOICE CONTROL</b><br><br>
    Interfaces multimodales · Diseño Interactivo<br>
    Explorando nuevas formas de interacción entre personas y tecnología.
</div>
""", unsafe_allow_html=True)
