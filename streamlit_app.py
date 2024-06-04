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
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Report SEO {client_name}</title>
        <style>
            .increment {{
                color: green;
                font-weight: bold;
            }}
            .decrement {{
                color: red;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <p>Ciao {contact_name},</p>
        <p>Ti invio il report {report_type} relativo al progetto SEO di {client_name}, focalizzandosi sui risultati del canale organico.</p>
        <p>Il periodo analizzato va dall'{timeframe}, con un confronto rispetto allo stesso periodo dell'anno precedente.</p>
        
        <h3>Acquisizione</h3>
        {key_info['acquisizione']}
        
        <h3>Engagement e Conversioni</h3>
        {key_info['engagement_e_conversioni']}
        
        <h3>Posizionamento Organico</h3>
        {key_info['posizionamento_organico']}
        
        <p>Continueremo a puntare su contenuti di qualità e ottimizzazione on-page per rafforzare la presenza organica del sito.</p>
        
        <p>Troverai maggiori dettagli nel report allegato in formato PDF. Ricordo anche che è possibile accedere al report online in qualsiasi momento, utilizzando le credenziali fornite in allegato a questa mail.</p>
        
        <p>Resto a disposizione per qualsiasi ulteriore informazione.</p>
        
        <p>Cordiali saluti,<br>{your_name}</p>
    </body>
    </html>
    """
    return email_template

def generate_email(client, report_text, client_name, contact_name, timeframe, report_type, your_name):
    max_input_tokens = 126000  # Set according to the context window of the model
    truncated_report_text = truncate_text(report_text, max_input_tokens)

    key_info_text = extract_key_info_from_report(client, truncated_report_text)
    # Simula la conversione del testo chiave in un dizionario strutturato
    key_info = {
        "acquisizione": "<p>Abbiamo registrato un incremento del traffico organico del <span class='increment'>+204,8%</span>, confermando che il canale organico è la principale fonte di acquisizione. Questo miglioramento evidenzia l'efficacia delle nostre strategie SEO nell'attrarre utenti qualificati.</p>",
        "engagement_e_conversioni": "<p>Per quanto riguarda l'engagement, i risultati sono molto positivi. La durata media del coinvolgimento è aumentata dell'<span class='increment'>+11,4%</span>, raggiungendo 1 minuto e 30 secondi. Le sessioni con coinvolgimento sono cresciute del <span class='increment'>+206,3%</span>, totalizzando 259.822 sessioni, e il tasso di coinvolgimento è salito del <span class='increment'>+6,5%</span>, attestandosi al 71,72%. Inoltre, le visualizzazioni totali sono aumentate del <span class='increment'>+166,8%</span>, raggiungendo 435.972. Questi dati indicano che gli utenti provenienti dalla ricerca organica sono maggiormente coinvolti e interagiscono più a lungo con i contenuti del sito.</p><p>Per quanto riguarda le conversioni, la maggior parte proviene dal traffico organico, con un totale di <span class='increment'>6.700 conversioni</span>, sottolineando l'importanza di questo canale nel generare azioni concrete da parte degli utenti.</p>",
        "posizionamento_organico": "<p>Su Google Search Console, abbiamo registrato un aumento dei clic del <span class='increment'>+494,6%</span> e delle impression del <span class='increment'>+521,2%</span>. Questo riflette un significativo miglioramento nella visibilità e nel rendimento del sito nei risultati di ricerca. È importante notare che la posizione media è migliorata, scendendo del <span class='increment'>-20,1%</span> (valore in verde), indicando una maggiore presenza nelle prime pagine dei risultati di ricerca.</p>"
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
                    quill_value = st_quill(value=email_content, html=True)
                    st.download_button("Scarica la mail", quill_value, file_name='email.html')
