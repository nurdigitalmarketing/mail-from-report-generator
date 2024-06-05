import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken
from streamlit_quill import st_quill
import pyperclip
import json

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
    return f"{number:,}".replace(",", ".")

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
                    "engagement_rate_change": "percentuale",
                    "avg_engagement_duration": "tempo",
                    "avg_engagement_duration_change": "percentuale",
                    "engaged_sessions": "numero",
                    "engaged_sessions_change": "percentuale",
                    "conversions": "numero",
                    "conversions_change": "percentuale",
                    "top_channel": "canale"
                }},
                "posizionamento_organico": {{
                    "clicks": "numero",
                    "clicks_change": "percentuale",
                    "impressions": "numero",
                    "impressions_change": "percentuale",
                    "avg_position": "numero",
                    "avg_position_change": "percentuale"
                }}
            }}
            Testo del report:
            {report_text}
        """}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        temperature=0.7,
        top_p=1.0,
        n=1,
        stop=None
    )

    response_content = response.choices[0].message.content

    st.write(f"Response content: {response_content}")  # Debug: Verifica il contenuto della risposta

    if not response_content.strip():
        st.error("Errore: la risposta dell'API è vuota.")
        return {}

    try:
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        st.error(f"Errore nella decodifica del JSON: {e}")
        return {}

def generate_email_content(client_name, contact_name, timeframe, key_info, your_name):
    email_template = f"""
    <p>Ciao {contact_name},</p>
    <p>Ti invio il report relativo al progetto SEO di {client_name}, focalizzandosi sui risultati del canale organico.</p>
    <p>Il periodo analizzato va dall'{timeframe}, con un confronto rispetto allo stesso periodo dell'anno precedente.</p>
    <p>Di seguito troverai i dettagli dei risultati raggiunti:</p>

    <p><strong>Attività svolte in questo periodo:</strong></p>
    <ul>
        <li>Miglioramento dei contenuti su diverse pagine chiave</li>
        <li>Aggiunta di link interni a pagine chiave</li>
        <li>Costruzione di nuovi backlink (vedi report sui link)</li>
    </ul>

    <p><strong>Risultati raggiunti:</strong></p>
    <p><strong>[Acquisizione]</strong></p>
    <ul>
        <li>Utenti: {format_number(key_info['acquisizione']['users'])}</li>
        <li>Sessioni: {format_number(key_info['acquisizione']['sessions'])}</li>
        <li>Paesi con maggiore acquisizione di utenti: {', '.join(key_info['acquisizione']['top_countries'])}</li>
    </ul>

    <p><strong>[Engagement e Conversioni]</strong></p>
    <ul>
        <li>Tasso di coinvolgimento: {key_info['engagement_e_conversioni']['engagement_rate']} con un {"incremento" if '-' not in key_info['engagement_e_conversioni']['engagement_rate_change'] else "decremento"} del {key_info['engagement_e_conversioni']['engagement_rate_change']}</li>
        <li>Durata media del coinvolgimento: {key_info['engagement_e_conversioni']['avg_engagement_duration']} con un {"incremento" if '-' not in key_info['engagement_e_conversioni']['avg_engagement_duration_change'] else "decremento"} del {key_info['engagement_e_conversioni']['avg_engagement_duration_change']}</li>
        <li>Sessioni con coinvolgimento: {format_number(key_info['engagement_e_conversioni']['engaged_sessions'])} con un {"incremento" if '-' not in key_info['engagement_e_conversioni']['engaged_sessions_change'] else "decremento"} del {key_info['engagement_e_conversioni']['engaged_sessions_change']}</li>
        <li>Conversioni: {format_number(key_info['engagement_e_conversioni']['conversions'])} con un {"incremento" if '-' not in key_info['engagement_e_conversioni']['conversions_change'] else "decremento"} del {key_info['engagement_e_conversioni']['conversions_change']}</li>
        <li>Canale che porta maggiori conversioni: {key_info['engagement_e_conversioni']['top_channel']}</li>
    </ul>

    <p><strong>[Search Console]</strong></p>
    <ul>
        <li>Clic: {format_number(key_info['posizionamento_organico']['clicks'])} con un {"incremento" if '-' not in key_info['posizionamento_organico']['clicks_change'] else "decremento"} del {key_info['posizionamento_organico']['clicks_change']}</li>
        <li>Impression: {format_number(key_info['posizionamento_organico']['impressions'])} con un {"incremento" if '-' not in key_info['posizionamento_organico']['impressions_change'] else "decremento"} del {key_info['posizionamento_organico']['impressions_change']}</li>
        <li>Posizione media: {key_info['posizionamento_organico']['avg_position']} con un {"incremento" if '-' not in key_info['posizionamento_organico']['avg_position_change'] else "decremento"} del {key_info['posizionamento_organico']['avg_position_change']}</li>
    </ul>

    <p>Troverai maggiori dettagli nel report allegato in formato PDF. Ricordo anche che è possibile accedere al report online in qualsiasi momento, utilizzando le credenziali fornite in allegato a questa mail.</p>

    <p>Fammi sapere se ti servisse altro.</p>

    <p>A presto,</p>
    <p><strong>{your_name}</strong></p>
    """
    return email_template

def generate_email(client, report_text, client_name, contact_name, timeframe, your_name):
    max_input_tokens = 126000  # Set according to the context window of the model
    truncated_report_text = truncate_text(report_text, max_input_tokens)

    key_info = extract_key_info_from_report(client, truncated_report_text)
    
    if not key_info:
        return ""

    email_content = generate_email_content(client_name, contact_name, timeframe, key_info, your_name)

    return email_content

st.set_page_config(page_title="Mail Generator from SEO PDF Reports | NUR® Digital Marketing", layout="centered")

# Blocco di descrizione
col1, col2 = st.columns([1, 7])
with col1:
    st.image("https://raw.githubusercontent.com/nurdigitalmarketing/previsione-del-traffico-futuro/9cdbf5d19d9132129474936c137bc8de1a67bd35/Nur-simbolo-1080x1080.png", width=80)
with col2:
    st.title('Mail Generator from SEO PDF Reports')
    st.markdown('###### by [NUR® Digital Marketing](https://www.nur.it)')

st.markdown("""
## Introduzione
Questo strumento è stato sviluppato per generare automaticamente email a partire da report PDF, con un focus particolare sui risultati del canale organico.
## Funzionamento
Per utilizzare questo strumento, carica un file PDF del report, inserisci le informazioni richieste e genera automaticamente l'email formattata.
""")

api_key = st.text_input("Inserisci la tua API key di OpenAI", type="password")
if api_key:
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
    if st.button("Copia email"):
        pyperclip.copy(quill_value)
        st.success("Email copiata negli appunti!")
