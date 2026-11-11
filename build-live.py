#!/usr/bin/env python3
"""Build the live GitHub Pages version from the demo artifact (rally-night.html).
Adds: full HTML head + PWA meta, Firebase Realtime Database sync, group PIN gate, admin PIN gate."""
import re, sys
import os; HERE=os.path.dirname(os.path.abspath(__file__)); SRC=os.path.join(HERE,'rally-night.html'); OUT=os.path.join(HERE,'index.html')
s=open(SRC).read()

FIREBASE = {
  "apiKey": "AIzaSyBoLJ8B69UYz-eQ2FhmXg5-RxT9iDVAak4",
  "authDomain": "pickleball-4d0c4.firebaseapp.com",
  "databaseURL": "https://pickleball-4d0c4-default-rtdb.firebaseio.com",
  "projectId": "pickleball-4d0c4",
  "appId": "1:800379995116:web:9d7a435ae762cb1f5f36c9",
}
import json
cfg=json.dumps(FIREBASE)

head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0f1a22">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Pickle">
<meta property="og:title" content="Pickle · Tuesday night sign-up">
<meta property="og:description" content="Tap your name if you're in.">
<meta property="og:image" content="https://devingalvin.github.io/Pickleball/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:url" content="https://devingalvin.github.io/Pickleball/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="apple-touch-icon-v2.png">
<link rel="icon" href="icon-192-v2.png">
<style>[hidden]{{display:none!important}}img{{max-width:100%}}</style>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-database-compat.js"></script>
</head>
<body>
'''
# the demo file starts with <title>; everything in it is body content
s = s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')

# status pill + PIN sheet + connecting overlay markup, inserted before the toast
extra_markup = '''<div class="sheet" id="pinSheet" hidden>
  <div class="card">
    <div class="row"><h2 id="pinTitle">Group PIN</h2><button class="ghost" id="pinClose">Cancel</button></div>
    <p class="hint" id="pinHint">Anyone with the link can watch. Scoring needs the group PIN, once per phone. Don't have it? Ask the group.</p>
    <label class="field"><span class="eyebrow" id="pinLabel">PIN</span><input id="pinInput" inputmode="numeric" pattern="[0-9]*" maxlength="5" autocomplete="one-time-code" placeholder="5 digits"></label>
    <p class="err" id="pinErr"></p>
    <button class="cta" id="pinGo">Unlock scoring</button>
  </div>
