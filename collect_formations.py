"""Incremental WEBサカWIKI formation data collection.
Publish catalog independently; keep previous good data on failures; rotate attempts.
"""
import json, os, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE='https://rohm.websoccer.info'
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'formations.json'
CATALOG=ROOT/'formations_catalog.json'
STATE=ROOT/'formations_progress.json'
LIMIT=max(1,min(int(os.getenv('FORMATION_BATCH','5')),12))
PAUSE=max(1.5,float(os.getenv('FORMATION_PAUSE','2.5')))
s=requests.Session()
s.headers.update({'User-Agent':'WEBsakaFanTool/1.2 (noncommercial, rate-limited)'})

def get(path):
    r=s.get(urljoin(BASE,path),timeout=35)
    r.raise_for_status()
    r.encoding=r.apparent_encoding
    time.sleep(PAUSE)
    return BeautifulSoup(r.text,'html.parser')

def write_json(path,obj):
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    temp.replace(path)

def discover():
    soup=get('/formation')
    found={}
    for a in soup.select('a[href]'):
        href=urlparse(urljoin(BASE,a['href']))
        if href.netloc!='rohm.websoccer.info':continue
        match=re.fullmatch(r'/formation/(\d+)/?',href.path)
        if match and a.get_text(' ',strip=True):
            found[int(match.group(1))]=a.get_text(' ',strip=True)
    return found

def rows_for(soup):
    output=[]
    for table in soup.select('table'):
        first=table.find('tr')
        if not first:continue
        headers=' '.join(c.get_text(' ',strip=True) for c in first.find_all(['th','td']))
        if '試合数' not in headers or '偏差値' not in headers:continue
        for tr in table.find_all('tr')[1:]:
            cells=[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)]
            if len(cells)<7:continue
            start=next((i for i,x in enumerate(cells) if re.fullmatch(r'\d{1,8}',x) and i>=3),None)
            if start is None or start+2>=len(cells):continue
            try:
                matches=int(cells[start]);rating=float(cells[start+1]);score=float(cells[start+2])
            except ValueError:continue
            if not 0<=score<=120:continue
            name=cells[1].strip()
            kind=cells[start-1].strip()
            if not name or name=='平均値' or kind not in ('金','銀','銅','無','PS'):continue
            def num(i):
                try:return float(cells[i])
                except (ValueError,IndexError):return 0
            output.append(dict(name=name,rank=kind,matches=matches,rating=rating,score=score,goals=num(start+3),assists=num(start+4)))
    return output

def complete(f):
    return isinstance(f,dict) and len(f.get('positions',[]))==11 and all(isinstance(p,list) and p for p in f['positions'])

def main():
    old=json.loads(DEST.read_text(encoding='utf-8')) if DEST.exists() else []
    existing={int(f['id']):f for f in old if complete(f)}
    prior_catalog=json.loads(CATALOG.read_text(encoding='utf-8')) if CATALOG.exists() else []
    try:
        found=discover()
        if not found:raise ValueError('Empty formation directory')
        catalog=[]
        for fid,title in sorted(found.items()):
            previous=existing.get(fid,{})
            match=re.search(r'(.+?)\s*\((\d+(?:-\d+)+)\)',title)
            name=match.group(1).strip() if match else (previous.get('name') or title)
            system=match.group(2) if match else previous.get('system','')
            catalog.append(dict(id=fid,name=name,system=system,url=f'{BASE}/formation/{fid}'))
        write_json(CATALOG,catalog)
    except (requests.RequestException,ValueError) as exc:
        print('Catalog refresh failed; retaining existing catalog:',exc,flush=True)
        catalog=prior_catalog
    if not catalog:
        print('No catalog available; no changes published',flush=True)
        return
    ids=[int(f['id']) for f in catalog]
    # Continue where last execution stopped. This avoids retrying a broken entry forever.
    progress=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    cursor=int(progress.get('cursor',0))%len(ids)
    ordered=ids[cursor:]+ids[:cursor]
    todo=[fid for fid in ordered if fid not in existing]
    if not todo:
        # When everything is collected, rotate refreshes to update stats.
        todo=ordered
    selected=todo[:LIMIT]
    success=0
    for fid in selected:
        entry=next(x for x in catalog if int(x['id'])==fid)
        try:
            page=get(f'/formation/{fid}')
            heading=page.find(['h1','h2'])
            heading_text=heading.get_text(' ',strip=True) if heading else ''
            match=re.search(r'(.+?)\s*\((\d+(?:-\d+)+)\)',heading_text)
            name=match.group(1).strip() if match else entry['name']
            system=match.group(2) if match else entry.get('system','')
            positions=[]
            for pos in range(1,12):
                rows=rows_for(get(f'/formation/{fid}/position/{pos}'))
                if not rows:raise ValueError(f'No usable results for position {pos}')
                positions.append(rows)
            fresh=dict(id=fid,name=name,system=system,positions=positions,url=f'{BASE}/formation/{fid}')
            previous=existing.get(fid,{})
            if previous.get('layout_status')=='verified' and len(previous.get('layout',[]))==11:
                fresh['layout']=previous['layout']
                fresh['layout_status']='verified'
            existing[fid]=fresh
            success+=1
            # Persist every successful formation immediately, even if later entries fail.
            write_json(DEST,[existing[k] for k in sorted(existing)])
            print(f'OK {fid}: {name} (11 positions)',flush=True)
        except (requests.RequestException,ValueError,IndexError,KeyError) as exc:
            print(f'SKIP {fid}: {exc}; previous results retained',flush=True)
    # Advance beyond the last attempted ID, including failures.
    last=selected[-1] if selected else ids[cursor]
    next_cursor=(ids.index(last)+1)%len(ids)
    write_json(STATE,{'cursor':next_cursor,'last_attempted_id':last,'catalog_count':len(ids)})
    print(f'Catalog {len(catalog)}; complete data {len(existing)}; successes {success}/{len(selected)}; next cursor {next_cursor}',flush=True)

if __name__=='__main__':main()
