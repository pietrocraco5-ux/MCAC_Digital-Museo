"""Tests black-box sul core REST; DB isolato, dati inventati."""
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from pathlib import Path
from core import handle,connection,dashboard,DB_FILE,init_db
from seed import seed

class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=DB_FILE
        cls.base=Path(tempfile.mkdtemp(prefix='mcac_base_'))/'base.sqlite3'
        seed(cls.base)
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base.parent)
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp(prefix='mcac_test_'))
        self.db=self.tmp/'data.sqlite3'
        shutil.copyfile(self.base,self.db)
        self.admin=self.login('admin@mcac.test')
        self.visitor=self.login('visitatore@mcac.test')
    def tearDown(self): shutil.rmtree(self.tmp)
    def api(self,method,path,data=None,token=None):
        return handle(method,path,data,('Bearer '+token) if token else None,self.db)
    def login(self,email,password='Demo2026!sicura'):
        status,out=handle('POST','/api/login',{'email':email,'password':password},None,self.db)
        self.assertEqual(status,200,out)
        return out['token']
    def test_01_health(self):
        s,r=self.api('GET','/api/health');self.assertEqual(s,200);self.assertEqual(r['status'],'ok')
    def test_02_catalog_and_events(self):
        self.assertEqual(len(self.api('GET','/api/works')[1]['items']),12)
        self.assertEqual(len(self.api('GET','/api/events')[1]['items']),8)
    def test_03_dashboard_admin_only(self):
        self.assertEqual(self.api('GET','/api/dashboard')[0],401)
        self.assertEqual(self.api('GET','/api/dashboard',token=self.visitor)[0],403)
        self.assertEqual(self.api('GET','/api/dashboard',token=self.admin)[0],200)
    def test_04_registration_and_login(self):
        s,r=self.api('POST','/api/register',{'name':'Mario Demo','email':'mario@example.test','password':'TestSicura1234'})
        self.assertEqual(s,201,r);self.assertTrue(self.login('mario@example.test','TestSicura1234'))
    def test_05_duplicate_email(self):
        s,r=self.api('POST','/api/register',{'name':'Persona demo','email':'visitatore@mcac.test','password':'TestSicura1234'})
        self.assertEqual(s,409,r)
    def test_06_password_too_short(self):
        self.assertEqual(self.api('POST','/api/register',{'name':'Mario Demo','email':'mario@example.test','password':'abc'})[0],400)
    def test_07_invalid_login(self):
        self.assertEqual(self.api('POST','/api/login',{'email':'admin@mcac.test','password':'errata'})[0],401)
    def test_08_booking_requires_login(self):
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':1,'seats':1})[0],401)
    def test_09_new_booking_uses_capacity(self):
        self.api('POST','/api/register',{'name':'Persona test','email':'booker@example.test','password':'TestSicura1234'})
        token=self.login('booker@example.test','TestSicura1234')
        before=self.api('GET','/api/events/1')[1]['event']['available']
        s,r=self.api('POST','/api/bookings',{'event_id':1,'seats':2},token)
        self.assertEqual(s,201,r)
        self.assertEqual(self.api('GET','/api/events/1')[1]['event']['available'],before-2)
    def test_10_duplicate_booking(self):
        self.api('POST','/api/register',{'name':'Persona test','email':'dup@example.test','password':'TestSicura1234'})
        token=self.login('dup@example.test','TestSicura1234')
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':1,'seats':1},token)[0],201)
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':1,'seats':1},token)[0],409)
    def test_11_booking_capacity_error(self):
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':1,'seats':999},self.visitor)[0],400)
        with connection(self.db) as db:
            db.execute('UPDATE events SET capacity=1 WHERE id=1')
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':1,'seats':1},self.visitor)[0],409)
    def test_12_cancel_booking(self):
        self.api('POST','/api/register',{'name':'Persona test','email':'cancel@example.test','password':'TestSicura1234'})
        token=self.login('cancel@example.test','TestSicura1234')
        bid=self.api('POST','/api/bookings',{'event_id':1,'seats':2},token)[1]['booking_id']
        self.assertEqual(self.api('DELETE',f'/api/bookings/{bid}',token=token)[0],200)
        self.assertEqual(self.api('DELETE',f'/api/bookings/{bid}',token=token)[0],409)
    def test_13_rebook_after_cancel(self):
        self.api('POST','/api/register',{'name':'Persona test','email':'rebook@example.test','password':'TestSicura1234'})
        token=self.login('rebook@example.test','TestSicura1234')
        bid=self.api('POST','/api/bookings',{'event_id':1,'seats':1},token)[1]['booking_id']
        self.api('DELETE',f'/api/bookings/{bid}',token=token)
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':1,'seats':2},token)[0],201)
    def test_14_feedback_requires_confirmed_booking(self):
        self.api('POST','/api/register',{'name':'Persona test','email':'rate@example.test','password':'TestSicura1234'})
        token=self.login('rate@example.test','TestSicura1234')
        self.assertEqual(self.api('POST','/api/feedback',{'event_id':1,'rating':5},token)[0],403)
        self.api('POST','/api/bookings',{'event_id':1,'seats':1},token)
        self.assertEqual(self.api('POST','/api/feedback',{'event_id':1,'rating':5,'comment':'Ottimo'},token)[0],201)
        self.assertEqual(self.api('POST','/api/feedback',{'event_id':1,'rating':4},token)[0],409)
    def test_15_invalid_rating(self):
        self.assertEqual(self.api('POST','/api/feedback',{'event_id':1,'rating':6},self.visitor)[0],400)
    def test_16_admin_create_event(self):
        body={'title':'Nuovo evento','kind':'Visita','starts_at':'2026-12-12T15:00','duration_minutes':90,'capacity':10,'description':'Esperimento didattico.'}
        self.assertEqual(self.api('POST','/api/events',body,self.visitor)[0],403)
        self.assertEqual(self.api('POST','/api/events',body,self.admin)[0],201)
        self.assertEqual(len(self.api('GET','/api/events')[1]['items']),9)
    def test_17_admin_create_work(self):
        body={'title':'Opera demo','author':'Autore demo','year':2020,'category':'Pittura','room':'Sala A','description':'Descrizione test.'}
        self.assertEqual(self.api('POST','/api/works',body,self.visitor)[0],403)
        self.assertEqual(self.api('POST','/api/works',body,self.admin)[0],201)
    def test_18_logout(self):
        self.assertEqual(self.api('POST','/api/logout',token=self.visitor)[0],200)
        self.assertEqual(self.api('GET','/api/me',token=self.visitor)[0],401)
    def test_19_sql_injection_is_data(self):
        self.api('POST','/api/register',{'name':'Test SQL','email':'sql@example.test','password':'TestSicura1234'})
        s,r=self.api('POST','/api/login',{'email':"admin@mcac.test' OR 1=1 --",'password':'wrong'})
        self.assertEqual(s,401)
        self.assertEqual(self.api('GET','/api/works')[0],200)
    def test_20_dashboard_formula(self):
        d=self.api('GET','/api/dashboard',token=self.admin)[1]
        self.assertEqual(d['users'],22);self.assertEqual(d['bookings'],43)
        self.assertEqual(d['feedback_count'],17)
        self.assertAlmostEqual(d['occupancy_percent'],round(100*d['seats_booked']/d['total_capacity'],1))
    def test_21_bad_input(self):
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':'1','seats':2},self.visitor)[0],400)
        self.assertEqual(self.api('GET','/api/no_such_endpoint')[0],404)
    def test_22_unknown_event(self):
        self.assertEqual(self.api('GET','/api/events/555555')[0],404)
        self.assertEqual(self.api('POST','/api/bookings',{'event_id':555555,'seats':1},self.visitor)[0],404)
    def test_23_simultaneous_booking_does_not_oversell(self):
        # Due utenti distinti competono per un unico posto residuo.
        for suffix in ('a','b'):
            status,_=self.api('POST','/api/register',
              {'name':'Utente '+suffix,'email':f'parallel_{suffix}@example.test','password':'TestSicura1234'})
            self.assertEqual(status,201)
        tokens=[self.login('parallel_a@example.test','TestSicura1234'),self.login('parallel_b@example.test','TestSicura1234')]
        with connection(self.db) as db:
            used=db.execute('SELECT COALESCE(SUM(seats),0) FROM bookings WHERE event_id=1 AND status="confirmed"').fetchone()[0]
            db.execute('UPDATE events SET capacity=? WHERE id=1',(used+1,))
        def book(token):
            return self.api('POST','/api/bookings',{'event_id':1,'seats':1},token)[0]
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses=list(executor.map(book,tokens))
        self.assertEqual(sorted(statuses),[201,409])
        e=self.api('GET','/api/events/1')[1]['event']
        self.assertEqual(e['available'],0)

if __name__=='__main__':unittest.main()
