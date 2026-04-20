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
    'Pr': {'nome': 'Permesso', 'tutto_giorno': True},
    'R':  None 
}

# ==========================================
# 2. FUNZIONI
# ==========================================
def estrai_turni_da_pdf(file_pdf, nome_utente):
    nome_utente = nome_utente.lower().strip()
    
    with pdfplumber.open(file_pdf) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            
            for row in table:
                row_cleaned = [str(cell).strip() if cell else "" for cell in row]
                # Controllo se il nome è presente in qualche cella della riga
                if any(nome_utente in cell.lower() for cell in row_cleaned):
                    # Cerchiamo di capire dove iniziano i turni (escludendo il nome)
                    # Se il nome è nella prima colonna, prendiamo dalla seconda in poi
                    return row_cleaned[1:] 
    return None

def crea_file_ical(lista_turni, anno, mese):
    cal = Calendar()
    cal.add('prodid', '-//Turni Web App//')
    cal.add('version', '2.0')
    tz = pytz.timezone('Europe/Rome')

    for giorno, lettera_turno in enumerate(lista_turni, start=1):
        try:
            data_base = datetime(anno, mese, giorno)
        except ValueError:
            break 

        # Verifichiamo che la lettera sia tra quelle configurate e non sia Riposo
        if lettera_turno in orari_turni and orari_turni[lettera_turno] is not None:
            config = orari_turni[lettera_turno]
            event = Event()
            event.add('summary', config['nome'])

            if config.get('tutto_giorno'):
                event.add('dtstart', data_base.date())
                event.add('dtend', (data_base + timedelta(days=1)).date())
            else:
                ora_i, min_i = map(int, config['inizio'].split(':'))
                ora_f, min_f = map(int, config['fine'].split(':'))
                
                inizio = tz.localize(datetime(anno, mese, giorno, ora_i, min_i))
                fine = tz.localize(datetime(anno, mese, giorno, ora_f, min_f))
                
                if fine <= inizio:
                    fine += timedelta(days=1)

                event.add('dtstart', inizio)
                event.add('dtend', fine)
            
            event.add('categories', config['nome'])
            cal.add_component(event)

    return cal.to_ical()

# ==========================================
# 3. INTERFACCIA WEB (STREAMLIT)
# ==========================================
st.title("📅 Convertitore Turni: PDF -> iCal")

col1, col2 = st.columns(2)
with col1:
    mese_selezionato = st.number_input("Mese", min_value=1, max_value=12, value=datetime.now().month)
with col2:
    anno_selezionato = st.number_input("Anno", min_value=2024, max_value=2050, value=datetime.now().year)

nome_utente = st.text_input("Inserisci il tuo Nome e Cognome")
file_caricato = st.file_uploader("Carica il PDF", type="pdf")

if file_caricato and nome_utente:
    if st.button("Genera Calendario"):
        with st.spinner("Analisi in corso..."):
            turni_estratti = estrai_turni_da_pdf(file_caricato, nome_utente)
            
            if turni_estratti:
                dati_ical = crea_file_ical(turni_estratti, anno_selezionato, mese_selezionato)
                st.success(f"✅ Turni trovati per {nome_utente}!")
                st.download_button(
                    label="📥 Scarica file .ics",
                    data=io.BytesIO(dati_ical),
                    file_name=f"turni_{nome_utente}_{mese_selezionato}.ics",
                    mime="text/calendar"
                )
            else:
                st.error(f"❌ Non ho trovato il nome '{nome_utente}' nel PDF. Controlla che sia scritto correttamente.")