import streamlit as st
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import io
import pdfplumber
import re

# ==========================================
# 1. CONFIGURAZIONE DEI TURNI
# ==========================================
orari_turni_standard = {
    'M': {'nome': 'Mattina', 'inizio': '07:30', 'fine': '15:12'},
    'P': {'nome': 'Pomeriggio', 'inizio': '12:18', 'fine': '20:00'}, 
    'G': {'nome': 'Giornata', 'inizio': '08:00', 'fine': '15:42'}, 
    'G1': {'nome': 'Giornata 1', 'inizio': '08:30', 'fine': '16:12'}, 
    'G2': {'nome': 'Giornata 2', 'inizio': '09:00', 'fine': '16:42'},
    'G3': {'nome': 'Giornata 3', 'inizio': '10:48', 'fine': '18:30'},
    'Pr': {'nome': 'Permesso', 'tutto_giorno': True},
    'R': None,
    'F': None,
    'Ro': None
}

orari_turni_allattamento = {
    'M': {'nome': 'Mattina', 'inizio': '07:30', 'fine': '12:42'},
    'P': {'nome': 'Pomeriggio', 'inizio': '14:48', 'fine': '20:00'}, 
    'G': {'nome': 'Giornata', 'inizio': '08:00', 'fine': '13:12'}, 
    'G1': {'nome': 'Giornata 1', 'inizio': '08:30', 'fine': '13:42'}, 
    'G2': {'nome': 'Giornata 2', 'inizio': '09:00', 'fine': '14:12'},
    'G3': {'nome': 'Giornata 3', 'inizio': '10:48', 'fine': '18:30'},
    'Pr': {'nome': 'Permesso', 'tutto_giorno': True},
    'R':  None 
}

# ==========================================
# 2. FUNZIONI
# ==========================================
def estrai_turni_da_pdf(file_pdf, nome_utente):
    nome_utente = nome_utente.upper().strip()
    
    with pdfplumber.open(file_pdf) as pdf:
        testo_pagina = pdf.pages[0].extract_text()
        righe = testo_pagina.split('\n')
        
        for i, riga in enumerate(righe):
            if nome_utente in riga.upper():
                contesto = " ".join(righe[i:i+3]) 
                
                codici_validi = ['M', 'P', 'G', 'G1', 'G2', 'G3', 'R', 'Pr', 'Ag', 'F', 'Ro']
                token = contesto.split()
                percorso_turni = []
                
                for t in token:
                    if t in codici_validi:
                        percorso_turni.append(t)
                    elif len(t) <= 3 and any(c in t for c in "MPGR"):
                        for char in t:
                            if char in "MPGR": percorso_turni.append(char)

                if percorso_turni:
                    return percorso_turni
                    
    return None

def crea_file_ical(lista_turni, anno, mese, orari_selezionati):
    cal = Calendar()
    cal.add('prodid', '-//Turni Web App//')
    cal.add('version', '1.1')
    tz = pytz.timezone('Europe/Rome')

    for giorno, lettera_turno in enumerate(lista_turni, start=1):
        try:
            data_base = datetime(anno, mese, giorno)
        except ValueError:
            break 

        if lettera_turno in orari_selezionati and orari_selezionati[lettera_turno] is not None:
            config = orari_selezionati[lettera_turno]
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
st.title("📅 Convertitore Turni Agrate: PDF -> iCal")

col1, col2 = st.columns(2)
with col1:
    mese_selezionato = st.number_input("Mese", min_value=1, max_value=12, value=datetime.now().month % 12 + 1)
with col2:
    anno_selezionato = st.number_input("Anno", min_value=2024, max_value=2050, value=datetime.now().year  + (1 if datetime.now().month == 12 else 0))

nome_utente = st.text_input("Inserisci COGNOME NOME (esattamente come scritto nel pdf)")

file_caricato = st.file_uploader("Carica il PDF", type="pdf")

# --- SEZIONE IMPOSTAZIONI AGGIUNTIVE ---
with st.expander("⚙️ Impostazioni"):
    usa_allattamento = st.checkbox("👶 Attiva orario ridotto (Allattamento)")
    # Qui potrai aggiungere altre st.checkbox o st.selectbox in futuro
    
if file_caricato and nome_utente:
    if st.button("Genera Calendario"):
        with st.spinner("Analisi in corso..."):
            turni_estratti = estrai_turni_da_pdf(file_caricato, nome_utente)
            
            if turni_estratti:
                # Scegli il dizionario in base all'impostazione
                dizionario_orari = orari_turni_allattamento if usa_allattamento else orari_turni_standard
                
                dati_ical = crea_file_ical(turni_estratti, anno_selezionato, mese_selezionato, dizionario_orari)
                
                st.success(f"✅ Turni trovati per {nome_utente}!")
                st.download_button(
                    label="📥 Scarica file .ics",
                    data=io.BytesIO(dati_ical),
                    file_name=f"Turni_{nome_utente}_{mese_selezionato}.ics",
                    mime="text/calendar"
                )
            else:
                st.error(f"❌ Non ho trovato il nome '{nome_utente}' nel PDF. Controlla che sia scritto correttamente.")
