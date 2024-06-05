import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken
from streamlit_quill import st_quill
import pyperclip

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

def extract_key_info_from_report(client, report_text):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""
            Analizza il seguente testo e estrai le informazioni chiave riguardanti acquisizione, engagement, conversioni e posizionamento organico.
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

    return response.choices[0].message.content

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
        <li>Utenti: {key_info['acquisizione']['users']}</li>
        <li>Sessioni: {key_info['acquisizione']['sessions']}</li>
        <li>Paesi con maggiore acquisizione di utenti: {key_info['acquisizione']['top_countries']}</li>
    </ul>

    <p><strong>[Engagement e Conversioni]</strong></p>
    <ul>
        <li>Tasso di coinvolgimento: {key_info['engagement_e_conversioni']['engagement_rate']}%</li>
        <li>Durata media del coinvolgimento: {key_info['engagement_e_conversioni']['avg_engagement_duration']}</li>
        <li>Sessioni con coinvolgimento: {key_info['engagement_e_conversioni']['engaged_sessions']}</li>
        <li>Conversioni: {key_info['engagement_e_conversioni']['conversions']}</li>
        <li>Canale che porta maggiori conversioni: {key_info['engagement_e_conversioni']['top_channel']}</li>
    </ul>

    <p><strong>[Search Console]</strong></p>
    <ul>
        <li>Clic: {key_info['posizionamento_organico']['clicks']}</li>
        <li>Impression: {key_info['posizionamento_organico']['impressions']}</li>
        <li>Posizione media: {key_info['posizionamento_organico']['avg_position']}</li>
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

    key_info_text = extract_key_info_from_report(client, truncated_report_text)
    # Simula la conversione del testo chiave in un dizionario strutturato
    key_info = {
        "acquisizione": {
            "users": "12345",  # Questo è un esempio, sostituisci con il valore reale
            "sessions": "67890",
            "top_countries": "Italia, USA, UK"
        },
        "engagement_e_conversioni": {
            "engagement_rate": "67.46",
            "avg_engagement_duration": "2 min 55 sec",
            "engaged_sessions": "35,682",
            "conversions": "3,720",
            "top_channel": "Ricerca organica"
        },
        "posizionamento_organico": {
            "clicks": "-13.0%",
            "impressions": "-0.9%",
            "avg_position": "-13.6%"
        }
    }
    email_content = generate_email_content(client_name, contact_name, timeframe, key_info, your_name)

    return email_content

# UI di Streamlit
st.title("Generatore di Mail da Report PDF")

# Blocco di descrizione
col1, col2 = st.columns([1, 7])
with col1:
    st.image("https://raw.githubusercontent.com/nurdigitalmarketing/previsione-del-traffico-futuro/9cdbf5d19d9132129474936c137bc8de1a67bd35/Nur-simbolo-1080x1080.png", width=80)
with col2:
    st.title('Generatore di Mail da Report PDF')
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
                    st.session_state['email_content'] = email_content

if 'email_content' in st.session_state:
    quill_value = st_quill(value=st.session_state['email_content'], html=True)
    if st.button("Copia email"):
        pyperclip.copy(quill_value)
        st.success("Email copiata negli appunti!")
