import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken
from streamlit_quill import st_quill

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

def generate_email_content(client_name, contact_name, timeframe, report_type, key_info, your_name):
    email_template = f"""
    <p>Ciao {contact_name},</p>
    <p>&nbsp;</p>
    <p>Scrivo per condividerti il report {report_type} per progetto SEO di {client_name}, con un focus particolare sui risultati del canale organico.</p>
    <p>Il periodo analizzato va dall'{timeframe} e confrontato con lo stesso periodo dell'anno precedente.</p>
    <p>&nbsp;</p>
    <p><strong>[ACQUISIZIONE]</strong></p>
    {key_info['acquisizione']}
    <p>&nbsp;</p>
    <p><strong>[ENGAGEMENT E CONVERSIONI]</strong></p>
    {key_info['engagement_e_conversioni']}
    <p>&nbsp;</p>
    <p><strong>[POSIZIONAMENTO ORGANICO]</strong></p>
    {key_info['posizionamento_organico']}
    <p>&nbsp;</p>
    <p>Troverai maggiori dettagli nel report allegato in formato PDF. Ricordo anche che &egrave; possibile accedere al <a href="https://www.report.nur.it/" target="_blank" rel="noopener noreferrer">report online</a> in qualsiasi momento, utilizzando le credenziali fornite in allegato a questa mail.</p>
    <p>Rimango a disposizione per qualsiasi chiarimento.</p>
    <p>&nbsp;</p>
    <p>A presto,</p>
    <p><strong>{your_name}</strong></p>
    """
    return email_template

def generate_email(client, report_text, client_name, contact_name, timeframe, report_type, your_name):
    max_input_tokens = 126000  # Set according to the context window of the model
    truncated_report_text = truncate_text(report_text, max_input_tokens)

    key_info_text = extract_key_info_from_report(client, truncated_report_text)
    # Simula la conversione del testo chiave in un dizionario strutturato
    key_info = {
        "acquisizione": "<p>Abbiamo registrato un incremento del traffico organico del <span style='color: green; font-weight: bold;'>+17,3%</span>, confermando che il canale organico è la principale fonte di acquisizione. Questo miglioramento evidenzia l'efficacia delle nostre strategie SEO nell'attrarre utenti qualificati.</p>",
        "engagement_e_conversioni": "<p>Per quanto riguarda l'engagement, i risultati sono molto positivi filtrando per traffico organico. La durata media del coinvolgimento è aumentata dell'<span style='color: green; font-weight: bold;'>+11,7%</span>, raggiungendo i 2 minuti e 55 secondi. Le sessioni con coinvolgimento sono aumentate del <span style='color: green; font-weight: bold;'>+15,4%</span>, totalizzando 35.682 sessioni, mentre il tasso di coinvolgimento ha mostrato un leggero incremento dello <span style='color: green; font-weight: bold;'>+0,5%</span>, attestandosi al 67,46%. Inoltre, le visualizzazioni totali sono cresciute del <span style='color: green; font-weight: bold;'>+15,7%</span>, raggiungendo 198.458. Questi dati indicano che gli utenti provenienti dalla ricerca organica sono maggiormente coinvolti e interagiscono più a lungo con i contenuti del sito.</p><p>Per quanto riguarda le conversioni, la maggior parte proviene dal traffico organico, con un totale di <span style='color: green; font-weight: bold;'>3.720 conversioni</span>, sottolineando l'importanza di questo canale nel generare azioni concrete da parte degli utenti.</p>",
        "posizionamento_organico": "<p>Su Google Search Console, abbiamo registrato un calo dei clic del <span style='color: red; font-weight: bold;'>-13,0%</span> e delle impression del <span style='color: red; font-weight: bold;'>-0,9%</span>. Queste flessioni negative sono dovute agli aggiornamenti di marzo rilasciati da Google. Stiamo monitorando attentamente la situazione per adattare le nostre strategie di conseguenza. È importante notare che la posizione media è migliorata, scendendo del <span style='color: green; font-weight: bold;'>-13,6%</span>. Questo è un aspetto positivo, in quanto indica una maggiore presenza nelle pagine superiori dei risultati di ricerca.</p>"
    }
    email_content = generate_email_content(client_name, contact_name, timeframe, report_type, key_info, your_name)

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
            if not all([client_name, contact_name, timeframe, report_type, your_name]):
                st.error("Per favore, compila tutti i campi richiesti.")
            else:
                with st.spinner("Generazione dell'email in corso..."):
                    report_text = extract_text_from_pdf(uploaded_file)
                    email_content = generate_email(client, report_text, client_name, contact_name, timeframe, report_type, your_name)
                    st.session_state['email_content'] = email_content

if 'email_content' in st.session_state:
    quill_value = st_quill(value=st.session_state['email_content'], html=True)
    st.download_button("Scarica la mail", quill_value, file_name='email.html')
