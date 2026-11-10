"""Inizializzazione dati ESCLUSIVAMENTE SIMULATI, idempotente se DB popolato."""
import random
from datetime import datetime,timedelta
from core import init_db,connection,password_hash,DB_FILE

WORKS=[
 ('Veduta del Golfo','L. Esposito',1898,'Pittura','Sala A','Paesaggio a olio ispirato alla costa napoletana.'),
 ('Il mercato antico','M. Russo',1912,'Pittura','Sala A','Scena urbana di vita popolare.'),
 ('Ceramica mediterranea','Bottega campana',1750,'Ceramica','Sala B','Vaso decorativo a motivi geometrici.'),
 ('Ritratto di musicista','A. De Luca',1924,'Pittura','Sala A','Ritratto immaginario della tradizione musicale.'),
 ('La piazza al tramonto','G. Romano',1884,'Pittura','Sala A','Rappresentazione di uno spazio cittadino.'),
 ('Busto di poeta','S. Vitale',1903,'Scultura','Sala C','Busto in marmo di figura immaginaria.'),
 ('Manifesto del teatro','Archivio MCAC',1936,'Grafica','Sala D','Manifesto d’epoca ricostruito per il catalogo.'),
 ('Mappa storica illustrata','Archivio MCAC',1805,'Documento','Sala D','Riproduzione dimostrativa di una mappa urbana.'),
 ('Figura in movimento','C. Ferraro',1961,'Scultura','Sala C','Scultura astratta in bronzo.'),
 ('Luce sul porto','P. Greco',1954,'Fotografia','Sala E','Fotografia artistica in bianco e nero.'),
 ('Partitura illustrata','Archivio MCAC',1930,'Documento','Sala D','Documento musicale con disegni.'),
 ('Composizione azzurra','E. Fontana',1972,'Pittura','Sala B','Opera astratta con tonalità del Mediterraneo.')
]
EVENTS=[
 ('Napoli tra arte e memoria','Visita guidata','2026-11-15T10:00',90,30,'Percorso commentato nella collezione permanente.'),
 ('Laboratorio colori del Mediterraneo','Laboratorio','2026-11-17T15:00',120,24,'Attività creativa dedicata ai colori e alle tecniche artistiche.'),
 ('Storie della città','Conferenza','2026-11-20T17:30',75,45,'Racconti e testimonianze della storia cittadina.'),
 ('Sculture e materiali','Visita guidata','2026-11-23T11:00',60,25,'Visita tematica dedicata alla scultura.'),
 ('Fotografia e memoria','Laboratorio','2026-11-25T16:00',100,28,'Laboratorio di lettura delle immagini.'),
 ('Notte al museo','Evento','2026-11-28T19:00',150,50,'Apertura serale con percorso culturale.'),
 ('Catalogare il patrimonio','Conferenza','2026-12-02T16:30',80,36,'Incontro divulgativo sulla catalogazione delle opere.'),
 ('Percorsi per le famiglie','Visita guidata','2026-12-06T10:30',90,32,'Attività culturale per piccoli gruppi e famiglie.')
]

def seed(path=None):
    init_db(path)
    rng=random.Random(20261108)
    with connection(path) as db:
        if db.execute('SELECT COUNT(*) FROM users').fetchone()[0]: return False
        users=[('Amministratore MCAC','admin@mcac.test','admin'),('Visitatore Demo','visitatore@mcac.test','visitor')]
        users += [(f'Visitatore simulato {i:02d}',f'ospite{i:02d}@mcac.test','visitor') for i in range(1,21)]
        for name,email,role in users:
            db.execute('INSERT INTO users(name,email,role,password_hash) VALUES(?,?,?,?)',
                       (name,email,role,password_hash('Demo2026!sicura')))
        db.executemany('INSERT INTO works(title,author,year,category,room,description) VALUES(?,?,?,?,?,?)',WORKS)
        db.executemany('INSERT INTO events(title,kind,starts_at,duration_minutes,capacity,description) VALUES(?,?,?,?,?,?)',EVENTS)
        # 43 prenotazioni confermate simulate, posti vincolati alle capacità degli eventi
        combos=set()
        while len(combos)<43:
            uid=rng.randint(2,22);eid=rng.randint(1,8)
            if (uid,eid) in combos: continue
            seats=rng.randint(1,3)
            used=db.execute('SELECT COALESCE(SUM(seats),0) FROM bookings WHERE event_id=? AND status="confirmed"',(eid,)).fetchone()[0]
            cap=EVENTS[eid-1][4]
            if used+seats>cap: continue
            db.execute('INSERT INTO bookings(user_id,event_id,seats) VALUES(?,?,?)',(uid,eid,seats))
            combos.add((uid,eid))
        for idx,(uid,eid) in enumerate(sorted(combos)[:17]):
            db.execute('INSERT INTO feedback(user_id,event_id,rating,comment) VALUES(?,?,?,?)',
                       (uid,eid,[4,5,4,3,5][idx%5],'Feedback dimostrativo sul servizio culturale.'))
    return True

if __name__=='__main__':
    seed()
    print('Database demo pronto:',DB_FILE)
