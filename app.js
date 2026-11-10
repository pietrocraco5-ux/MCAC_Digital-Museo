/* MCAC Digital: client-side SPA, API JSON, nessun servizio esterno. */
const state={page:'home',user:null,token:sessionStorage.getItem('mcac_token')||'',works:[],events:[],bookings:[]};
const $=id=>document.getElementById(id);
const esc=t=>String(t??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function notify(message,error=false){const t=$('toast');t.textContent=message;t.className=(error?'error ':'')+'visible';clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.className='',4000)}
async function api(path,options={}){
  let headers={'Content-Type':'application/json',...(options.headers||{})};
  if(state.token)headers.Authorization='Bearer '+state.token;
  let response;
  try{response=await fetch('/api'+path,{...options,headers});}catch(e){throw new Error('Server non raggiungibile. Avvia python server.py.');}
  let body=await response.json();if(!response.ok)throw new Error(body.error||'Errore nella richiesta');return body;
}
function closeModal(){$('modal').classList.add('hidden');$('modal-inner').innerHTML=''}
function showModal(html){$('modal-inner').innerHTML=html;$('modal').classList.remove('hidden');}
function field(label,name,type='text',attr='required'){return `<div class="form-field"><label for="f_${name}">${esc(label)}</label><input id="f_${name}" name="${esc(name)}" type="${type}" ${attr}></div>`}
function status(msg){notify(msg,false)}
function updateNav(){
  $('user-label').textContent=state.user?state.user.name:'';
  $('login-open').classList.toggle('hidden',!!state.user);
  $('logout').classList.toggle('hidden',!state.user);
  $('admin-nav').classList.toggle('hidden',!state.user||state.user.role!=='admin');
}
function goto(page){if(page==='dashboard'&&state.user?.role!=='admin'){notify('Area riservata agli amministratori.',true);return;}
  state.page=page;
  document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id==='page-'+page));
  document.querySelectorAll('nav .nav-link').forEach(x=>x.classList.toggle('active',x.dataset.page===page));
  if(page==='bookings')loadBookings();if(page==='dashboard')loadDashboard();
  window.scrollTo({top:0,behavior:'instant'});
}
function loginModal(mode='login'){
  const isRegister=mode==='register';
  showModal(`<h2>${isRegister?'Crea il tuo account':'Bentornato!'}</h2><p>${isRegister?'Registrati per prenotare eventi e visite.':'Accedi per gestire prenotazioni e feedback.'}</p>
    <form id="auth-form">${isRegister?field('Nome e cognome','name'):''}${field('Email','email','email')}${field('Password (minimo 10 caratteri)','password','password')}
    <button type="submit" class="btn btn-primary">${isRegister?'Registrati':'Accedi'}</button></form>
    <p class="smallnote">Account dimostrativi: admin@mcac.test oppure visitatore@mcac.test<br>Password: Demo2026!sicura</p>
    <button class="link-button" id="auth-switch">${isRegister?'Hai già un account? Accedi':'Non hai un account? Registrati'}</button>`);
  $('auth-switch').onclick=()=>loginModal(isRegister?'login':'register');
  $('auth-form').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));try{
    if(isRegister){await api('/register',{method:'POST',body:JSON.stringify(v)});status('Account creato. Ora puoi accedere.');loginModal();return;}
    let out=await api('/login',{method:'POST',body:JSON.stringify(v)});state.token=out.token;state.user=out.user;
    sessionStorage.setItem('mcac_token',state.token);updateNav();closeModal();status('Accesso effettuato.');
    if(state.page==='bookings')loadBookings();if(state.page==='dashboard')loadDashboard();
  }catch(err){notify(err.message,true)}};
}
function formatDate(s){return new Date(s).toLocaleString('it-IT',{day:'2-digit',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit'})}
function workCard(w,i){let palette=['blue','orange',''];return `<article class="item-card"><div class="art-thumb ${palette[i%3]}" role="img" aria-label="Segnaposto grafico astratto dell'opera"></div><div class="card-body"><span class="card-type">${esc(w.category)} · ${esc(w.room)}</span><h3>${esc(w.title)}</h3><p>${esc(w.description)}</p><div class="card-meta"><span>${esc(w.author)}</span><strong>${esc(w.year)}</strong></div></div></article>`}
function eventCard(e,i){const full=e.available<=0;return `<article class="item-card"><div class="art-thumb ${i%2?'orange':'blue'}" role="img" aria-label="Illustrazione astratta dell'evento"></div><div class="card-body"><span class="card-type">${esc(e.kind)}</span><h3>${esc(e.title)}</h3><p>${esc(e.description)}</p><div class="card-meta"><span>${esc(formatDate(e.starts_at))}</span><span class="pill ${full?'full':''}">${full?'Esaurito':e.available+' posti'}</span></div><button class="btn btn-primary" data-book="${e.id}" ${full?'disabled':''}>${full?'Posti esauriti':'Prenota una visita →'}</button></div></article>`}
function renderWorks(){const q=$('work-search').value.toLowerCase(),cat=$('work-category').value;
  const items=state.works.filter(w=>(!cat||w.category===cat)&&[w.title,w.author,w.room].join(' ').toLowerCase().includes(q));
  $('work-grid').innerHTML=items.map(workCard).join('')||'<div class="empty">Nessuna opera trovata.</div>';
}
function renderEvents(){const q=$('event-search').value.toLowerCase(),kind=$('event-kind').value;
  const items=state.events.filter(e=>e.status==='active'&&(!kind||kind===e.kind)&&[e.title,e.description].join(' ').toLowerCase().includes(q));
  $('event-grid').innerHTML=items.map(eventCard).join('')||'<div class="empty">Nessun evento trovato.</div>';
  document.querySelectorAll('[data-book]').forEach(b=>b.onclick=()=>bookingModal(Number(b.dataset.book)));
}
function bookingModal(id){const event=state.events.find(e=>e.id===id);if(!event)return;
 if(!state.user){loginModal();notify('Accedi per prenotare.');return;}
 showModal(`<h2>Prenota il tuo posto</h2><p><b>${esc(event.title)}</b><br>${esc(formatDate(event.starts_at))}<br>Disponibilità: ${event.available} posti</p>
 <form id="booking-form">${field('Numero partecipanti (1–6)','seats','number','required min="1" max="6" value="1"')}<button class="btn btn-primary" type="submit">Conferma prenotazione</button></form>`);
 $('booking-form').onsubmit=async e=>{e.preventDefault();const seats=Number(new FormData(e.target).get('seats'));try{
   await api('/bookings',{method:'POST',body:JSON.stringify({event_id:id,seats})});
   closeModal();status('Prenotazione confermata!');await loadEvents();
 }catch(err){notify(err.message,true)}};
}
async function loadWorks(){const d=await api('/works');state.works=d.items;
 const categories=[...new Set(state.works.map(w=>w.category))].sort();$('work-category').innerHTML='<option value="">Tutte le categorie</option>'+categories.map(v=>`<option>${esc(v)}</option>`).join('');renderWorks()}
async function loadEvents(){const d=await api('/events');state.events=d.items;
 const kinds=[...new Set(state.events.map(w=>w.kind))].sort();const old=$('event-kind').value;
 $('event-kind').innerHTML='<option value="">Tutte le tipologie</option>'+kinds.map(v=>`<option>${esc(v)}</option>`).join('');$('event-kind').value=old;renderEvents()}
async function loadBookings(){if(!state.user){$('booking-content').innerHTML='<div class="notice"><strong>Accedi alla tua area personale.</strong><p>Per vedere e gestire le prenotazioni devi effettuare il login.</p><button class="btn btn-primary" id="booking-login">Accedi</button></div>';$('booking-login').onclick=()=>loginModal();return;}
 try{const d=await api('/bookings');state.bookings=d.items;const rows=d.items.map(b=>`<tr><td>${esc(b.event_title)}</td><td>${esc(formatDate(b.starts_at))}</td><td>${b.seats}</td><td><span class="pill ${b.status==='cancelled'?'full':''}">${b.status==='confirmed'?'Confermata':'Cancellata'}</span></td><td><div class="row-actions">${b.status==='confirmed'?`<button class="btn btn-light" data-feedback="${b.event_id}">Valuta</button><button class="btn btn-danger" data-cancel="${b.id}">Cancella</button>`:''}</div></td></tr>`).join('');
 $('booking-content').innerHTML=d.items.length?`<table class="data-table"><thead><tr><th>Evento</th><th>Quando</th><th>Posti</th><th>Stato</th><th>Azioni</th></tr></thead><tbody>${rows}</tbody></table>`:'<div class="empty">Non hai ancora effettuato prenotazioni.</div>';
 document.querySelectorAll('[data-cancel]').forEach(b=>b.onclick=async()=>{if(!confirm('Vuoi cancellare questa prenotazione?'))return;try{await api('/bookings/'+b.dataset.cancel,{method:'DELETE'});status('Prenotazione cancellata.');await loadBookings();await loadEvents()}catch(e){notify(e.message,true)}});
 document.querySelectorAll('[data-feedback]').forEach(b=>b.onclick=()=>feedbackModal(Number(b.dataset.feedback)));
 }catch(e){notify(e.message,true)}}
function feedbackModal(event_id){showModal(`<h2>La tua esperienza</h2><p>Come valuti il servizio del museo? Il feedback è collegato alla tua prenotazione.</p><form id="feedback-form"><div class="form-field"><label for="f_rating">Valutazione</label><select id="f_rating" name="rating"><option value="5">5 - Eccellente</option><option value="4">4 - Molto buona</option><option value="3">3 - Buona</option><option value="2">2 - Sufficiente</option><option value="1">1 - Da migliorare</option></select></div><div class="form-field"><label for="f_comment">Commento (facoltativo)</label><textarea id="f_comment" name="comment" maxlength="500"></textarea></div><button class="btn btn-primary">Invia feedback</button></form>`);
 $('feedback-form').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));try{await api('/feedback',{method:'POST',body:JSON.stringify({event_id,rating:Number(v.rating),comment:v.comment})});closeModal();status('Feedback inviato.')}catch(err){notify(err.message,true)}}}
