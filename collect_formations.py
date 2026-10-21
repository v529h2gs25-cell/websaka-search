"""Incremental, conservative WEBサカWIKI formation leaderboard collector.
Discovers formations from /formation and fetches a limited number each run.
Existing successful entries survive partial errors; publication is atomic.
"""
import json, os, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE='https://rohm.websoccer.info'
DEST=Path(__file__).with_name('formations.json')
LIMIT=max(1,min(int(os.getenv('FORMATION_BATCH','3')),10))
PAUSE=max(2.0,float(os.getenv('FORMATION_PAUSE','2.5')))
s=requests.Session();s.headers.update({'User-Agent':'WEBsakaFanTool/1.1 (noncommercial, limited rate)'})
def get(path):
    url=urljoin(BASE,path)
    r=s.get(url,timeout=35);r.raise_for_status();r.encoding=r.apparent_encoding
    time.sleep(PAUSE)
    return BeautifulSoup(r.text,'html.parser')
def discover():
    soup=get('/formation')
    found={}
    for a in soup.select('a[href]'):
        href=urlparse(urljoin(BASE,a['href']))
        if href.netloc!='rohm.websoccer.info':continue
        m=re.fullmatch(r'/formation/(\d+)/?',href.path)
        if not m:continue
        title=a.get_text(' ',strip=True)
        if title:found[int(m.group(1))]=title
    return found

def rows_for(soup):
    output=[]
    for table in soup.select('table'):
        header=table.find('tr')
        if not header:continue
        headers=[c.get_text(' ',strip=True) for c in header.find_all(['th','td'])]
        if not ('試合数' in ' '.join(headers) and '偏差値' in ' '.join(headers)):continue
        for tr in table.find_all('tr')[1:]:
            cells=[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)]
            if len(cells)<7:continue
            # Wiki table: rank | player | [avatar] | kind | matches | rating | deviation ...
            start=next((i for i,x in enumerate(cells) if re.fullmatch(r'\d{1,8}',x) and i>=3),None)
            if start is None or start+2>=len(cells):continue
            try:
                matches=int(cells[start]);rating=float(cells[start+1]);score=float(cells[start+2])
            except ValueError:continue
            if not 0<=score<=120:continue
            name=cells[1].strip() if len(cells)>1 else ''
            kind=cells[start-1].strip()
            if not name or name=='平均値' or kind not in ('金','銀','銅','無','PS'):continue
            def num(i):
                try:return float(cells[i])
                except (ValueError,IndexError):return 0
            output.append({'name':name,'rank':kind,'matches':matches,'rating':rating,'score':score,'goals':num(start+3),'assists':num(start+4)})
    return output

def main():
    existing={}
    if DEST.exists():
        data=json.loads(DEST.read_text(encoding='utf-8'))
        if isinstance(data,list):existing={int(f['id']):f for f in data if isinstance(f,dict) and 'id' in f}
    discovered=discover()
    if not discovered:raise RuntimeError('No formations discovered; previous export retained')
    todo=[fid for fid in discovered if fid not in existing]
    # Refresh existing formations only when no new formations remain.
    if not todo:todo=list(discovered)
    successful=0
    for fid in todo[:LIMIT]:
        try:
            page=get(f'/formation/{fid}')
            heading=page.find(['h1','h2'])
            title=heading.get_text(' ',strip=True) if heading else ''
            m=re.search(r'(.+?)\s*\((\d+(?:-\d+)+)\)',title)
            name=m.group(1).strip() if m else discovered[fid]
            system=m.group(2) if m else ''
            if not system:
                # Formations list is grouped by system; if not available keep blank instead of guessing.
                old=existing.get(fid,{})
                system=old.get('system','')
            positions=[]
            for pos in range(1,12):
                rows=rows_for(get(f'/formation/{fid}/position/{pos}'))
                if not rows:raise ValueError(f'Empty/unrecognized position {pos}')
                positions.append(rows)
            existing[fid]={'id':fid,'name':name,'system':system,'positions':positions,'url':f'{BASE}/formation/{fid}'}
            successful+=1
            print(f'Validated {fid}: {name}, 11 positions',flush=True)
        except (requests.RequestException,ValueError) as e:
            print(f'Skipping {fid}: {e}; retaining prior data',flush=True)
    if successful==0:raise RuntimeError('No complete formation collected; previous export retained')
    payload=list(existing.values())
    tmp=DEST.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    tmp.replace(DEST)
    print(f'Saved {len(payload)} formations ({successful} collected this run)',flush=True)
if __name__=='__main__':main()
