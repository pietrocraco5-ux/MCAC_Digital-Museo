# Architettura tecnica e modello del caso studio

**Organizzazione simulata:** Museo Civico delle Arti e della Cultura di Napoli (MCAC). Non esistono rilievi sul campo. Tutti i dati presenti nella piattaforma sono generati esclusivamente per la dimostrazione.

## Scenario AS-IS → TO-BE

- **AS-IS (ipotetico):** prenotazioni ricevute via email, registrazione visitatori in fogli di calcolo, catalogo separato, feedback non strutturati.
- **TO-BE (prototipo):** unico database per utenti, catalogo, eventi, prenotazioni e feedback, con interfaccia web, API e dashboard.

## Architettura logica

`Browser (HTML / CSS / JS) ⇄ JSON su HTTP ⇄ Flask (oppure server locale) ⇄ SQLite`

La business logic è in `core.py`; `app.py` e `server.py` sono due adapter intercambiabili.

## Componenti

| Componente | File | Responsabilità |
|---|---|---|
| Front-end | `static/index.html`, `style.css`, `app.js` | Navigazione, schede eventi, moduli, grafici CSS |
| API | `app.py` oppure `server.py` | HTTP, serializzazione JSON, codici di risposta |
| Dominio | `core.py` | Autenticazione, ACL, prenotazioni, indicatori |
| Persistenza | `schema.sql`, `mcac.sqlite3` | Vincoli, integrità e memorizzazione |
| Dataset | `seed.py` | Popolamento riproducibile inventato |
| Test | `tests/test_api.py` | Verifiche automatizzate API e logica |

## Regole aziendali implementate

1. L'utente si registra come `visitor` con email univoca.
2. La password è memorizzata con PBKDF2-HMAC-SHA256, salt casuale e 600.000 iterazioni.
3. Il login restituisce un token bearer, il cui solo SHA-256 è memorizzato in `sessions`; durata 12 ore.
4. Si prenotano da 1 a 6 posti per evento; non si possono creare due prenotazioni confermate per lo stesso utente/evento.
5. Il controllo capienza avviene nel database all'interno di `BEGIN IMMEDIATE` per serializzare la lettura dei posti e il successivo inserimento.
6. Cancellare una prenotazione libera i posti; è possibile prenotare di nuovo.
7. Solo l'utente che ha una prenotazione confermata può inviare un feedback (massimo 1 per evento).
8. Solo un amministratore può leggere dashboard completa e inserire opere o eventi.

## Modello relazionale

`users (id PK, email UNIQUE, role)`; `works (id PK)`; `events (id PK, capacity)`; `bookings (id PK, user_id FK, event_id FK, UNIQUE(user_id,event_id))`; `feedback (id PK, user_id FK, event_id FK, UNIQUE(user_id,event_id))`; `sessions (token_hash PK, user_id FK)`.

**Cardinalità:** un utente possiede 0..N prenotazioni; un evento riceve 0..N prenotazioni; un utente lascia 0..N feedback, al massimo uno per evento; un utente può avere 0..N sessioni. Le opere sono catalogate indipendentemente dagli eventi nella versione 1.

`PRAGMA foreign_keys=ON` viene eseguito ad ogni nuova connessione SQLite.

## Formule degli indicatori

- `Posti prenotati = Σ bookings.seats WHERE status = 'confirmed'`.
- `Disponibilità evento i = capacity_i - Σ seats_confirmed(event_id=i)`.
- `Occupazione evento i (%) = 100 × posti_prenotati_i / capacity_i`.
- `Occupazione totale (%) = 100 × Σ posti prenotati / Σ capacità eventi attivi`.
- `Valutazione media = AVG(feedback.rating)`.
- **Nota:** l'occupazione totale non è la media semplice delle percentuali dei singoli eventi, ma una media pesata sulla capienza.

## Codici HTTP

- `200`: lettura o azione riuscita; `201`: risorsa creata.
- `400`: dati non validi; `401`: autenticazione assente/scaduta.
- `403`: permesso insufficiente; `404`: risorsa non trovata; `409`: conflitto o posti non disponibili.

## Limiti (da dichiarare nell'elaborato)

- È un progetto **locale e didattico**, non un sistema per clienti reali.
- Non sono implementati conferma tramite email, gestione pagamenti, prenotazioni con attesa, modifiche eventi, upload immagini, account recovery, HTTPS, rate limiting o log di audit.
- Gli eventi e i feedback sono dimostrativi; la verifica dell'effettiva partecipazione prima del feedback non è prevista.
- I grafici presentano dati **generati** e non rappresentano misure raccolte in un museo.
- Gli account demo e le credenziali pubbliche non sono adatti alla produzione.
- Per l'uso pubblico servirebbero autenticazione più evoluta, protezione dati, analisi rischi, monitoraggio, test di concorrenza su scala, backup, logging, infrastruttura HTTPS e valutazione di conformità GDPR.

## Sitografia tecnica ufficiale

- Flask Quickstart: https://flask.palletsprojects.com/en/stable/quickstart/
- SQLite foreign keys: https://www.sqlite.org/foreignkeys.html
- OWASP Password Storage: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
