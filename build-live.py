#!/usr/bin/env python3
"""Build the live GitHub Pages version from the demo artifact (rally-night.html).
Adds: full HTML head + PWA meta, Firebase Realtime Database sync, group PIN gate."""
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
    <label class="field"><span class="eyebrow">PIN</span><input id="pinInput" inputmode="numeric" pattern="[0-9]*" maxlength="5" autocomplete="one-time-code" placeholder="5 digits"></label>
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
firebase.initializeApp(''' + cfg + ''');
const fdb = firebase.database(); const leagueRef = fdb.ref('league'); const pinRef = fdb.ref('pin');
let applying=false, loaded=false, lastWrite=null;
function snapshotState(){
  return { v:1, players:PLAYERS, seasons:state.seasons, pairing:state.pairing, nights:state.nights,
    tonight:{ date:state.tonight.date, present:[...state.tonight.present], started:state.tonight.started, games:state.tonight.games, current:state.tonight.current||null, courts:state.tonight.courts||1 },
    updatedAt: Date.now() };
}
function persist(){
  if(applying||!loaded) return;
  const snap=snapshotState(); lastWrite=snap.updatedAt;
  leagueRef.set(snap).catch(e=>{ toast('Save failed: '+(e.code||e.message)); $('#sync').className='sync off'; });
}
function applyRemote(d){
  if(!d) return;
  applying=true;
  try{
    PLAYERS = d.players||[]; state.seasons = d.seasons||[]; state.pairing = d.pairing||'split';
    state.nights = (d.nights||[]).map(n=>({date:n.date, season:n.season, games:n.games||[]}));
    state.nights.forEach(n=>n.games.forEach(g=>{ g.a=g.a||[]; g.b=g.b||[]; }));
    const t=d.tonight||{}; state.tonight = { date:t.date, present:new Set(t.present||[]), started:!!t.started, games:t.games||[], current:normCur(t.current), courts:t.courts===2?2:1 };
    if(state.tonight.current) state.tonight.current.forEach(g=>{ g.a=g.a||[]; g.b=g.b||[]; });
    state.tonight.games.forEach(g=>{ g.a=g.a||[]; g.b=g.b||[]; });
    if(state.tab) show(state.tab, state.sub);
  } finally { applying=false; }
}
leagueRef.on('value', snap=>{
  const d=snap.val();
  if(!loaded){
    loaded=true; $('#connecting').hidden=true;
    if(!d){ persist(); toast('League created from last Tuesday\\'s games'); const h=(location.hash||'#tonight').slice(1); show(['tonight','season','bracket','history'].includes(h)?h:'tonight', null); }
    else { applyRemote(d); const h=(location.hash||'#tonight').slice(1); show(['tonight','season','bracket','history'].includes(h)?h:'tonight', null); }
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
const EDIT_SEL='#roster,#courtsSeg,#startBtn,#acts .gated,.changeBtn,.rowedit,#undoBtn,.scorebtn,#endNight,#deleteNight,#seasonBtn,#addConfirm,#newName,#log .item,#nightLog .item,#courts .matchup';
let unlocked=false; try{ unlocked=localStorage.getItem('pickle-unlocked')==='1'; }catch(e){}
let pinOnServer=undefined; pinRef.on('value', s=>{ pinOnServer=s.val()||null; });
document.addEventListener('click', e=>{
  if(unlocked) return; const t=e.target.closest(EDIT_SEL); if(!t) return;
  e.stopPropagation(); e.preventDefault(); openPin();
}, true);
document.addEventListener('focusin', e=>{ if(!unlocked && e.target.closest(EDIT_SEL)){ e.target.blur(); openPin(); } }, true);
document.addEventListener('pointerdown', e=>{ if(!unlocked && e.target.closest('#log .item,#nightLog .item,#courts .matchup')){ e.stopPropagation(); } }, true);
function openPin(){
  const creating = pinOnServer===null;
  $('#pinTitle').textContent = creating?'Set the group PIN':'Group PIN';
  $('#pinHint').textContent = creating?'No PIN yet. Pick 5 digits and share it with the group. Anyone with the link can watch; scoring needs the PIN.':'Anyone with the link can watch. Scoring needs the group PIN, once per phone. Don\\'t have it? Ask the group.';
  $('#pinGo').textContent = creating?'Set PIN & unlock':'Unlock scoring';
  $('#pinInput').value=''; $('#pinErr').textContent=''; showSheet('#pinSheet'); setTimeout(()=>$('#pinInput').focus(),50);
}
$('#pinClose').onclick=()=>{ hideSheet('#pinSheet'); };
function tryPin(){
  const v=$('#pinInput').value.trim();
  if(!/^\\d{5}$/.test(v)){ $('#pinErr').textContent='Exactly 5 digits.'; return; }
  const done=()=>{ unlocked=true; try{ localStorage.setItem('pickle-unlocked','1'); }catch(e){} hideSheet('#pinSheet'); toast('Scoring unlocked on this phone'); };
  if(pinOnServer===null){ pinRef.set(v).then(done).catch(()=>{ $('#pinErr').textContent='Could not save the PIN.'; }); }
  else if(v===String(pinOnServer)) done();
  else $('#pinErr').textContent='Wrong PIN. Ask whoever runs the night.';
}
$('#pinGo').onclick=tryPin; $('#pinInput').addEventListener('keydown',e=>{ if(e.key==='Enter') tryPin(); });
'''

# replace the no-op hook and the startup lines
s = s.replace('// ---------- persistence hook (no-op in the demo; the live build replaces it) ----------\nfunction persist(){}\n', sync_js, 1)
startup = "const h=(location.hash||'#tonight').slice(1); show(['tonight','season','bracket','history'].includes(h)?h:'tonight', null);\n"
assert startup in s
s = s.replace(startup, "// startup happens once the league loads (see live sync above)\n", 1)

# ---------- build stamp + update bar ----------
# version.json carries the stamp of the deployed build; the app polls it and offers a reload when it's behind,
# so a home-screen install doesn't sit on last week's version until someone force-quits it.
import hashlib
BUILD = hashlib.sha1(s.encode()).hexdigest()[:8]
update_markup = '''<button class="updatebar" id="updateBar" hidden>New version ready · Tap to update</button>'''
update_css = '''.updatebar{position:fixed;left:16px;right:16px;bottom:calc(env(safe-area-inset-bottom) + 84px);z-index:60;min-height:44px;border-radius:12px;border:0;background:var(--ball);color:var(--ball-ink);font-weight:700;font-size:14px;box-shadow:0 8px 24px rgba(0,0,0,.4);animation:toastIn .3s both}'''
update_js = '''
const BUILD='%s';
async function checkBuild(){ try{ const r=await fetch('version.json?t='+Date.now(),{cache:'no-store'}); const j=await r.json(); if(j.build&&j.build!==BUILD) $('#updateBar').hidden=false; }catch(_){} }
$('#updateBar').onclick=async()=>{ $('#updateBar').textContent='Updating…'; try{ await fetch('index.html',{cache:'reload'}); }catch(_){} location.reload(); };
setInterval(checkBuild, 5*60*1000); document.addEventListener('visibilitychange',()=>{ if(!document.hidden) checkBuild(); }); setTimeout(checkBuild, 4000);
''' % BUILD
s = s.replace('<div class="toast" id="toast" hidden></div>', update_markup + '\n<div class="toast" id="toast" hidden></div>', 1)
s = s.replace('</style>', update_css + '\n</style>', 1)
s = s.replace('</script>', update_js + '</script>')  # last script block in the body
open(os.path.join(HERE,'version.json'),'w').write('{"build":"%s"}\n' % BUILD)

out = head + s + '\n</body>\n</html>\n'
open(OUT,'w').write(out)
print('built', len(out), 'bytes')
