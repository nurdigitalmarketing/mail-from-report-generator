import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken
import re

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_data_from_text(text):
    sessioni_pattern = re.compile(r'Sessioni con coinvolgimento\s+([\d,]+)')
    conversioni_pattern = re.compile(r'Conversioni\s+([\d,]+)')
    
    sessioni_match = sessioni_pattern.search(text)
    conversioni_match = conversioni_pattern.search(text)
    
    sessioni = sessioni_match.group(1) if sessioni_match else "N/A"
    conversioni = conversioni_match.group(1) if conversioni_match else "N/A"
    
    return sessioni, conversioni

def truncate_text(text, max_tokens):
    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return encoding.decode(tokens)

def generate_email(client, report_text, client_name, contact_name, timeframe, report_type, your_name):
    max_input_tokens = 6000  # Set according to the context window of the model
    truncated_report_text = truncate_text(report_text, max_input_tokens)
    
    sessioni, conversioni = extract_data_from_text(report_text)

    summary_prompt = f"""
    Riassumi i risultati del report per il cliente {client_name} (referente: {contact_name}) riguardante il report {report_type} per il periodo {timeframe}.
    Il riassunto dovrebbe concentrarsi sui risultati positivi e essere breve.
    Ecco il testo del report:

    {truncated_report_text}
    """

    summary_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": summary_prompt}],
        max_tokens=500,
        temperature=0.7,
        top_p=1.0,
        n=1,
        stop=None
    )

    summary = summary_response.choices[0].message["content"] if summary_response and summary_response.choices and summary_response.choices[0].message and "content" in summary_response.choices[0].message else "Riassunto non disponibile."

    email_content = f"""
    <p>Ciao {contact_name},</p>
    <p>Ti invio il report relativo al progetto SEO di {client_name}, focalizzandosi sui risultati del canale organico.</p>
    <p>Il periodo analizzato va dall'{timeframe}, con un confronto rispetto allo stesso periodo dell'anno precedente.</p>
    <p>Di seguito troverai un breve riassunto dei risultati raggiunti:</p>
    <p>{summary}</p>
    <p>Di seguito troverai i dettagli dei risultati raggiunti:</p>
    <p>&nbsp;</p>
    <p>Risultati raggiunti:</p>
    <p>[Acquisizione]</p>
    <ul>
    <li>Utenti: 88.72</li>
    <li>Sessioni: 133.08</li>
    <li>Paesi con maggiore acquisizione di utenti: Lombardia, Lazio e Veneto</li>
    </ul>
    <p>&nbsp;</p>
    <p>[Engagement e Conversioni]</p>
    <ul>
    <li>Tasso di coinvolgimento: 65,62%</li>
    <li>Durata media del coinvolgimento: 00:01:47</li>
    <li>Sessioni con coinvolgimento: {sessioni}</li>
    <li>Conversioni: {conversioni}</li>
    <li>Canale che porta maggiori conversioni: Organic Search</li>
    </ul>
    <p>&nbsp;</p>
    <p>[Search Console]</p>
    <ul>
    <li>Clic: 61.57 con un decremento del -21.8%</li>
    <li>Impression: 3.546.337 con un incremento del 0.9%</li>
    <li>Posizione media: 18,04 con un decremento del -20.1%</li>
    </ul>
    <p>&nbsp;</p>
    <p>Troverai maggiori dettagli nel report allegato in formato PDF. Ricordo anche che &egrave; possibile accedere al report online in qualsiasi momento, utilizzando le credenziali fornite in allegato a questa mail.</p>
    <p>&nbsp;</p>
    <p>Fammi sapere se ti servisse altro.</p>
    <p>&nbsp;</p>
    <p>A presto,</p>
    <p>{your_name}</p>
    """

    return email_content

# UI di Streamlit
st.title("Generatore di Mail da Report PDF")

api_key = st.text_input("Inserisci la tua API key di OpenAI", type="password")
if api_key:
    client = OpenAI(api_key=api_key)

    uploaded_file = st.file_uploader("Carica il PDF del report", type="pdf")

    if uploaded_file is not None:
        client_name = st.text_input("Nome del cliente")
        contact_name = st.text_input("Nome del referente")
        timeframe = st.text_input("Timeframe (es. 1 marzo 2024 - 31 maggio 2024)")
        report_type = st.selectbox("Tipologia di report", ["trimestrale", "SAR", "year review"])
        your_name = st.text_input("Il tuo nome")

        if st.button("Genera Mail"):
            report_text = extract_text_from_pdf(uploaded_file)
            email_content = generate_email(client, report_text, client_name, contact_name, timeframe, report_type, your_name)
            st.text_area("Email generata", email_content, height=400)

            st.download_button("Scarica la mail", email_content)

