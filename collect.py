"""Collect publicly visible WEBサカWIKI player listings into players.json.
Run: pip install requests beautifulsoup4 && python collect.py
Please respect the website's terms, robots rules and server load.
"""
import json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
BASE='https://rohm.websoccer.info'
s=requests.Session();s.headers.update({'User-Agent':'WebsakaPersonalSearch/1.0 (personal data indexing)'})
players=[]
for page in range(1,57):
    url=f'{BASE}/player/list/normal/{page}'
    response=s.get(url,timeout=25);response.raise_for_status()
    soup=BeautifulSoup(response.text,'html.parser')
    # Use the site's visible text order to identify player blocks.
    lines=[x.strip() for x in soup.get_text('\n').splitlines() if x.strip()]
    headers=[]
    for i,line in enumerate(lines):
        m=re.match(r'^\[(FW|MF|DF|GK)\]\s*(.+?)\s*\((金|銀|銅|無)\)$',line)
        if m:headers.append((i,m))
    for idx,(start,m) in enumerate(headers):
        end=headers[idx+1][0] if idx+1<len(headers) else len(lines)
        block='\n'.join(lines[start:end]);score=re.search(r'偏差値\s*\n?\s*([\d.]+)',block)
        if not score:continue
        position,name,rank=m.groups()
        link=soup.find('a',string=lambda t:bool(t and name in t))
        href=link.get('href','') if link else ''
        from urllib.parse import urljoin
        players.append(dict(name=name,position=position,rank=rank,score=float(score.group(1)),page=page,url=urljoin(BASE,href) if href else url))
    print(f'page {page}/56: {len(headers)} headers, {len(players)} total')
    time.sleep(1.5)
if not players:raise RuntimeError('No players extracted; site markup may have changed.')
Path(__file__).with_name('players.json').write_text(json.dumps(players,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Saved {len(players)} players')
