import streamlit as st
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import io
import pdfplumber

# ==========================================
# 1. CONFIGURAZIONE DEI TURNI
# ==========================================
orari_turni = {
    'M': {'nome': 'Mattina', 'inizio': '07:30', 'fine': '13:12'},
    'P': {'nome': 'Pomeriggio', 'inizio': '14:18', 'fine': '20:00'}, 
    'G': {'nome': 'Giornata', 'inizio': '08:00', 'fine': '13:42'}, 
    'G1': {'nome': 'Giornata 1', 'inizio': '08:30', 'fine': '14:12'}, 
    'G2': {'nome': 'Giornata 2', 'inizio': '09:00', 'fine': '14:42'},
    'G3': {'nome': 'Giornata 3', 'inizio': '10:48', 'fine': '18:30'},
    'Pr': {'nome': 'Permesso', 'tutto_giorno': True}, # Turno speciale
    'R':  None 
}

# ==========================================
# 2. FUNZIONI
# ==========================================
def estrai_turni_da_pdf(file_pdf, nome_utente):
    turni_trovati = []
    nome_utente = nome_utente.lower().strip()
    
    with pdfplumber.open(file_pdf) as pdf:
        for page in pdf.pages:
            # Estrae la tabella dalla pagina
            table = page.extract_table()
            if not table:
                continue
            
            for row in table:
                # Pulizia della riga per il confronto (rimuove None e spazi)
                row_cleaned = [str(cell).strip() if cell else "" for cell in row]
                
                # Cerchiamo se il nome dell'utente è in questa riga (solitamente prima colonna)
                if any(nome_utente in cell.lower() for cell in row_cleaned):
                    # Supponendo che i turni inizino dopo il nome (es. dalla colonna 1 in poi)
                    # Adatta l'indice [1:] in base a quante colonne di "intestazione" ci sono
                    turni_trovati = row_cleaned[1:] 
                    return turni_trovati # Trovato, usciamo
    return None

    # Simuliamo un mese di turni casuali per testare l'app
    #return ['R', 'R', 'R', 'G', 'G', 'G', 'Pr'] # R = Riposo, Pr = Permesso

def crea_file_ical(lista_turni, anno, mese):
    """Prende la lista di lettere e genera il contenuto del file .ics"""
    cal = Calendar()
    cal.add('prodid', '-//Turni Web App//')
    cal.add('version', '1.0')
    tz = pytz.timezone('Europe/Rome')

    for giorno, lettera_turno in enumerate(lista_turni, start=1):
        # Se il giorno supera i giorni del mese, ci fermiamo
        try:
            data_base = datetime(anno, mese, giorno)
        except ValueError:
            break 

        # Gestione Turno Intero (Pr)
        if config.get('tutto_giorno'):
            event.add('dtstart', data_evento.date())
            # Per lo standard iCal, il giorno di fine è esclusivo, quindi aggiungiamo +1
            event.add('dtend', (data_evento + timedelta(days=1)).date())
        else:
            # Turni con orario
            ora_i, min_i = map(int, config['inizio'].split(':'))
            ora_f, min_f = map(int, config['fine'].split(':'))
            
            inizio = tz.localize(datetime(anno, mese, giorno, ora_i, min_i))
            fine = tz.localize(datetime(anno, mese, giorno, ora_f, min_f))
            
            if fine <= inizio:
                fine += timedelta(days=1)

            event.add('dtstart', inizio)
            event.add('dtend', fine)
            
        # --- NOTA SUL COLORE ---
        # iCalendar non supporta nativamente i colori di Google Calendar.
        # L'unico modo è assegnare una CATEGORY, ma Google spesso la ignora.
        event.add('categories', config['nome'])
            
        cal.add_component(event)

    return cal.to_ical()

# ==========================================
# 3. INTERFACCIA WEB (STREAMLIT)
# ==========================================

# Titolo e descrizione dell'app
st.title("📅 Convertitore Turni: PDF -> iCal")
st.write("Carica il PDF dei turni, seleziona il tuo nome e scarica il calendario per il tuo smartphone.")

# Layout: Creiamo due colonne per organizzare visivamente gli input
col1, col2 = st.columns(2)

with col1:
    mese_selezionato = st.number_input("Mese (es. 4 per Aprile)", min_value=1, max_value=12, value=datetime.now().month)
with col2:
    anno_selezionato = st.number_input("Anno", min_value=2024, max_value=2050, value=datetime.now().year)

# Campo per inserire il nome (che poi cercheremo nel PDF)
nome_utente = st.text_input("Inserisci il tuo Nome e Cognome (esattamente come scritto nel PDF)")

# Area per caricare il file PDF
file_caricato = st.file_uploader("Carica il PDF dei turni mensili", type="pdf")

# Pulsante per avviare la conversione (appare solo se è stato caricato un file e inserito un nome)
if file_caricato is not None and nome_utente:
    
    if st.button("Genera Calendario"):
        with st.spinner("Analisi del PDF in corso..."):
            
            # 1. Estraiamo la lista di lettere dal PDF
            turni_estratti = estrai_turni_da_pdf(file_caricato, nome_utente)
            
            # 2. Generiamo i dati del calendario
            dati_ical = crea_file_ical(turni_estratti, anno_selezionato, mese_selezionato)
            
            # 3. Prepariamo il file per il download in memoria
            file_in_memoria = io.BytesIO(dati_ical)
            
            st.success("✅ Calendario generato con successo!")
            
            # 4. Mostriamo il pulsante di Download
            st.download_button(
                label="📥 Scarica file .ics",
                data=file_in_memoria,
                file_name=f"turni_{mese_selezionato}_{anno_selezionato}.ics",
                mime="text/calendar"
            )
elif file_caricato is None:
    st.info("Carica un file PDF per iniziare.")
elif not nome_utente:
    st.warning("Inserisci il tuo nome per poter cercare i tuoi turni nel PDF.")