function dashboardHTML(d){const stats=[['Utenti',d.users],['Opere',d.works],['Eventi',d.events],['Prenotazioni',d.bookings],['Posti prenotati',d.seats_booked],['Tasso occupazione',d.occupancy_percent+'%'],['Feedback',d.feedback_count],['Valutazione media',d.rating_mean===null?'—':d.rating_mean+'/5']];
 let bars=d.by_event.map(x=>`<div class="bar-row"><span class="bar-label" title="${esc(x.title)}">${esc(x.title)}</span><span class="bar-track"><span class="bar-fill" style="display:block;width:${Math.max(0,Math.min(100,x.occupancy_percent))}%"></span></span><span class="bar-val">${x.occupancy_percent}%</span></div>`).join('');
 let dist=Object.entries(d.rating_distribution).reverse().map(([rating,n])=>`<div class="bar-row"><span class="bar-label" style="width:35px">${rating} ★</span><span class="bar-track"><span class="bar-fill" style="display:block;width:${d.feedback_count?100*n/d.feedback_count:0}%"></span></span><span class="bar-val">${n}</span></div>`).join('');
 return `<div class="metrics">${stats.map(([l,v])=>`<div class="metric"><span>${esc(l)}</span><b>${esc(v)}</b></div>`).join('')}</div><div class="dashboard-panels"><div class="panel"><h3>Occupazione per evento</h3>${bars}</div><div class="panel"><h3>Distribuzione delle valutazioni</h3>${dist}</div></div>
 <div class="dashboard-panels"><div class="panel"><h3>Nuovo evento</h3><form id="event-create">${field('Titolo','title')}${field('Tipologia','kind')}${field('Data e ora','starts_at','datetime-local')}${field('Durata (minuti)','duration_minutes','number','required min="15" max="600" value="90"')}${field('Capienza','capacity','number','required min="1" max="500" value="30"')}${field('Descrizione','description')}<button class="btn btn-primary">Aggiungi evento</button></form></div><div class="panel"><h3>Nuova opera</h3><form id="work-create">${field('Titolo','title')}${field('Autore','author')}${field('Anno','year','number','required value="1900"')}${field('Categoria','category')}${field('Sala','room')}${field('Descrizione','description')}<button class="btn btn-primary">Aggiungi opera</button></form></div></div>`;
}
async function loadDashboard(){if(state.user?.role!=='admin')return;
 try{const d=await api('/dashboard');$('dashboard-content').innerHTML=dashboardHTML(d);
 $('event-create').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));v.duration_minutes=Number(v.duration_minutes);v.capacity=Number(v.capacity);try{await api('/events',{method:'POST',body:JSON.stringify(v)});notify('Evento inserito.');await loadEvents();await loadDashboard()}catch(x){notify(x.message,true)}};
 $('work-create').onsubmit=async e=>{e.preventDefault();const v=Object.fromEntries(new FormData(e.target));v.year=Number(v.year);try{await api('/works',{method:'POST',body:JSON.stringify(v)});notify('Opera inserita.');await loadWorks();await loadDashboard()}catch(x){notify(x.message,true)}};
 }catch(e){notify(e.message,true)}}
async function boot(){
 document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>goto(b.dataset.page)));
 $('login-open').onclick=()=>loginModal();$('logout').onclick=async()=>{try{await api('/logout',{method:'POST'})}catch(e){}state.token='';state.user=null;sessionStorage.removeItem('mcac_token');updateNav();goto('home');notify('Sessione terminata.')};
 $('modal-close').onclick=closeModal;$('modal').onclick=e=>{if(e.target===$('modal'))closeModal()};
 $('work-search').oninput=renderWorks;$('work-category').onchange=renderWorks;$('event-search').oninput=renderEvents;$('event-kind').onchange=renderEvents;
 if(state.token){try{state.user=(await api('/me')).user}catch(e){state.token='';sessionStorage.removeItem('mcac_token')}}
 updateNav();
 try{await Promise.all([loadWorks(),loadEvents()])}catch(e){notify('Impossibile caricare i dati: '+e.message,true)}
}
document.addEventListener('DOMContentLoaded',boot);
