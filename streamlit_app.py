from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz

# 1. Configurazione dei tuoi turni (Personalizza questi orari)
orari_turni = {
    'M': {'inizio': '07:30', 'fine': '13:12'},
    'P': {'inizio': '14:18', 'fine': '20:00'}, 
    'G': {'inizio': '08:00', 'fine': '13:42'}, 
    'G1': {'inizio': '08:30', 'fine': '14:12'}, 
    'G2': {'inizio': '09:00', 'fine': '14:42'},
    'G3': {'inizio': '10:48', 'fine': '18:30'} 
}

# 2. Simuliamo l'estrazione dal PDF per il mese di Aprile 2026
# (Nella realtà, qui useresti pdfplumber per estrarre questa lista)
nome_lavoratore = "Pietro Isotti"
mese_anno = (2026, 5) # Aprile 2026
# Immaginiamo che questi siano i turni estratti dall'1 al 7 del mese:
turni_estratti = ['R', 'R', 'R', 'G', 'G', 'G', 'Pr'] # R = Riposo, Pr = Permesso

# 3. Creazione del Calendario
cal = Calendar()
cal.add('prodid', '-//Il Mio Generatore di Turni//')
cal.add('version', '1.0')
tz = pytz.timezone('Europe/Rome')

# 4. Creazione degli eventi
for giorno, lettera_turno in enumerate(turni_estratti, start=1):
    if lettera_turno in orari_turni:
        turno = orari_turni[lettera_turno]
        
        # Calcolo data e ora di inizio
        ora_inizio, min_inizio = map(int, turno['inizio'].split(':'))
        inizio = tz.localize(datetime(mese_anno[0], mese_anno[1], giorno, ora_inizio, min_inizio))
        
        # Calcolo data e ora di fine
        ora_fine, min_fine = map(int, turno['fine'].split(':'))
        fine = tz.localize(datetime(mese_anno[0], mese_anno[1], giorno, ora_fine, min_fine))

        # Creazione Evento iCal
        event = Event()
        event.add('summary', f'Turno {lettera_turno}')
        event.add('dtstart', inizio)
        event.add('dtend', fine)
        cal.add_component(event)

# 5. Salvataggio del file
with open('miei_turni.ics', 'wb') as f:
    f.write(cal.to_ical())
    
print("File .ics generato con successo!")