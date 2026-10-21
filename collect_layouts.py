"""Detect purple position markers in rendered Wiki formation thumbnails.
Writes only fully validated 11-point layouts; failures retain existing data.
Requires playwright chromium and Pillow. No screenshots are committed.
"""
import io, json, math, os, time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

DEST=Path(__file__).with_name('formations.json')
BATCH=max(1,min(int(os.getenv('LAYOUT_BATCH','3')),10))
BASE='https://rohm.websoccer.info'

def detect(blob):
    im=Image.open(io.BytesIO(blob)).convert('RGB')
    w,h=im.size
    # Purple dot used for selected position, not red/blue jerseys.
    mask=set()
    for y in range(int(h*.04),int(h*.91)):
        for x in range(int(w*.04),int(w*.96)):
            r,g,b=im.getpixel((x,y))
            if 50<r<190 and 15<g<150 and 90<b<255 and b>r*1.12 and b>g*1.28:
                mask.add((x,y))
    groups=[]
    while mask:
        start=mask.pop();stack=[start];pts=[start]
        while stack:
            x,y=stack.pop()
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if (nx,ny) in mask:
                    mask.remove((nx,ny));stack.append((nx,ny));pts.append((nx,ny))
        if len(pts)>=12:
            groups.append(pts)
    groups.sort(key=len,reverse=True)
    if not groups:return None
    group=groups[0]
    if len(group)<12 or len(group)>w*h*.075:return None
    x=sum(p[0] for p in group)/len(group);y=sum(p[1] for p in group)/len(group)
    # Formation thumbnail includes a footer; normalize to the playing field.
    return {'x':round(100*x/w,2),'y':round(100*y/(h*.85),2)}

def read_position(page,fid,pos):
    page.goto(f'{BASE}/formation/{fid}/position/{pos}',wait_until='domcontentloaded',timeout=45000)
    page.wait_for_timeout(650)
    candidates=page.locator('img')
    for i in range(min(candidates.count(),20)):
        item=candidates.nth(i)
        try:
            meta=item.evaluate('''el=>({w:el.getBoundingClientRect().width,h:el.getBoundingClientRect().height,src:el.currentSrc,alt:el.alt})''')
            w,h=meta['w'],meta['h']
            if not (60<=w<=300 and 85<=h<=380 and .35<=w/h<=1.3):continue
            # Capture a slightly larger box in case the marker is an HTML overlay.
            box=item.bounding_box()
            if not box:continue
            clip={'x':max(0,box['x']-3),'y':max(0,box['y']-3),'width':w+6,'height':h+6}
            blob=page.screenshot(clip=clip,animations='disabled')
            result=detect(blob)
            if result:return result
        except Exception:continue
    return None

def valid(points):
    if len(points)!=11 or any(p is None for p in points):return False
    if any(not (5<=p['x']<=95 and 4<=p['y']<=100) for p in points):return False
    if points[0]['y']<78:return False
    for i,a in enumerate(points):
        for b in points[i+1:]:
            if math.dist((a['x'],a['y']),(b['x'],b['y']))<5:return False
    return True

def main():
    if not DEST.exists():raise SystemExit('formations.json missing')
    data=json.loads(DEST.read_text(encoding='utf-8'))
    pending=[f for f in data if not (f.get('layout_status')=='verified' and len(f.get('layout',[]))==11)]
    if not pending:print('All layouts already verified');return
    successes=0
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1200,'height':1000},device_scale_factor=2)
        for f in pending[:BATCH]:
            fid=f['id'];pts=[]
            for pos in range(1,12):
                try:point=read_position(page,fid,pos)
                except Exception as e:print('position error',fid,pos,str(e)[:140]);point=None
                pts.append(point)
                print('layout',fid,pos,point,flush=True)
                time.sleep(.5)
            if valid(pts):
                f['layout']=pts;f['layout_status']='verified';successes+=1
                print('VERIFIED',fid,flush=True)
            else:
                print('UNVERIFIED',fid,'previous layout retained',flush=True)
        browser.close()
    if successes:
        temp=DEST.with_suffix('.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        temp.replace(DEST)
    print(f'Layout pass: {successes} verified out of {min(len(pending),BATCH)} checked')

if __name__=='__main__':main()
