"""WEBサカWIKI listing collector. Preserves last published data on parsing failures."""
import json, re, time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE = 'https://rohm.websoccer.info'
OUT = Path(__file__).with_name('players.json')
HEADER = re.compile(r'\[(FW|MF|DF|GK)\]\s*(.+?)\s*\(\s*(金|銀|銅|無)\s*\)')
SCORE = re.compile(r'偏差値\s*[:：]?\s*(\d+(?:\.\d+)?)')


def extra_stats(block):
    """Extract displayed 4x3 + GK center aptitude grid and 3 stats.

    Rows are kept in their displayed order (upper to lower). The names of
    ability categories are not assumed without verified source labels.
    """
    prefix = re.split(r'モデル\s*|偏差値\s*|年齢\s*', block, maxsplit=1)[0]
    # The visible listing has 12 grid cells, one central GK cell, then 3 stats.
    # Exclude description by accepting only a contiguous run of small integers.
    run = re.match(r'^\s*((?:\d{1,2}\s+){15}\d{1,2})(?=\s|$)', prefix)
    if not run:
        return None, None
    nums = [int(x) for x in re.findall(r'\d+', run.group(1))]
    if len(nums) != 16 or any(n < 0 or n > 10 for n in nums):
        return None, None
    # 4 rows x 3 positions, then GK center, then 3 raw abilities.
    aptitude = [nums[i:i+3] for i in range(0, 12, 3)] + [[None, nums[12], None]]
    return aptitude, nums[13:16]


def collect():
    session = requests.Session()
    session.headers.update({'User-Agent': 'WebsakaPersonalSearch/1.0 (personal indexing)'})
    players = []
    for page in range(1, 57):
        url = f'{BASE}/player/list/normal/{page}'
        response = session.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style']):
            tag.decompose()
        text = soup.get_text(' ', strip=True)
        matches = list(HEADER.finditer(text))
        count = 0
        for i, match in enumerate(matches):
            block = text[match.end(): matches[i+1].start() if i+1 < len(matches) else len(text)]
            score = SCORE.search(block)
            if not score:
                continue
            position, name, rank = match.groups()
            name = name.strip()
            link = soup.find('a', string=lambda t: bool(t and name in t.strip()))
            href = link.get('href', '') if link else ''
            aptitude, abilities = extra_stats(block)
            players.append(dict(name=name, position=position, rank=rank,
                                score=float(score.group(1)), page=page,
                                url=urljoin(BASE, href) if href else url,
                                aptitude=aptitude, abilities=abilities))
            count += 1
        print(f'Page {page}/56: {count} players, total {len(players)}', flush=True)
        time.sleep(1.5)
    if len(players) < 1000:
        raise RuntimeError(f'Only {len(players)} players parsed; refusing to overwrite data')
    parsed = sum(p['aptitude'] is not None for p in players)
    print(f'Extended aptitude/ability fields parsed: {parsed}/{len(players)}', flush=True)
    # If a site markup change breaks all extended fields, preserve the existing
    # dataset and fail loudly rather than silently publish a degraded version.
    if parsed < int(len(players) * .8):
        raise RuntimeError(f'Only {parsed}/{len(players)} aptitude grids parsed; refusing to overwrite')
    OUT.write_text(json.dumps(players, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {len(players)} players')


if __name__ == '__main__':
    collect()