</div>
<div class="sheet" id="connecting"><div class="card" style="border-radius:20px;margin:auto;text-align:center"><h2>Connecting…</h2><p class="hint" id="connHint">Loading the league.</p></div></div>
<div class="toast" id="toast" hidden></div>'''
s = s.replace('<div class="toast" id="toast" hidden></div>', extra_markup, 1)

# status dot in the header
assert '<div class="date" id="hdrDate"></div></div>' in s, 'header slot missing'
s = s.replace('<div class="date" id="hdrDate"></div></div>', '<div class="date" id="hdrDate"></div><span class="sync" id="sync" title="Live"></span></div>', 1)
# (.sync and #connecting styles live in rally-night.html so this file never depends on the header's CSS text)

sync_js = '''// ---------- live sync (Firebase Realtime Database) ----------
// Safety: the live build only talks to the league database when served from the real site. Opened from disk or
// anywhere else (a local test, a headless browser), it runs on the demo data and never writes. This exists because
// a screenshot test once started a night for the whole group.
const LIVE = location.hostname==='devingalvin.github.io';
// Two tiers (see RULES.md). Group PIN: check in, score tonight, end the night. Admin PIN: fix or delete saved games,
// delete nights, rename/remove players, season settings. Off the live host, ?admin=0 previews the non-admin view.
let ADMIN=null, ADMIN_NAME=null; try{ ADMIN=localStorage.getItem('pickle-admin'); ADMIN_NAME=localStorage.getItem('pickle-admin-name'); }catch(e){}
if(!LIVE){ ADMIN=/[?&]admin=0/.test(location.search)?null:'demo'; ADMIN_NAME='Devin'; }
function admin(){ return !!ADMIN; } function adminName(){ return ADMIN_NAME||'Admin'; }
function adminUI(){ const b=$('#adminLink'); b.hidden=false; b.textContent=admin()?`Admin: ${adminName()}`:'Wrong score? Admin unlock'; }
if(!LIVE){ $('#connecting').hidden=true; const h=(location.hash||'#tonight').slice(1); show(['tonight','season','bracket','history'].includes(h)?h:'tonight', null); console.warn('Pickle: not on the live host, running offline on demo data'); }
else firebase.initializeApp(''' + cfg + ''');
const stubRef={ on(){}, set(){ return Promise.resolve(); }, update(){ return Promise.resolve(); }, child(){ return stubRef; }, once(){ return Promise.resolve({val:()=>null}); } };
const fdb = LIVE ? firebase.database() : { ref:()=>stubRef }; const leagueRef = fdb.ref('league'); const dataRef = fdb.ref('league/data'); const pinRef = fdb.ref('pin');
// Security model (see RULES.md): /league/data is readable by anyone with the link. Every write is one update that
// carries a fresh /league/k: "<PIN>:<nonce>" for the group, "A<ADMIN PIN>:<nonce>" for an admin, plus only the parts
// of the league that changed. The rules check k against /pin and /admin (which nobody can read) and decide per part:
// tonight, the roster and a brand-new night take either PIN; changing or deleting a saved night, seasons and pairing
// take the admin PIN. k must differ from the last one, so a saved token can't be replayed.
let PIN=null; try{ PIN=localStorage.getItem('pickle-pin'); }catch(e){}
const nonce=()=>Date.now().toString(36)+Math.random().toString(36).slice(2,6);
const token=adm=>adm? 'A'+ADMIN+':'+nonce() : PIN+':'+nonce();
let applying=false, loaded=false, lastWrite=null, blocked=false; // blocked: nothing to sync against; never write demo data over the league
let base=null; // what the server holds, part by part, as of the last sync
const J=JSON.stringify;
function parts(){ const s=snapshotState(); return { snap:s, players:J(s.players), tonight:J(s.tonight), seasons:J(s.seasons), pairing:J(s.pairing), nights:s.nights.map(n=>J(n)) }; }
function resync(){ dataRef.once('value').then(s=>{ if(s.val()) applyRemote(s.val()); }).catch(()=>{}); }
function snapshotState(){
  return { v:1, players:PLAYERS, seasons:state.seasons, pairing:state.pairing, nights:state.nights,
    tonight:{ date:state.tonight.date, present:[...state.tonight.present], started:state.tonight.started, games:state.tonight.games, current:state.tonight.current||null, courts:state.tonight.courts||1, scorer:state.tonight.scorer||null, late:[...lateSet()].filter(p=>state.tonight.present.has(p)), credit:credits() },
    updatedAt: Date.now() };
}
function persist(){
  if(applying||!loaded||blocked) return;
  if(!PIN&&!ADMIN){ unlocked=false; openPin('That change needs the group PIN.'); return; }
  const z=parts(), b=base||{nights:[]}, u={}; let needAdmin=false;
  if(z.players!==b.players) u['data/players']=z.snap.players;
  if(z.tonight!==b.tonight) u['data/tonight']=z.snap.tonight;
  if(z.seasons!==b.seasons){ u['data/seasons']=z.snap.seasons; needAdmin=true; }
  if(z.pairing!==b.pairing){ u['data/pairing']=z.snap.pairing; needAdmin=true; }
  // saved nights: adding one at the end is open to the group (End night); touching an existing one is an admin write
  if(z.nights.length>=b.nights.length && b.nights.every((x,i)=>x===z.nights[i])){ for(let i=b.nights.length;i<z.nights.length;i++) u['data/nights/'+i]=z.snap.nights[i]; }
  else { u['data/nights']=z.snap.nights; needAdmin=true; }
  if(!Object.keys(u).length) return;
  if(needAdmin&&!ADMIN){ resync(); openAdmin('That change needs the admin code.'); return; }
  const adm=needAdmin||!PIN; lastWrite=z.snap.updatedAt; u['data/updatedAt']=lastWrite; u.k=token(adm); base=z;
  leagueRef.update(u).catch(e=>{
    resync(); // put this phone back on what the league actually holds
    if(String(e.code||e.message).includes('PERMISSION')){
      if(adm){ ADMIN=null; ADMIN_NAME=null; try{ localStorage.removeItem('pickle-admin'); localStorage.removeItem('pickle-admin-name'); }catch(_){} openAdmin('Admin code did not work on this phone. Enter it again and redo that last change.'); }
      else { PIN=null; unlocked=false; try{ localStorage.removeItem('pickle-pin'); localStorage.removeItem('pickle-unlocked'); }catch(_){} openPin('Wrong PIN on this phone. Enter it again and redo that last change.'); } }
    else toast('Save failed: '+(e.code||e.message)); $('#sync').className='sync off'; });
}
function applyRemote(d){
  if(!d) return;
  applying=true;
  try{
    PLAYERS = d.players||[]; state.seasons = d.seasons||[]; state.pairing = d.pairing||'split';
    state.nights = (d.nights||[]).map(n=>({date:n.date, season:n.season, games:n.games||[]}));
    state.nights.forEach(n=>n.games.forEach(g=>{ g.a=g.a||[]; g.b=g.b||[]; }));
    const t=d.tonight||{}; state.tonight = { date:t.date, present:new Set(t.present||[]), started:!!t.started, games:t.games||[], current:normCur(t.current), courts:t.courts===2?2:1, scorer:(t.scorer&&t.scorer.id)?t.scorer:null, late:new Set(t.late||[]), credit:(t.credit||[]).filter(c=>c&&c.p) };
    if(state.tonight.current) state.tonight.current.forEach(g=>{ g.a=g.a||[]; g.b=g.b||[]; });
    state.tonight.games.forEach(g=>{ g.a=g.a||[]; g.b=g.b||[]; });
    base=parts();
    if(state.tab) show(state.tab, state.sub);
  } finally { applying=false; }
}
const startView=()=>{ const h=(location.hash||'#tonight').slice(1); show(['tonight','season','bracket','history'].includes(h)?h:'tonight', null); };
dataRef.on('value', snap=>{
  const d=snap.val();
  if(!loaded){
    loaded=true; $('#connecting').hidden=true;
    if(d){ applyRemote(d); startView(); return; }
    // nothing at /league/data: don't guess, and never write demo data over a league we couldn't read
    blocked=true; startView(); toast('No league data found. Nothing will be saved.');
    return;
  }
  if(d && d.updatedAt===lastWrite) return; // our own write echoed back
  const sheetOpen=!$('#sheet').hidden;
  applyRemote(d);
  const pg=state.pending && normCur(state.tonight.current)?.[state.pending.idx];
  if(sheetOpen && (!pg || scored(pg))){ hideSheet('#sheet'); state.pending=null; toast('Someone else just scored that game'); }
}, err=>{ $('#connHint').textContent='Could not reach the league database. Check your connection and reload.'; $('#sync').className='sync off'; });
fdb.ref('.info/connected').on('value', s=>{ $('#sync').className='sync '+(s.val()?'on':'off'); });
$('#sync').onclick=()=>{ const c=$('#sync').className; toast(c.includes('on')?'Live. Everyone sees the same thing.':c.includes('off')?'Offline. Changes save here and sync when you reconnect.':'Connecting…'); };
$('#sync').style.cssText+='width:14px;height:14px;margin:-3px;cursor:pointer;background-clip:content-box;padding:3px;';
setTimeout(()=>{ if(!loaded) $('#connHint').textContent='Still connecting. If this hangs, the database may not be set up yet.'; }, 8000);

