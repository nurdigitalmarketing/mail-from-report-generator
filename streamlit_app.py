import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken

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

def generate_email(client, report_text, client_name, contact_name, timeframe, report_type, your_name):
    max_input_tokens = 126000  # Set according to the context window of the model
    truncated_report_text = truncate_text(report_text, max_input_tokens)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""
            Crea una mail per il cliente {client_name} (referente: {contact_name}) riguardante il report {report_type} per il periodo {timeframe}.
            Ecco il testo del report:
            
            {truncated_report_text}
            
            Utilizza il seguente template:
            
            Ciao {contact_name},
            
            Scrivo per condividerti il report {report_type} per progetto SEO di RIVA 1920, con un focus particolare sui risultati del canale organico.
            
            Il periodo analizzato va dall'{timeframe} e confrontato con lo stesso periodo dell'anno precedente.
            
            [ACQUISIZIONE]
            Abbiamo registrato un incremento del traffico organico del +17,3%, confermando il canale organico come una delle principali fonti di acquisizione. Questo miglioramento riflette l'efficacia delle nostre strategie SEO nell'attrarre utenti qualificati.
            
            [ENGAGEMENT E CONVERSIONI]
            Per quanto riguarda l'engagement, abbiamo osservato risultati molto positivi filtrando per traffico organico. La durata media del coinvolgimento è aumentata dell'11,7%, raggiungendo i 2 minuti e 55 secondi. Le sessioni con coinvolgimento sono aumentate del 15,4%, totalizzando 35.682 sessioni, mentre il tasso di coinvolgimento ha mostrato un leggero incremento dello 0,5%, attestandosi al 67,46%. Inoltre, le visualizzazioni totali sono cresciute del 15,7%, raggiungendo 198.458. Questi dati indicano che gli utenti provenienti dalla ricerca organica sono maggiormente coinvolti e interagiscono più a lungo con i contenuti del sito.
            
            Per quanto riguarda le conversioni, la maggior parte di esse proviene dal traffico organico, con un totale di 3.720 conversioni, evidenziando l'importanza del canale organico nel generare azioni concrete da parte degli utenti.
            
            [POSIZIONAMENTO ORGANICO]
            Su Google Search Console, abbiamo registrato un calo dei clic del -13,0% e delle impression del -0,9%. Queste flessioni negative sono dovute agli aggiornamenti di marzo rilasciati da Google. Stiamo monitorando attentamente la situazione per adattare le nostre strategie di conseguenza. È importante notare che la posizione media è migliorata, scendendo del -13,6%. Questo è un aspetto positivo, in quanto indica una maggiore presenza nelle pagine superiori dei risultati di ricerca.
            
            Continueremo a puntare su contenuti di qualità e ottimizzazione on-page per rafforzare la presenza a seguito degli aggiornamenti.
            
            Troverai maggiori dettagli nel report allegato in formato PDF. Ricordo anche che è possibile accedere al report online in qualsiasi momento, utilizzando le credenziali fornite in allegato a questa mail.
            
            Fammi sapere se ti servisse altro.
            
            A presto,
            
            {your_name}
        """}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
            top_p=1.0,
            n=1,
            stop=None
        )
        return response.choices[0].message["content"]
    except Exception as e:
        st.error(f"Errore durante la generazione della mail: {e}")
        return ""

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
                    st.text_area("Email generata", email_content, height=400)
                    st.download_button("Scarica la mail", email_content)
