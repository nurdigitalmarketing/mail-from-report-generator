import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken
from streamlit_quill import st_quill
import json
import re

def extract_text_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Errore durante l'estrazione del testo: {e}")
        return ""

def truncate_text(text, max_tokens):
    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return encoding.decode(tokens)

def format_number(number):
    try:
        number = float(number.replace(",", ""))
    except ValueError:
        return number
    return f"{number:,.3f}".replace(",", ".")

def clean_json_response(response_content):
    response_content = response_content.strip()
    if response_content.startswith("```json") and response_content.endswith("```"):
        response_content = response_content[7:-3].strip()
    response_content = re.sub(r'^[^\{]*', '', response_content)
    response_content = re.sub(r'[^\}]*$', '', response_content)
    return response_content

def extract_key_info_from_report(client, report_text):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""
            Analizza il seguente testo e estrai le informazioni chiave riguardanti acquisizione, engagement, conversioni e posizionamento organico.
            Fornisci i dati nel seguente formato JSON:
            {{
                "acquisizione": {{
                    "users": "numero",
                    "sessions": "numero",
                    "top_countries": ["lista", "di", "paesi"]
                }},
                "engagement_e_conversioni": {{
                    "engagement_rate": "percentuale",
                    "conversion_rate": "percentuale"
                }},
                "posizionamento_organico": {{
                    "top_keywords": ["lista", "di", "keywords"]
                }}
            }}
        """}
    ]

    try:
        response = client.Completion.create(
            engine="davinci-codex",
            prompt=json.dumps(messages),
            max_tokens=150
        )
        response_content = response.choices[0].text
        return clean_json_response(response_content)
    except Exception as e:
        st.error(f"Errore durante l'estrazione delle informazioni: {e}")
        return None

def generate_email(client, report_text, client_name, contact_name, timeframe, your_name):
    key_info = extract_key_info_from_report(client, report_text)
    if not key_info:
        return None

    email_template = f"""
    Ciao {contact_name},

    Ecco il report per il periodo {timeframe}.

    Acquisizione:
    - Utenti: {key_info['acquisizione']['users']}
    - Sessioni: {key_info['acquisizione']['sessions']}
    - Paesi principali: {", ".join(key_info['acquisizione']['top_countries'])}

    Engagement e Conversioni:
    - Tasso di engagement: {key_info['engagement_e_conversioni']['engagement_rate']}
    - Tasso di conversione: {key_info['engagement_e_conversioni']['conversion_rate']}

    Posizionamento Organico:
    - Principali keywords: {", ".join(key_info['posizionamento_organico']['top_keywords'])}

    Grazie,
    {your_name}
    """
    return email_template

# Layout
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://raw.githubusercontent.com/nurdigitalmarketing/previsione-del-traffico-futuro/9cdbf5d19d9132129474936c137bc8de1a67bd35/Nur-simbolo-1080x1080.png", width=80)
with col2:
    st.title('Mail from SEO PDF Report Generator')
    st.markdown('###### by [NUR® Digital Marketing](https://www.nur.it)')

st.markdown("""
### Introduzione
Questo strumento è stato sviluppato per generare automaticamente email a partire da report PDF, con un focus particolare sui risultati del canale organico.
### Funzionamento
Per utilizzare questo strumento, carica un file PDF del report, inserisci le informazioni richieste e genera automaticamente l'email formattata.
""")

# Usa st.secrets per accedere alla chiave API
api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=api_key)

uploaded_file = st.file_uploader("Carica il PDF del report", type="pdf")

if uploaded_file is not None:
    client_name = st.text_input("Nome del cliente")
    contact_name = st.text_input("Nome del referente")
    timeframe = st.text_input("Timeframe (es. 1 marzo 2024 - 31 maggio 2024)")
    report_type = st.selectbox("Tipologia di report", ["trimestrale", "SAR"])
    your_name = st.text_input("Il tuo nome")

    if st.button("Genera Mail"):
        if not all([client_name, contact_name, timeframe, report_type, your_name]):
            st.error("Per favore, compila tutti i campi richiesti.")
        else:
            with st.spinner("Generazione dell'email in corso..."):
                report_text = extract_text_from_pdf(uploaded_file)
                email_content = generate_email(client, report_text, client_name, contact_name, timeframe, your_name)
                if email_content:
                    st.session_state['email_content'] = email_content

if 'email_content' in st.session_state:
    quill_value = st_quill(value=st.session_state['email_content'], html=True)