// ---------- group PIN gate ----------
const EDIT_SEL='#roster,#courtsSeg,#startBtn,#acts .gated,.changeBtn,#undoBtn,.scorebtn,#endNight,#addConfirm,#newName,#courts .matchup,#lateBtn,.latehere'; // admin-only controls aren't here: they don't render without the admin PIN
let unlocked=false; try{ unlocked=localStorage.getItem('pickle-unlocked')==='1'; }catch(e){}
let pinOnServer=undefined; pinRef.once('value').then(s=>{ pinOnServer=s.val()||null; }).catch(()=>{ pinOnServer='hidden'; }); // 'hidden' = new rules in place
if(ADMIN) unlocked=true; else if(!PIN) unlocked=false; // an admin can do everything the group can; an old "unlocked" flag without a PIN is not enough
document.addEventListener('click', e=>{
  if(unlocked) return; const t=e.target.closest(EDIT_SEL); if(!t) return;
  e.stopPropagation(); e.preventDefault(); openPin();
}, true);
document.addEventListener('focusin', e=>{ if(!unlocked && e.target.closest(EDIT_SEL)){ e.target.blur(); openPin(); } }, true);
document.addEventListener('pointerdown', e=>{ if(!unlocked && e.target.closest('#courts .matchup')){ e.stopPropagation(); } }, true);
let pinMode='group';
// one sheet, two inputs: digits for the group PIN, a word for the admin code (not case sensitive)
function pinField(adminMode){ const i=$('#pinInput'); $('#pinLabel').textContent=adminMode?'Code':'PIN';
  if(adminMode){ i.setAttribute('inputmode','text'); i.removeAttribute('pattern'); i.maxLength=24; i.placeholder='Admin code'; i.setAttribute('autocomplete','off'); i.setAttribute('autocapitalize','none'); i.setAttribute('autocorrect','off'); i.spellcheck=false; }
  else { i.setAttribute('inputmode','numeric'); i.setAttribute('pattern','[0-9]*'); i.maxLength=5; i.placeholder='5 digits'; i.setAttribute('autocomplete','one-time-code'); } }
