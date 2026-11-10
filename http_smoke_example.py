import json,urllib.request,urllib.error
from pathlib import Path
base='http://127.0.0.1:5088'
results=[]
def call(method,path,data=None,token=None):
 raw=json.dumps(data).encode() if data is not None else None
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(base+path,data=raw,headers=headers,method=method)
 try:
  with urllib.request.urlopen(req,timeout=10) as r:
   return r.status,json.loads(r.read().decode())
 except urllib.error.HTTPError as r:
  return r.code,json.loads(r.read().decode())
for path in ('/api/health','/api/works','/api/events'):
 status,payload=call('GET',path)
 results.append({'method':'GET','path':path,'http_status':status,'pass':status==200})
status,payload=call('POST','/api/login',{'email':'admin@mcac.test','password':'Demo2026!sicura'})
token=payload.get('token');results.append({'method':'POST','path':'/api/login','http_status':status,'pass':status==200 and bool(token)})
status,payload=call('GET','/api/dashboard',token=token)
results.append({'method':'GET','path':'/api/dashboard','http_status':status,'pass':status==200 and payload.get('bookings')==43})
status,payload=call('GET','/api/dashboard')
results.append({'method':'GET','path':'/api/dashboard (anonimo)','http_status':status,'pass':status==401})
status,payload=call('POST','/api/logout',{},token)
results.append({'method':'POST','path':'/api/logout','http_status':status,'pass':status==200})
status,payload=call('GET','/api/dashboard',token=token)
results.append({'method':'GET','path':'/api/dashboard (token revocato)','http_status':status,'pass':status==401})
out={'description':'Esecuzione reale richieste HTTP contro server standard locale, con dataset simulato','checks':results,'passed':sum(r['pass'] for r in results),'total':len(results)}
Path('/mnt/data/MCAC_Digital/results/http_smoke.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(json.dumps(out,indent=2,ensure_ascii=False))
assert all(x['pass'] for x in results)
