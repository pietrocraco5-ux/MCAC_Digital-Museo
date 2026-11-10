"""Server locale pronto senza dipendenze, che usa le stesse API di Flask."""
import json
import mimetypes
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from core import handle,MAX_BODY,ROOT
from seed import seed

class Handler(BaseHTTPRequestHandler):
    def send_json(self,status,obj):
        raw=json.dumps(obj,ensure_ascii=False).encode('utf8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(raw)
    def route(self):
        path=urlsplit(self.path).path
        if path.startswith('/api/'):
            raw=b''
            if self.command in ('POST','PUT','PATCH'):
                try: size=int(self.headers.get('Content-Length','0'))
                except ValueError: size=MAX_BODY+1
                if size>MAX_BODY or size<0:return self.send_json(413,{'error':'Richiesta troppo grande.'})
                raw=self.rfile.read(size)
            try: data=json.loads(raw) if raw else {}
            except (ValueError,UnicodeDecodeError):return self.send_json(400,{'error':'JSON non valido.'})
            status,result=handle(self.command,path,data,self.headers.get('Authorization'))
            return self.send_json(status,result)
        if self.command!='GET':return self.send_json(405,{'error':'Metodo non supportato.'})
        files={'/':'index.html','/index.html':'index.html','/style.css':'style.css','/app.js':'app.js'}
        filename=files.get(path)
        if not filename:return self.send_json(404,{'error':'Risorsa non trovata.'})
        p=ROOT/'static'/filename
        buf=p.read_bytes();mime=mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
        self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8')
        self.send_header('Content-Length',str(len(buf)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(buf)
    def do_GET(self):self.route()
    def do_POST(self):self.route()
    def do_DELETE(self):self.route()

def run(port=5000):
    seed()
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'MCAC Digital - apri http://127.0.0.1:{port} (CTRL+C per uscire)',flush=True)
    server.serve_forever()
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=5000)
    run(p.parse_args().port)
