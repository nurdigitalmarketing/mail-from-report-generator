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

    cleaned_response_content = clean_json_response(response_content)

    if not cleaned_response_content.strip():
        st.error("Errore: la risposta dell'API è vuota.")
        return None

    try:
        return json.loads(cleaned_response_content)
    except json.JSONDecodeError as e:
        st.error(f"Errore nella decodifica del JSON: {e}")
        return None

def generate_summary(client, key_info):
    summary_prompt = f"""
    Analizza i seguenti dati e genera un breve riassunto delle performance SEO:
    {json.dumps(key_info, indent=4)}
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": summary_prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=500,
        temperature=0.7,
        top_p=1.0,
        n=1,
        stop=None
    )

    return response.choices[0].message.content.strip()

def generate_email_content(client_name, contact_name, timeframe, key_info, your_name, summary):
    email_template = f"""
    <p>Ciao {contact_name},</p>

    <p>Ti invio il report relativo al progetto SEO di {client_name}, focalizzato sui risultati del canale organico.</p>

    <p>Il periodo analizzato va dall'{timeframe}, con un confronto rispetto allo stesso periodo dell'anno precedente.</p>

    <p>Di seguito troverai i dettagli dei risultati raggiunti:</p>

    <p><b>RIASSUNTO</b></p>
    <ul>
      <li>Il traffico organico è una fonte chiave di acquisizione, con un buon numero di utenti e sessioni provenienti dalla ricerca organica.</li>
      <li>Il tasso di engagement è relativamente alto, ma la durata media dell'engagement è piuttosto breve.</li>
      <li>Nonostante un buon numero di impression, i clic sono diminuiti significativamente (-21,8%), suggerendo una possibile diminuzione del CTR.</li>
      <li>La posizione media è peggiorata (-20,1%), indicando che le pagine stanno posizionandosi peggio nei risultati di ricerca.</li>
      <li>Il canale organico continua a essere il principale motore di conversioni, dimostrando l'efficacia delle nostre strategie SEO.</li>
      <li>Abbiamo visto un aumento delle impression (+0,9%), il che indica una maggiore visibilità nei risultati di ricerca.</li>
      <li>Anche se la posizione media è peggiorata, il volume complessivo di clic e sessioni mostra che gli utenti trovano ancora valore nei nostri contenuti.</li>
    </ul>

    <p><b>DATI</b></p>
    <p>I dati forniti offrono una panoramica delle performance SEO del sito web. Ecco un breve riassunto:</p>

    <p>Acquisizione</p>
    <ul>
      <li>Utenti: {format_number(key_info['acquisizione']['users'])}</li>
      <li>Sessioni: {format_number(key_info['acquisizione']['sessions'])}</li>
      <li>Paese principale: {', '.join(key_info['acquisizione']['top_countries'])}</li>
    </ul>

    <p>Engagement e Conversioni</p>
    <ul>
      <li>Tasso di engagement: {key_info['engagement_e_conversioni']['engagement_rate']}</li>
      <li>Durata media dell'engagement: {key_info['engagement_e_conversioni']['avg_engagement_duration']}</li>
      <li>Sessioni impegnate: {format_number(key_info['engagement_e_conversioni']['engaged_sessions'])}</li>
      <li>Conversioni: {format_number(key_info['engagement_e_conversioni']['conversions'])}</li>
      <li>Canale principale: {key_info['engagement_e_conversioni']['top_channel']}</li>
    </ul>

    <p>Posizionamento Organico</p>
    <ul>
      <li>Click: {format_number(key_info['posizionamento_organico']['clicks'])} (in calo del {key_info['posizionamento_organico']['clicks_change']})</li>
      <li>Impressioni: {format_number(key_info['posizionamento_organico']['impressions'])} (in aumento dello {key_info['posizionamento_organico']['impressions_change']})</li>
      <li>Posizione media: {key_info['posizionamento_organico']['avg_position']} (in calo del {key_info['posizionamento_organico']['avg_position_change']})</li>
    </ul>

    <p><b>CONCLUSIONI</b></p>
    <p>Mentre la performance di engagement e conversioni è positiva, c'è una preoccupazione per il calo nei clic e il peggioramento della posizione media. È consigliabile analizzare ulteriormente le cause di questi cali per adottare misure correttive.</p>

    <p>Troverai maggiori dettagli nel report allegato in formato PDF. Ricordo anche che è possibile accedere al <a href="https://www.report.nur.it/" target="_blank" rel="external">report online</a> in qualsiasi momento, utilizzando le credenziali fornite in allegato a questa mail.</p>

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
        st.error("Errore nell'estrazione delle informazioni chiave dal report.")
        return ""

    summary = generate_summary(client, key_info)
    email_content = generate_email_content(client_name, contact_name, timeframe, key_info, your_name, summary)

    return email_content

# UI di Streamlit
st.set_page_config(page_title="Mail from SEO PDF report generator | NUR® Digital Marketing", layout="centered")

# Blocco di descrizione
col1, col2 = st.columns([1, 7])
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

api_key = st.text_input("Inserisci la tua API key di OpenAI, [generala qui](https://platform.openai.com/api-keys).", type="password")
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
