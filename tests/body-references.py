"""Reference markers must never corrupt image alt/href/loading attributes."""
import json,os,shutil,tempfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from browser_storage import open_written_case
ROOT=Path(__file__).resolve().parents[1];ART=Path(tempfile.mkdtemp(prefix='hitomon-body-references-'))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if urlparse(path).path.startswith('/ap-study/'):path=path[len('/ap-study'):]
  return super().translate_path(path)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
BASE=os.getenv('HITOMON_TEST_URL',f'http://127.0.0.1:{server.server_port}/ap-study/')
cases=json.loads((ROOT/'content/ap/written-cases.json').read_text())+json.loads((ROOT/'content/fp2/practical-cases.json').read_text())
try:
 with sync_playwright() as p:
  opts={'executable_path':shutil.which('chromium'),'args':['--no-sandbox']}
  if BASE.startswith('https:') and os.getenv('HTTPS_PROXY'):opts['proxy']={'server':os.environ['HTTPS_PROXY'],'bypass':'127.0.0.1,localhost'}
  b=p.chromium.launch(**opts);pg=b.new_page(viewport={'width':1440,'height':1000});errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(BASE+'ap/?part=written&entry=home');pg.locator('.quick-start').wait_for()
  result=pg.evaluate('''async cases=>{
   const {caseBodyHTML,addBodyReferences}=await import('./src/ui/case-body.js');let figures=0,markers=0,imageAliases=0;
   const mappings=Object.fromEntries((await(await fetch(new URL('data/qualifications/ap/manifest.json',document.baseURI))).json()).cases.index.map(e=>[e.caseId,e.referenceTargets||{}]));
   for(const c of cases){
    const root=document.createElement('div');root.innerHTML=caseBodyHTML(c,document.baseURI,mappings[c.id]);
    const images=[...root.querySelectorAll('figure img')];
    if(images.length!==c.bodyFigures.length)throw Error(c.id+': figure count');
    c.bodyFigures.forEach((f,i)=>{
     const img=images[i],figure=img.closest('figure');
     if(img.getAttribute('alt')!==f.alt||img.getAttribute('loading')!=='lazy'||img.src!==new URL(f.image,document.baseURI).href)throw Error(c.id+': changed image attributes');
     if(img.closest('a').textContent.trim()||figure.querySelector('figcaption').textContent!==f.caption)throw Error(c.id+': leaked attribute text');
     if(!figure.querySelector('a>img'))throw Error(c.id+': damaged image link');figures++;
    });
    for(const [id,ref] of Object.entries(c.bodyRefs||{})){
     const text=ref.text||ref.anchor,target=[...root.querySelectorAll('[id]')].find(e=>e.id==='written-ref-'+id);
     if(!target)throw Error(c.id+': unresolved reference '+id);markers++;
     if(!['text','figure'].includes(target.dataset.bodyRefKind))throw Error(c.id+': unclassified reference '+id);
     if(mappings[c.id]?.[id]){const expected=root.querySelector('#written-ref-'+mappings[c.id][id]);if(target.closest('figure')!==expected||target.dataset.bodyRefKind!=='figure')throw Error(c.id+': wrong image target '+id);imageAliases++;}
     if(c.bodyFigures.some(f=>f.caption===text)&&target?.tagName!=='FIGURE')throw Error(c.id+': figure reference not on figure');
    }
   }
   const html='<p><strong>分割</strong>された参照</p><a href="https://example.test/参照"><img alt="属性だけの参照 &quot; quoted" loading="lazy"></a>';
   const root=document.createElement('div');root.innerHTML=addBodyReferences(html,{split:{text:'分割された参照'},attribute:{text:'属性だけの参照'},quote:{text:'quoted'}});
   if(root.querySelector('img').getAttribute('alt')!=='属性だけの参照 " quoted'||root.querySelector('img').getAttribute('loading')!=='lazy'||root.querySelector('a').textContent.trim())throw Error('synthetic attribute integrity');
   if(!root.querySelector('#written-ref-split strong')||root.querySelector('#written-ref-attribute,#written-ref-quote'))throw Error('synthetic text-only markers');
   const figureHTML='<figure><a><img alt="図内の語"></a><figcaption>図1</figcaption></figure><p>図内の語</p>';
   root.innerHTML=addBodyReferences(figureHTML,{figure:{anchor:'図1'},inside:{text:'図内の語'},missing:{text:'未定義の語'}},{inside:'figure'});
   if(root.querySelector('#written-ref-inside')?.closest('figure')?.id!=='written-ref-figure'||root.querySelector('#written-ref-missing'))throw Error('explicit image reference / unresolved reference');
   root.innerHTML=addBodyReferences(figureHTML,{figure:{anchor:'図1'},missing:{text:'未定義の語'}});
   if(root.querySelector('#written-ref-missing'))throw Error('missing text guessed as image');
   return {cases:cases.length,figures,markers,imageAliases};
  }''',cases)
  open_written_case(pg,'ap-r07h-pm8')
  pg.evaluate('async()=>{await Promise.all([...document.querySelectorAll(".written-body img")].map(img=>{img.loading="eager";return img.decode();}));}')
  assert pg.locator('.written-body figure a').all_text_contents()==['','']
  assert pg.locator('.written-body #written-ref-figure-1').evaluate('e=>e.tagName')=='FIGURE'
  pg.locator('[data-action=written-reference]').click();pg.locator('.written-layout[data-pane=body]').wait_for();pg.locator('#written-ref-figure-1').screenshot(path=str(ART/'pm8-figure1.png'))
  field=pg.locator('.written-field').first;field.locator('textarea').fill('保持する回答');pg.reload();pg.locator('.written-layout').wait_for();assert pg.locator('textarea').first.input_value()=='保持する回答';assert pg.locator('.written-body figure a').all_text_contents()==['','']
  for width in [320,390,1440]:
   pg.set_viewport_size({'width':width,'height':1000})
   if width<=390:pg.locator('[data-action=written-pane][data-pane=body]').click()
   assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1');pg.screenshot(path=str(ART/f'pm8-{width}.png'))
  open_written_case(pg,'ap-r07h-pm6');pg.locator('[data-action=written-reference]').click();pg.locator('.written-layout[data-pane=body]').wait_for();
  assert pg.locator('#written-ref-blank-a').evaluate('e=>e.closest("figure").id')=='written-ref-figure-1'
  pg.locator('#written-ref-blank-a').evaluate('e=>e.scrollIntoView({block:"start"})');assert pg.locator('#written-ref-blank-a').evaluate('e=>Math.abs(e.getBoundingClientRect().top-e.closest("figure").getBoundingClientRect().top)')<24
  assert not errors,errors;b.close()
finally:server.shutdown()
(ART/'results.json').write_text(json.dumps({**result,'pm8FigureReferenceJump':True,'typedAnswerPreserved':True,'pageErrors':errors},ensure_ascii=False,indent=2)+'\n')
print('PASS reference markers / real cases and figure attributes / pm8 render, jump and input resume:',result);print('Artifacts:',ART)
