"""Collect a small, expandable set of WEBサカWIKI formation-position leaderboards.
Never overwrite a previous successful export on partial failure.
"""
import json, re, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE='https://rohm.websoccer.info'
DEST=Path(__file__).with_name('formations.json')
# Expand this list gradually after verifying site access policy and load.
IDS=[67,34,49]
S=requests.Session()
S.headers.update({'User-Agent':'WEBsakaFanTool/1.0 (personal, rate-limited research)'})
def get(url):
    r=S.get(url,timeout=30);r.raise_for_status();r.encoding=r.apparent_encoding
    time.sleep(2)
    return BeautifulSoup(r.text,'html.parser')
def parse_rows(soup):
    results=[]
    for table in soup.select('table'):
        heads=[x.get_text(' ',strip=True) for x in table.select('tr')[:1]]
        if not heads or '試合数' not in heads[0] or '評価点' not in heads[0]: continue
        for tr in table.select('tr'):
            cells=[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)]
            if len(cells)<10: continue
            # Rank, name, optional image, type, matches, rating, deviation, goals, assists ...
            idx=next((i for i,x in enumerate(cells) if re.fullmatch(r'\d{2,7}',x) and i>=2),None)
            if idx is None or idx<2 or idx+6>=len(cells): continue
            try:
                matches=int(cells[idx]);rating=float(cells[idx+1]);deviation=float(cells[idx+2])
                goals=float(cells[idx+3]);assists=float(cells[idx+4])
            except (ValueError,IndexError): continue
            name=next((v.strip() for v in reversed(cells[:idx-1]) if v.strip() and v.strip()!='位' and not re.fullmatch(r'\d+\s*位',v.strip())), '')
            kind=cells[idx-1].strip()
            if not name or name=='平均値':continue
            results.append(dict(name=name,rank=kind,matches=matches,rating=rating,score=deviation,goals=goals,assists=assists))
    return results

def main():
    formations=[]
    for fid in IDS:
        page=get(f'{BASE}/formation/{fid}')
        heading=page.find(['h1','h2'])
        title=heading.get_text(' ',strip=True) if heading else f'フォーメーション {fid}'
        m=re.search(r'(.+?)\s*\((\d+(?:-\d+)+)\)',title)
        name=m.group(1).strip() if m else title
        system=m.group(2) if m else ''
        positions=[]
        for pos in range(1,12):
            soup=get(f'{BASE}/formation/{fid}/position/{pos}')
            rows=parse_rows(soup)
            if not rows:raise RuntimeError(f'No table rows for formation {fid} position {pos}; existing data kept')
            positions.append(rows)
            print(f'Formation {fid} position {pos}: {len(rows)} rows',flush=True)
        formations.append(dict(id=fid,name=name,system=system,positions=positions,url=f'{BASE}/formation/{fid}'))
    tmp=DEST.with_suffix('.tmp')
    tmp.write_text(json.dumps(formations,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    tmp.replace(DEST)
    print(f'Saved {len(formations)} complete formations')
if __name__=='__main__':main()
