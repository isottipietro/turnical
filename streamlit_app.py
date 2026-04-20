import streamlit as st
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import io

# ==========================================
# 1. CONFIGURAZIONE DEI TURNI
# ==========================================
orari_turni = {
    'M': {'inizio': '07:30', 'fine': '13:12'},
    'P': {'inizio': '14:18', 'fine': '20:00'}, 
    'G': {'inizio': '08:00', 'fine': '13:42'}, 
    'G1': {'inizio': '08:30', 'fine': '14:12'}, 
    'G2': {'inizio': '09:00', 'fine': '14:42'},
    'G3': {'inizio': '10:48', 'fine': '18:30'} 
}

# ==========================================
# 2. FUNZIONI
# ==========================================
def estrai_turni_da_pdf(file_pdf, nome_utente):
    """
    ATTENZIONE: Questa è una funzione simulata.
    Qui andrà inserita la logica con pdfplumber per leggere il tuo PDF specifico.
    Per ora, restituisce una lista finta di 30 giorni per farti testare l'app.
    """
    # Simuliamo un mese di turni casuali per testare l'app
    return ['R', 'R', 'R', 'G', 'G', 'G', 'Pr'] # R = Riposo, Pr = Permesso

def crea_file_ical(lista_turni, anno, mese):
    """Prende la lista di lettere e genera il contenuto del file .ics"""
    cal = Calendar()
    cal.add('prodid', '-//Turni Web App//')
    cal.add('version', '2.0')
    tz = pytz.timezone('Europe/Rome')

    for giorno, lettera_turno in enumerate(lista_turni, start=1):
        # Se il giorno supera i giorni del mese, ci fermiamo
        try:
            data_base = datetime(anno, mese, giorno)
        except ValueError:
            break 

        if lettera_turno in orari_turni and orari_turni[lettera_turno] is not None:
            turno = orari_turni[lettera_turno]
            
            ora_inizio, min_inizio = map(int, turno['inizio'].split(':'))
            inizio = tz.localize(datetime(anno, mese, giorno, ora_inizio, min_inizio))
            
            ora_fine, min_fine = map(int, turno['fine'].split(':'))
            fine = tz.localize(datetime(anno, mese, giorno, ora_fine, min_fine))
            
            if fine <= inizio:
                fine += timedelta(days=1) # Turno a cavallo della mezzanotte

            event = Event()
            event.add('summary', f'Turno {lettera_turno}')
            event.add('dtstart', inizio)
            event.add('dtend', fine)
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