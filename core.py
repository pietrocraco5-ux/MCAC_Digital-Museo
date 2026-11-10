"""MCAC Digital - dominio e API indipendenti dal server HTTP.
Solo librerie standard: sqlite3, json, hashlib, secrets, datetime.
Dati, account e contesto museale sono inventati per finalità didattiche.
"""
import hashlib
import hmac
import json
import re
import secrets
from contextlib import contextmanager
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / 'mcac.sqlite3'
MAX_BODY = 12000

class APIError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)

@contextmanager
def connection(path=None):
    db = sqlite3.connect(str(path or DB_FILE), timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=10000')
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db(path=None):
    with connection(path) as db:
        db.executescript((ROOT/'schema.sql').read_text(encoding='utf8'))

def password_hash(password):
    salt = secrets.token_bytes(16)
    iterations = 600000
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    return 'pbkdf2_sha256$%d$%s$%s' % (iterations, salt.hex(), key.hex())

def password_verify(password, stored):
    try:
        kind, rounds, salt, digest = stored.split('$')
        if kind != 'pbkdf2_sha256': return False
        test = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(test, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False

def user_view(u):
    return {k:u[k] for k in ('id','name','email','role')}

def require_user(db, bearer, role=None):
    if not bearer or not bearer.lower().startswith('bearer '):
        raise APIError(401, 'Accesso richiesto: effettua il login.')
    key = hashlib.sha256(bearer[7:].strip().encode()).hexdigest()
    u = db.execute('''SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id
         WHERE s.token_hash=? AND s.expires_at>datetime('now')''',(key,)).fetchone()
    if not u: raise APIError(401,'Sessione non valida o scaduta.')
    if role and u['role']!=role: raise APIError(403,'Operazione riservata agli amministratori.')
    return u

def get_text(obj, field, minimum=1, maximum=250):
    value = obj.get(field)
    if not isinstance(value,str) or not minimum <= len(value.strip()) <= maximum:
        raise APIError(400, f'Il campo {field} deve contenere tra {minimum} e {maximum} caratteri.')
    return value.strip()

def get_int(obj, field, minimum, maximum):
    value=obj.get(field)
    if isinstance(value,bool) or not isinstance(value,int) or not minimum<=value<=maximum:
        raise APIError(400, f'Il campo {field} deve essere un intero tra {minimum} e {maximum}.')
    return value

def list_events(db):
    return [dict(x) for x in db.execute('''SELECT e.*, COALESCE(SUM(CASE WHEN b.status='confirmed' THEN b.seats ELSE 0 END),0) AS reserved,
             e.capacity-COALESCE(SUM(CASE WHEN b.status='confirmed' THEN b.seats ELSE 0 END),0) AS available
             FROM events e LEFT JOIN bookings b ON b.event_id=e.id
             GROUP BY e.id ORDER BY e.starts_at''')]

def dashboard(db):
    counts={}
    for label,query in {
        'users':'SELECT count(*) FROM users',
        'works':'SELECT count(*) FROM works',
        'events':'SELECT count(*) FROM events',
        'bookings':'SELECT count(*) FROM bookings WHERE status="confirmed"',
        'cancelled':'SELECT count(*) FROM bookings WHERE status="cancelled"',
        'seats_booked':'SELECT COALESCE(sum(seats),0) FROM bookings WHERE status="confirmed"',
        'feedback_count':'SELECT count(*) FROM feedback',
        'rating_mean':'SELECT ROUND(AVG(rating),2) FROM feedback'
    }.items(): counts[label]=db.execute(query).fetchone()[0]
    ev=list_events(db)
    counts['total_capacity']=sum(e['capacity'] for e in ev if e['status']=='active')
    counts['occupancy_percent']=round(100*counts['seats_booked']/counts['total_capacity'],1) if counts['total_capacity'] else 0
    counts['by_event']=[{'id':e['id'],'title':e['title'],'reserved':e['reserved'],'capacity':e['capacity'],'occupancy_percent':round(e['reserved']*100/e['capacity'],1)} for e in ev]
    counts['by_kind']=[dict(x) for x in db.execute('''SELECT e.kind,COUNT(b.id) booking_count,
         COALESCE(SUM(b.seats),0) seats FROM bookings b JOIN events e ON e.id=b.event_id
         WHERE b.status='confirmed' GROUP BY e.kind ORDER BY seats DESC''')]
    counts['rating_distribution']={str(i):db.execute('SELECT COUNT(*) FROM feedback WHERE rating=?',(i,)).fetchone()[0] for i in range(1,6)}
    return counts

def handle(method, path, data=None, bearer=None, db_path=None):
    """Restituisce (stato_http, oggetto_json). Errori convertiti in JSON.
    Questa stessa funzione serve sia l'adapter Flask sia il server standard.
    """
    data=data or {}
    try:
        if not isinstance(data,dict): raise APIError(400,'JSON deve essere un oggetto.')
        with connection(db_path) as db:
            if method=='GET' and path=='/api/health':
                db.execute('SELECT 1'); return 200, {'status':'ok','app':'MCAC Digital','version':'1.0.0'}
            if method=='POST' and path=='/api/register':
                name=get_text(data,'name',2,100)
                email=get_text(data,'email',5,180).lower()
                pwd=get_text(data,'password',10,128)
                if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email): raise APIError(400,'Formato email non valido.')
                try:
                    cur=db.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(name,email,password_hash(pwd)))
                except sqlite3.IntegrityError: raise APIError(409,'Indirizzo email già registrato.')
                return 201,{'user_id':cur.lastrowid,'message':'Registrazione completata.'}
            if method=='POST' and path=='/api/login':
                email=get_text(data,'email',5,180).lower()
                pwd=get_text(data,'password',1,128)
                u=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                if not u or not password_verify(pwd,u['password_hash']):
                    raise APIError(401,'Email o password non corretti.')
                token=secrets.token_urlsafe(32)
                expires=(datetime.now(timezone.utc)+timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
                db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)',
                           (hashlib.sha256(token.encode()).hexdigest(),u['id'],expires))
                return 200,{'token':token,'expires_in_seconds':43200,'user':user_view(u)}
            if method=='POST' and path=='/api/logout':
                require_user(db,bearer)
                db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(bearer[7:].strip().encode()).hexdigest(),))
                return 200,{'message':'Sessione chiusa.'}
            if method=='GET' and path=='/api/me':
                return 200,{'user':user_view(require_user(db,bearer))}
            if method=='GET' and path=='/api/works':
                return 200,{'items':[dict(x) for x in db.execute('SELECT * FROM works ORDER BY id')]}
            if method=='GET' and path=='/api/events':
                return 200,{'items':list_events(db)}
            if method=='GET' and re.fullmatch(r'/api/events/\d+',path):
                event_id=int(path.rsplit('/',1)[1]); ev=next((e for e in list_events(db) if e['id']==event_id),None)
                if ev is None: raise APIError(404,'Evento inesistente.')
                return 200,{'event':ev}
            if method=='GET' and path=='/api/bookings':
                u=require_user(db,bearer)
                items=[dict(x) for x in db.execute('''SELECT b.*,e.title as event_title,e.starts_at,e.kind
                     FROM bookings b JOIN events e ON e.id=b.event_id WHERE b.user_id=? ORDER BY e.starts_at''',(u['id'],))]
                return 200,{'items':items}
            if method=='POST' and path=='/api/bookings':
                u=require_user(db,bearer)
                event_id=get_int(data,'event_id',1,1000000)
                seats=get_int(data,'seats',1,6)
                db.execute('BEGIN IMMEDIATE')
                event=db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
                if not event: raise APIError(404,'Evento inesistente.')
                if event['status']!='active': raise APIError(409,'Evento non prenotabile.')
                existing=db.execute('SELECT * FROM bookings WHERE user_id=? AND event_id=?',(u['id'],event_id)).fetchone()
                if existing and existing['status']=='confirmed': raise APIError(409,'Hai già una prenotazione confermata per questo evento.')
                occupied=db.execute('SELECT COALESCE(SUM(seats),0) FROM bookings WHERE event_id=? AND status="confirmed"',(event_id,)).fetchone()[0]
                if occupied+seats>event['capacity']: raise APIError(409,f'Posti insufficienti: disponibili {event["capacity"]-occupied}.')
                if existing:
                    db.execute('UPDATE bookings SET seats=?,status="confirmed",created_at=datetime("now") WHERE id=?',(seats,existing['id']))
                    booking_id=existing['id']
                else:
                    booking_id=db.execute('INSERT INTO bookings(user_id,event_id,seats) VALUES(?,?,?)',(u['id'],event_id,seats)).lastrowid
                db.execute('COMMIT')
                return 201,{'booking_id':booking_id,'status':'confirmed','seats':seats}
            if method=='DELETE' and re.fullmatch(r'/api/bookings/\d+',path):
                u=require_user(db,bearer);bid=int(path.rsplit('/',1)[1])
                b=db.execute('SELECT * FROM bookings WHERE id=? AND user_id=?',(bid,u['id'])).fetchone()
                if not b: raise APIError(404,'Prenotazione inesistente.')
                if b['status']=='cancelled': raise APIError(409,'Prenotazione già cancellata.')
                db.execute('UPDATE bookings SET status="cancelled" WHERE id=?',(bid,))
                return 200,{'message':'Prenotazione cancellata.'}
            if method=='POST' and path=='/api/feedback':
                u=require_user(db,bearer)
                eid=get_int(data,'event_id',1,1000000)
                rating=get_int(data,'rating',1,5)
                comment=get_text(data,'comment',0,500) if 'comment' in data else ''
                booking=db.execute('SELECT id FROM bookings WHERE user_id=? AND event_id=? AND status="confirmed"',(u['id'],eid)).fetchone()
                if not booking: raise APIError(403,'È necessaria una prenotazione confermata per valutare questo evento.')
                try: fid=db.execute('INSERT INTO feedback(user_id,event_id,rating,comment) VALUES(?,?,?,?)',(u['id'],eid,rating,comment)).lastrowid
                except sqlite3.IntegrityError: raise APIError(409,'Hai già valutato questo evento.')
                return 201,{'feedback_id':fid,'message':'Grazie per la valutazione.'}
            if method=='GET' and path=='/api/dashboard':
                require_user(db,bearer,'admin');return 200,dashboard(db)
            if method=='GET' and path=='/api/admin/bookings':
                require_user(db,bearer,'admin')
                return 200,{'items':[dict(x) for x in db.execute('''SELECT b.*,u.name AS user_name,u.email,e.title AS event_title FROM bookings b JOIN users u ON u.id=b.user_id JOIN events e ON e.id=b.event_id ORDER BY b.id DESC LIMIT 200''')]}
            if method=='POST' and path=='/api/events':
                require_user(db,bearer,'admin')
                title=get_text(data,'title',3,150);kind=get_text(data,'kind',3,50)
                starts_at=get_text(data,'starts_at',16,20);description=get_text(data,'description',5,600)
                try: datetime.fromisoformat(starts_at)
                except ValueError: raise APIError(400,'Data evento non valida.')
                duration=get_int(data,'duration_minutes',15,600);capacity=get_int(data,'capacity',1,500)
                eid=db.execute('INSERT INTO events(title,kind,starts_at,duration_minutes,capacity,description) VALUES(?,?,?,?,?,?)',
                               (title,kind,starts_at,duration,capacity,description)).lastrowid
                return 201,{'event_id':eid,'message':'Evento creato.'}
            if method=='POST' and path=='/api/works':
                require_user(db,bearer,'admin')
                title=get_text(data,'title',2,150);author=get_text(data,'author',2,150)
                year=get_int(data,'year',-3000,2100);category=get_text(data,'category',2,50)
                room=get_text(data,'room',2,80);description=get_text(data,'description',5,1000)
                wid=db.execute('INSERT INTO works(title,author,year,category,room,description) VALUES(?,?,?,?,?,?)',
                               (title,author,year,category,room,description)).lastrowid
                return 201,{'work_id':wid,'message':'Opera inserita.'}
            raise APIError(404,'Endpoint non trovato.')
    except APIError as exc:
        return exc.status,{'error':exc.message}
    except sqlite3.Error:
        return 500,{'error':'Errore interno del database.'}
