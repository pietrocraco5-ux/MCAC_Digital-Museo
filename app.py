"""Adapter Flask facoltativo. Il core applicativo coincide con server.py.
Per provarlo senza installare Flask: python server.py
"""
from flask import Flask,request,jsonify,send_from_directory
from core import ROOT,handle,MAX_BODY
from seed import seed

app=Flask(__name__,static_folder=str(ROOT/'static'),static_url_path='')
app.config['MAX_CONTENT_LENGTH']=MAX_BODY
seed()

@app.route('/')
def home(): return send_from_directory(str(ROOT/'static'),'index.html')

@app.route('/api/<path:path>',methods=['GET','POST','DELETE'])
def api(path):
    data=request.get_json(silent=True) or {}
    status,result=handle(request.method,'/api/'+path,data,request.headers.get('Authorization'))
    return jsonify(result),status,{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=False)
