from pathlib import Path
p=Path('/mnt/data/v5work/index.html'); s=p.read_text()
s=s.replace(' · v4</p>',' · v5</p>')
start=s.index('<section class="panel" id="teamPanel"'); end=s.index('<section class="panel" id="comparePanel"',start)
s=s[:start]+'''<section class="panel" id="teamPanel" hidden><h2>⚽ マイチーム編成 v5</h2><p class="helpnote">フォーメーションを選び、ピッチ上の枠をタップして選手名を検索。各枠の「Wiki番号」は実際のゲーム画面と照合して設定できます（初期値は仮番号）。</p><div class="team-actions"><label>フォーメーション <select id="formationSelect"></select></label><label>最低出場数 <input id="minMatches" type="number" value="100" min="0" step="10" style="width:100px"></label><button class="toolbtn" id="saveTeam">保存</button><button class="toolbtn" id="clearTeam">全員クリア</button></div><p id="formationStatus" class="helpnote"></p><div class="pitch" id="teamGrid"></div><div id="playerPicker" class="picker" hidden><h3 id="pickerTitle">選手を配置</h3><label>選手名を入力 <input id="pickerSearch" type="search" placeholder="例：ゾフ、ノテウス"></label><div id="pickerResults"></div><button type="button" id="closePicker">閉じる</button></div></section>''' +s[end:]
s=s.replace('const teamKey=\'websaka-team-v4\';',"const teamKey='websaka-team-v5';")
s=s.replace("try{const t=JSON.parse(localStorage.getItem(teamKey)||'null');if(Array.isArray(t)&&t.length===11)team=t}catch(e){}","try{const t=JSON.parse(localStorage.getItem(teamKey)||'null');if(t&&Array.isArray(t.team)&&t.team.length===11)team=t.team}catch(e){}")
s=s.replace("const slotNames=['GK','DF 右','DF 中央','DF 左','DF 自由','MF 右','MF 中央','MF 左','MF 自由','FW 右','FW 左'];","const slotNames=['GK','LB','LCB','RCB','RB','LDH','RDH','LOH','COH','ROH','CF'];")
s=s.replace("$('teamToggle').textContent=`⚽ マイチーム (${team.filter(Boolean).length}/11)`;","$('teamToggle').textContent=`⚽ マイチーム (${team.filter(Boolean).length}/11)`;")
s=s.replace("const idx=team.indexOf(null);if(idx<0){alert('チームは11人までです');return}team[idx]=key(p);saveTeam();teamVisible=true;render()","const idx=team.indexOf(null);if(idx<0){alert('チームは11人までです');return}team[idx]=key(p);saveTeam();teamVisible=true;render()")
start=s.index("$('clearTeam').onclick=");end=s.index('function load(data)',start)
s=s[:start]+'''$('clearTeam').onclick=()=>{if(confirm('チームを全員クリアしますか？')){team=Array(11).fill(null);saveTeam();render()}};
const layout=[{label:'GK',x:50,y:92},{label:'LB',x:14,y:74},{label:'LCB',x:38,y:76},{label:'RCB',x:62,y:76},{label:'RB',x:86,y:74},{label:'LDH',x:36,y:55},{label:'RDH',x:64,y:55},{label:'LOH',x:16,y:34},{label:'COH',x:50,y:30},{label:'ROH',x:84,y:34},{label:'CF',x:50,y:10}];
let formations=[],selectedFormation='67',pickerSlot=-1;
let mapping={};
try{const old=JSON.parse(localStorage.getItem(teamKey)||'null');if(old){selectedFormation=String(old.formation||'67');mapping=old.mapping||{}}}catch(e){}
const formationData=()=>formations.find(f=>String(f.id)===selectedFormation);
function saveTeam(){try{localStorage.setItem(teamKey,JSON.stringify({team,formation:selectedFormation,mapping}))}catch(e){alert('ブラウザに保存できませんでした')}}
function formPos(i){const v=mapping[selectedFormation+'-'+i];return v===undefined?i+1:Number(v)}
function rowFor(p,i){const f=formationData();if(!f)return null;const rows=f.positions[formPos(i)-1]||[];return rows.find(r=>r.name===p.name&&r.rank===p.rank)||null}
function renderTeam(){const grid=$('teamGrid');grid.replaceChildren();const f=formationData();$('formationStatus').textContent=f?`${f.name} (${f.system})：公開されたポジション別実績を表示中。Wiki番号はゲーム内の番号と照合してください。`:'このフォーメーションの成績は未取得です。選手名検索と配置は利用できます。';
 const names=f?layout:layout;
 for(let i=0;i<11;i++){
  const p=players.find(x=>key(x)===team[i]);const pos=names[i];
  const slot=document.createElement('div');slot.className='pitch-slot';slot.style.left=pos.x+'%';slot.style.top=pos.y+'%';
  const pick=document.createElement('button');pick.type='button';pick.className='pitch-pick';pick.textContent=(p?p.name:'＋ 選手')+'\\n'+pos.label;pick.onclick=()=>openPicker(i);slot.append(pick);
  const number=document.createElement('select');number.title='WIKIのポジション番号';number.setAttribute('aria-label',pos.label+'のWiki番号');
  for(let n=1;n<=11;n++){const o=document.createElement('option');o.value=n;o.textContent='Wiki '+n;number.append(o)}number.value=formPos(i);number.onchange=()=>{mapping[selectedFormation+'-'+i]=Number(number.value);saveTeam();renderTeam()};slot.append(number);
  if(p){const r=rowFor(p,i);const info=document.createElement('small');info.textContent=r?`評価 ${r.rating.toFixed(2)} / ${r.matches}試合`:'実績未取得';slot.append(info)}grid.append(slot)
 }
}
function openPicker(i){pickerSlot=i;$('playerPicker').hidden=false;$('pickerTitle').textContent=layout[i].label+' に選手を配置';$('pickerSearch').value='';renderPicker();$('pickerSearch').focus();$('playerPicker').scrollIntoView({behavior:'smooth',block:'nearest'})}
function renderPicker(){const box=$('pickerResults');box.replaceChildren();const q=$('pickerSearch').value.trim().toLowerCase();const min=Number($('minMatches').value)||0;
 let list=players.filter(p=>!team.some((k,i)=>i!==pickerSlot&&k===key(p))&&(!q||p.name.toLowerCase().includes(q)));
 const f=formationData();if(f)list.sort((a,b)=>{const ra=rowFor(a,pickerSlot),rb=rowFor(b,pickerSlot);return ((rb&&rb.matches>=min?rb.score:-999)-(ra&&ra.matches>=min?ra.score:-999))||b.score-a.score});else list.sort((a,b)=>a.name.localeCompare(b.name,'ja'));
 list.slice(0,40).forEach(p=>{const r=rowFor(p,pickerSlot);const b=document.createElement('button');b.type='button';b.className='picker-result';b.textContent=`${p.name} (${p.rank}・${p.position})`+(r?`｜Wiki偏差値 ${r.score.toFixed(2)}｜${r.matches}試合｜評価 ${r.rating.toFixed(2)}`:'｜該当実績なし');b.onclick=()=>{team[pickerSlot]=key(p);saveTeam();$('playerPicker').hidden=true;render()};box.append(b)});
 const clear=document.createElement('button');clear.textContent='この枠を空にする';clear.onclick=()=>{team[pickerSlot]=null;saveTeam();$('playerPicker').hidden=true;render()};box.append(clear)
}
$('pickerSearch').oninput=renderPicker;$('minMatches').oninput=renderPicker;$('closePicker').onclick=()=>{$('playerPicker').hidden=true};
$('formationSelect').onchange=e=>{selectedFormation=e.target.value;saveTeam();renderTeam()};
fetch('./formations.json').then(r=>{if(!r.ok)throw Error('未配信');return r.json()}).then(data=>{if(!Array.isArray(data))throw Error('形式エラー');formations=data;const sel=$('formationSelect');sel.replaceChildren();data.forEach(f=>{const o=document.createElement('option');o.value=f.id;o.textContent=f.name+' ('+f.system+')';sel.append(o)});if(!data.some(f=>String(f.id)===selectedFormation))selectedFormation=String(data[0]?.id||67);sel.value=selectedFormation;renderTeam()}).catch(()=>{$('formationStatus').textContent='formations.json はまだ未生成です。Actionsの収集成功後に実績が表示されます。';const sel=$('formationSelect');const o=document.createElement('option');o.value='67';o.textContent='ブラジル 2014 (4-2-3-1)';sel.append(o);renderTeam()});
''' +s[end:]
s=s.replace("if(!found.length){const e=", "if(!found.length){const e=")
s=s.replace("e.textContent='条件に合う選手がいません';", "e.textContent=coords&&!players.some(p=>Array.isArray(p.aptitude))?'適性データがまだ取得されていません。適性エリアを「すべて」に戻してください。':'条件に合う選手がいません';")
s=s.replace('</style>', '''
.pitch{height:560px;max-width:520px;margin:20px auto;position:relative;border:4px solid #e3f0e5;border-radius:18px;background:repeating-linear-gradient(0deg,#276e43 0px,#276e43 69px,#2d794a 70px,#2d794a 140px);box-shadow:inset 0 0 0 2px #ffffff55}
.pitch:before{content:'';position:absolute;inset:7%;border:2px solid #ffffff70;pointer-events:none}.pitch:after{content:'';position:absolute;top:45%;left:25%;width:50%;height:10%;border:2px solid #ffffff70;border-radius:50%;pointer-events:none}
.pitch-slot{position:absolute;transform:translate(-50%,-50%);width:24%;min-width:72px;text-align:center;z-index:1}.pitch-pick{width:100%;min-height:45px;border:1px solid #d3e3ff;border-radius:10px;background:#f5faff;color:#152b49;font-size:12px;white-space:pre-line;overflow-wrap:anywhere;padding:5px 2px;font-weight:700}.pitch-slot select{font-size:10px;padding:2px;margin-top:2px;max-width:100%;background:#fff}.pitch-slot small{display:block;background:#ffffffec;color:#19344a;border-radius:4px;font-size:10px}.picker{border:2px solid #c6d8ef;border-radius:14px;padding:15px;margin-top:18px}.picker-result{display:block;width:100%;text-align:left;padding:12px;margin:6px 0;background:#f6f9ff;border:1px solid #d9e4f3;border-radius:8px;color:#17334d}.picker input{width:100%}
@media(max-width:500px){.pitch{height:490px}.pitch-slot{width:25%}.pitch-pick{font-size:11px;min-height:44px}}
</style>''')
p.write_text(s)
