# MCAC Digital — prototipo web per museo simulato

Progetto universitario **dimostrativo**. Il Museo Civico delle Arti e della Cultura di Napoli (MCAC), i nomi delle opere, i visitatori, gli eventi e tutte le statistiche sono **inventati**. Non è un sito istituzionale e non tratta dati reali.

## Avvio immediato (nessuna libreria da installare)

1. Installa **Python 3.10+**.
2. Apri il terminale nella cartella `MCAC_Digital`.
3. Esegui `python seed.py` e poi `python server.py`.
4. Apri **http://127.0.0.1:5000** nel browser.
5. Termina il server con `Ctrl+C`.

Su Windows, se il comando `python` non è disponibile, usa `py -3 seed.py` e `py -3 server.py`.

### Avvio con Flask (facoltativo, consigliato per la traccia)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux / macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python seed.py
python app.py
```

Gli endpoint e i dati sono **identici** nei due server perché condividono `core.py`.
Il server standard, incluso per comodità, usa `http.server` ed è destinato **solo alla dimostrazione locale**, come il server di sviluppo Flask.

## Account di prova (non riutilizzare in produzione)

| Profilo | Email | Password |
|---|---|---|
| Amministratore | `admin@mcac.test` | `Demo2026!sicura` |
| Visitatore | `visitatore@mcac.test` | `Demo2026!sicura` |

Il database contiene account e prenotazioni **fittizi**. Le password sono salvate con PBKDF2-HMAC-SHA256 e salt casuale (600.000 iterazioni); non sono in chiaro.

## Funzionalità

- Catalogo con ricerca e filtro per categoria.
- Calendario eventi, disponibilità posti e prenotazioni (1-6 posti).
- Registrazione, login con token temporaneo, logout.
- Elenco e cancellazione delle proprie prenotazioni.
- Feedback associato a prenotazioni confermate (1-5).
- Dashboard amministrativa, con occupazione per evento e valutazioni.
- Inserimento di nuove opere ed eventi riservato agli amministratori.
- API REST JSON con errori HTTP espliciti.

## Struttura file

```text
MCAC_Digital/
├── app.py               adapter Flask
├── server.py            server dimostrativo senza dipendenze
├── core.py              logica business + autenticazione + API
├── seed.py              generatore deterministico di dati inventati
├── schema.sql           struttura relazionale, vincoli e indici
├── mcac.sqlite3         database dimostrativo già incluso
├── static/              index.html, style.css, app.js
├── docs/                API OpenAPI, diagrammi e documentazione
├── tests/               test automatici
└── results/             report test, schermate e grafici
```

## Test automatici

Esegui `python -m unittest discover -s tests -v`. I test utilizzano un database temporaneo e non modificano `mcac.sqlite3`.

## Sicurezza e limitazioni

Il sistema usa query SQL parametrizzate, hash sicuro delle password, token casuali salvati come digest, controllo del ruolo amministratore e transazioni `BEGIN IMMEDIATE` per evitare doppie assegnazioni di posti. La demo utilizza un token in `sessionStorage`, non include verifica email, recupero password, limitazione tentativi, log di audit, HTTPS o infrastruttura di backup. **Non pubblicare la demo su Internet né inserirvi dati personali reali** senza ulteriori misure.

## File correlati

- `docs/ARCHITETTURA.md`: processi, scelte tecniche, formule, limiti.
- `docs/openapi.yaml`: specifica degli endpoint.
- `docs/diagrams/`: architettura, schema E-R, use case.
- `results/`: dati derivati dal database, grafici e test.
