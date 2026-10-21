
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://rohm.websoccer.info"
players = []

session = requests.Session()
session.headers.update({
    "User-Agent": "WebsakaPersonalSearch/1.0"
})

header_pattern = re.compile(
    r"\[(FW|MF|DF|GK)\]\s*(.+?)\s*"
    r"\(\s*(金|銀|銅|無)\s*\)"
)

score_pattern = re.compile(
    r"偏差値\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)"
)

for page in range(1, 57):
    url = f"{BASE}/player/list/normal/{page}"

    response = session.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)
    matches = list(header_pattern.finditer(text))

    page_count = 0

    for i, match in enumerate(matches):
        start = match.end()
        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        block = text[start:end]
        score_match = score_pattern.search(block)

        if not score_match:
            continue

        position, name, rank = match.groups()
        name = name.strip()
        score = float(score_match.group(1))

        link = soup.find(
            "a",
            string=lambda t: bool(
                t and name in t.strip()
            )
        )

        href = link.get("href", "") if link else ""

        players.append({
            "name": name,
            "position": position,
            "rank": rank,
            "score": score,
            "page": page,
            "url": urljoin(BASE, href) if href else url
        })

        page_count += 1

    print(
        f"Page {page}/56: "
        f"{page_count} players, "
        f"total {len(players)}",
        flush=True
    )

    time.sleep(1.5)

if not players:
    raise RuntimeError(
        "No players extracted. Check HTML structure."
    )

output = Path(__file__).with_name("players.json")

output.write_text(
    json.dumps(
        players,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print(f"Saved {len(players)} players")