function openAdmin(msg){
  pinMode='admin'; pinField(true); if(msg) setTimeout(()=>{ $('#pinErr').textContent=msg; },60);
  $('#pinTitle').textContent='Admin code';
  $('#pinHint').textContent='Admins can fix or delete saved scores, delete a night, edit the roster and run the season. Once per phone.';
  $('#pinGo').textContent='Unlock admin';
  $('#pinInput').value=''; $('#pinErr').textContent=''; showSheet('#pinSheet'); setTimeout(()=>$('#pinInput').focus(),50);
}
function lockAdmin(){ ADMIN=null; ADMIN_NAME=null; try{ localStorage.removeItem('pickle-admin'); localStorage.removeItem('pickle-admin-name'); }catch(_){} if(!PIN) unlocked=false; show(state.tab,state.sub); toast('Admin locked on this phone'); }
$('#adminLink').onclick=()=>{ if(admin()) actionSheet('Admin',`${adminName()} can fix scores on this phone`,[{label:'Lock admin on this phone',run:lockAdmin}]); else openAdmin(); };
function tryAdmin(v){
  $('#pinErr').textContent='Checking…';
  leagueRef.child('k').set('A'+v+':'+nonce()).then(()=>{
    ADMIN=v; unlocked=true; try{ localStorage.setItem('pickle-admin',v); }catch(e){} hideSheet('#pinSheet'); show(state.tab,state.sub);
    // the name goes on every score this phone corrects
    const pick=p=>{ ADMIN_NAME=p; try{ localStorage.setItem('pickle-admin-name',p); }catch(e){} show(state.tab,state.sub); toast(`Admin unlocked for ${p}`); };
    setTimeout(()=>actionSheet('Admin unlocked','Who are you?',PLAYERS.map(p=>({label:p,run:()=>pick(p)}))),250);
  }).catch(()=>{ $('#pinErr').textContent='Wrong admin code.'; });
}
function openPin(msg){
  pinMode='group'; pinField(false); const creating = pinOnServer===null;
  if(msg) setTimeout(()=>{ $('#pinErr').textContent=msg; },60);
  $('#pinTitle').textContent = creating?'Set the group PIN':'Group PIN';
  $('#pinHint').textContent = creating?'No PIN yet. Pick 5 digits and share it with the group. Anyone with the link can watch; scoring needs the PIN.':'Anyone with the link can watch. Scoring needs the group PIN, once per phone. Don\\'t have it? Ask the group.';
  $('#pinGo').textContent = creating?'Set PIN & unlock':'Unlock scoring';
  $('#pinInput').value=''; $('#pinErr').textContent=''; showSheet('#pinSheet'); setTimeout(()=>$('#pinInput').focus(),50);
}
$('#pinClose').onclick=()=>{ hideSheet('#pinSheet'); };
function tryPin(){
  if(pinMode==='admin'){ const c=$('#pinInput').value.trim().toLowerCase(); if(c.length<3||c.includes(':')){ $('#pinErr').textContent='Enter the admin code.'; return; } tryAdmin(c); return; }
  const v=$('#pinInput').value.trim();
  if(!/^\\d{5}$/.test(v)){ $('#pinErr').textContent='Exactly 5 digits.'; return; }
  const done=()=>{ PIN=v; unlocked=true; try{ localStorage.setItem('pickle-pin',v); localStorage.setItem('pickle-unlocked','1'); }catch(e){} hideSheet('#pinSheet'); toast('Scoring unlocked on this phone'); };
  const wrong=()=>{ $('#pinErr').textContent='Wrong PIN. Ask the group.'; };
  if(pinOnServer===null){ pinRef.set(v).then(done).catch(()=>{ $('#pinErr').textContent='Could not save the PIN.'; }); }
  else if(pinOnServer==='hidden'||pinOnServer===undefined){ $('#pinErr').textContent='Checking…'; leagueRef.child('k').set(v+':'+nonce()).then(done).catch(wrong); }
  else if(v===String(pinOnServer)) done();
  else wrong();
}
$('#pinGo').onclick=tryPin; $('#pinInput').addEventListener('keydown',e=>{ if(e.key==='Enter') tryPin(); });
'''

# replace the no-op hook and the startup lines
HOOK = "// ---------- persistence + admin hooks (no-ops in the demo; the live build replaces them) ----------\nfunction persist(){}\nfunction admin(){ return true; } function adminName(){ return 'Devin'; } function adminUI(){}\n"
assert HOOK in s, 'hook block missing'
s = s.replace(HOOK, sync_js, 1)
startup = "const h=(location.hash||'#tonight').slice(1); show(['tonight','season','bracket','history'].includes(h)?h:'tonight', null);\n"
assert startup in s
s = s.replace(startup, "// startup happens once the league loads (see live sync above)\n", 1)

# ---------- build stamp + update bar ----------
# version.json carries the stamp of the deployed build; the app polls it and offers a reload when it's behind,
# so a home-screen install doesn't sit on last week's version until someone force-quits it.
import hashlib
BUILD = hashlib.sha1(s.encode()).hexdigest()[:8]
update_markup = '''<div class="updatescrim" id="updateScrim" hidden></div><button class="updatebar" id="updateBar" hidden>New version ready · Tap to update</button>'''
update_css = '''.updatebar{position:fixed;left:16px;width:calc(100% - 32px);bottom:calc(env(safe-area-inset-bottom) + 84px);z-index:60;min-height:44px;border-radius:12px;border:0;background:var(--ball);color:var(--ball-ink);font-weight:700;font-size:14px;box-shadow:0 8px 24px rgba(0,0,0,.4);animation:updateIn .3s both}
@keyframes updateIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.updatescrim{position:fixed;inset:0;z-index:59;background:rgba(6,12,16,.72);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px);animation:fadeIn .25s both}'''
update_js = '''
const BUILD='%s';
let dismissedBuild=null;
function showUpdate(on){ $('#updateBar').hidden=!on; $('#updateScrim').hidden=!on; }
async function checkBuild(){ try{ const r=await fetch('version.json?t='+Date.now(),{cache:'no-store'}); const j=await r.json(); if(j.build&&j.build!==BUILD&&j.build!==dismissedBuild){ latestBuild=j.build; showUpdate(true); } }catch(_){} }
let latestBuild=null;
$('#updateBar').onclick=async()=>{ $('#updateBar').textContent='Updating…'; try{ await fetch('index.html',{cache:'reload'}); }catch(_){} location.reload(); };
$('#updateScrim').onclick=()=>{ dismissedBuild=latestBuild; showUpdate(false); }; // tap outside to carry on with this version for now
setInterval(checkBuild, 5*60*1000); document.addEventListener('visibilitychange',()=>{ if(!document.hidden) checkBuild(); }); setTimeout(checkBuild, 4000);
''' % BUILD
s = s.replace('<div class="toast" id="toast" hidden></div>', update_markup + '\n<div class="toast" id="toast" hidden></div>', 1)
s = s.replace('</style>', update_css + '\n</style>', 1)
s = s.replace('</script>', update_js + '</script>')  # last script block in the body
open(os.path.join(HERE,'version.json'),'w').write('{"build":"%s"}\n' % BUILD)

out = head + s + '\n</body>\n</html>\n'
open(OUT,'w').write(out)
print('built', len(out), 'bytes')
