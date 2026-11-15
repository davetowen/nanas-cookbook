import glob, os, re, json, subprocess
from PIL import Image
S='/tmp/claude-0/-home-claude/f2b6ad73-d825-5f47-917e-b8750b100caa/scratchpad/'
OUT=S+'site2/'
def web(src,dst,mx=1100,q=78):
    im=Image.open(src).convert('RGB'); im.thumbnail((mx,mx)); im.save(dst,quality=q,optimize=True,progressive=True); return im.size
cat=[]
GROUPS={'Hazel':[37,39,40,41,42,47,26,35,38],'Duane':[25,15,21,17,22,2,1,4,7,8,19,20,23,24],'Ginny':[27,50,53,51,54,29,46,55,31,33,32,30,5,6],
        'Christmas':[11,10,12,3,43,18,36,13],'Family & places':[9,49,52,16,28,34,14,44,45,48],'Whispering Pines & school':[57,58,59,60,61,62,63,64,65,66,67,56]}
gof={n:g for g,ns in GROUPS.items() for n in ns}
CLIPS={25:'03 - Duane Bonnie 1943 (test).mp4'}
for f in glob.glob(S+'review/animated/*.mp4'):
    m=re.match(r'(\d+) - ',os.path.basename(f))
    if m and 'test' not in f: CLIPS[int(m.group(1))]=os.path.basename(f)
for f in sorted(glob.glob('/mnt/user-data/outputs/cleaned/*.jpg')):
    b=os.path.basename(f); n=int(b[:2]); cap=re.sub(r'\.jpg$','',b[5:]).strip()
    w,h=web(f,OUT+'photos/z%02d.jpg'%n)
    e={'id':'z%02d'%n,'src':'photos/z%02d.jpg'%n,'cap':cap,'group':gof.get(n,'Family & places'),'w':w,'h':h}
    c=S+'review/colorized/'+b
    if os.path.exists(c): web(c,OUT+'photos/z%02dc.jpg'%n); e['color']='photos/z%02dc.jpg'%n
    if n in (45,51): e['preferOriginal']=True
    if n in CLIPS:
        dst=OUT+'clips/z%02d.mp4'%n
        subprocess.run(['ffmpeg','-v','error','-y','-i',S+'review/animated/'+CLIPS[n],'-vf','scale=-2:960','-c:v','libx264','-crf','30','-preset','slow','-c:a','aac','-b:a','64k','-movflags','+faststart',dst],check=True)
        e['clip']='clips/z%02d.mp4'%n
    ym=re.findall(r'(19\d\d)',cap); e['year']=int(ym[0]) if ym else None
    cat.append(e)
book={}
for f in sorted(glob.glob('/mnt/user-data/outputs/from-book/*.jpg')):
    k=os.path.basename(f)[5:-4]   # image34
    w,h=web(f,OUT+'photos/b_%s.jpg'%k); book[k]={'src':'photos/b_%s.jpg'%k,'w':w,'h':h}
c20=S+'review/colorized/book-image20.jpg'
if os.path.exists(c20): web(c20,OUT+'photos/b_image20c.jpg'); book['image20']['color']='photos/b_image20c.jpg'
json.dump({'album':cat,'book':book},open(S+'build/media.json','w'),ensure_ascii=False,indent=0)
print(len(cat),len(book),sum(1 for e in cat if e.get('color')),sum(1 for e in cat if e.get('clip')))
