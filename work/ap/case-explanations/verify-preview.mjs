// Exercise the editorial library with Playwright; never write learner records.
import {readFile,writeFile,mkdtemp,stat} from 'node:fs/promises';
import {createServer} from 'node:http';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {resolve,sep,join,extname} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';

const require=createRequire(import.meta.url);
const {chromium}=require('playwright');
const ROOT=resolve(fileURLToPath(new URL('../../../',import.meta.url)));
const here=fileURLToPath(new URL('.',import.meta.url));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const previewSHA256=sha(await readFile(new URL('preview.html',import.meta.url)));
const {batches}=JSON.parse(await readFile(new URL('catalog.json',import.meta.url),'utf8'));
const bank=JSON.parse(await readFile(new URL('../../../content/ap/written-cases.json',import.meta.url),'utf8'));
const cases=[];
for(const batch of batches){
 for(const c of batch.cases){
  const mapping=JSON.parse(await readFile(new URL((c.draftDirectory||batch.directory)+'/explanation-links.json',import.meta.url),'utf8'));
  cases.push({...c,examLabel:batch.examLabel,targets:mapping[c.id]});
 }
}
const art=await mkdtemp(join(tmpdir(),'hitomon-explanation-library-'));
const server=createServer(async(req,res)=>{
 try{
  const path=resolve(ROOT,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!path.startsWith(ROOT+sep)&&path!==ROOT)throw Error('Outside repository');
  if(!(await stat(path)).isFile())throw Error('Not a file');
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'})[extname(path)]||'application/octet-stream');
  res.end(await readFile(path));
 }catch{res.statusCode=404;res.end('Not found');}
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const url=`http://127.0.0.1:${server.address().port}/work/ap/case-explanations/preview.html`;
const errors=[],failedRequests=[],links=[],layouts=[];
let browser;
const check=(condition,message)=>{if(!condition)throw Error(message);};
try{
 browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844}});
 page.on('pageerror',error=>errors.push(String(error)));
 page.on('requestfailed',request=>failedRequests.push(request.url()));
 page.on('response',response=>{if(response.status()>=400&&!response.url().endsWith('/favicon.ico'))failedRequests.push(response.status()+' '+response.url());});
 await page.goto(url);
 for(const c of cases){
  await page.locator(`.preview-nav a[href="#${c.id}"]`).click();
  await page.waitForFunction(id=>document.querySelector('.preview-case:not([hidden])')?.id===id,c.id);
  check(await page.locator('.preview-case:visible').count()===1,'One visible case');
  check(await page.locator('.preview-case:visible').getAttribute('id')===c.id,'Case selection '+c.id);
  check((await page.locator('.preview-case:visible .question-meta').innerText()).includes(c.examLabel),'Exam label '+c.id);
  for(const t of c.targets){
   const anchor=c.id+'--'+t.id;
   await page.locator('.preview-case:visible details').evaluateAll(nodes=>nodes.forEach(n=>n.open=false));
   await page.locator(`.preview-question-link[href="#${anchor}"]`).click();
   await page.waitForFunction(id=>{
    const el=document.getElementById(id);
    if(document.activeElement!==el)return false;
    for(let node=el;node;node=node.parentElement)if(node.tagName==='DETAILS'&&!node.open)return false;
    return true;
   },anchor);
   const heading=page.locator(`[id="${anchor}"]`);
   check(await heading.isVisible(),'Visible target '+anchor);
   check((await heading.getAttribute('data-explanation-heading')??await heading.innerText())===t.heading,'Heading '+anchor);
   const context=await heading.evaluateHandle(el=>el.matches('.preview-question-context')?el:el.tagName==='SUMMARY'?el.parentElement.querySelector('.preview-detail > .preview-question-context'):el.nextElementSibling);
   await context.evaluate(el=>{el.querySelector('.preview-source-question').open=true;});
   check(await context.evaluate(el=>el.querySelector('.preview-source-question').innerText.length>0),'Source question visible '+anchor);
   const prompt=await context.evaluate(el=>{
    const copy=el.querySelector('.preview-source-question').cloneNode(true);
    for(const math of copy.querySelectorAll('.katex')){
     const tex=math.querySelector('annotation[encoding="application/x-tex"]');
     if(!tex)throw Error('Math source annotation missing');
     math.replaceWith('$'+tex.textContent+'$');
    }
    return copy.textContent;
   });
   const item=bank.find(x=>x.id===c.id).items.find(x=>x.id===t.itemId);
   const fences=/^```[^\r\n]*\r?\n([\s\S]*?)^```[ \t]*\r?$/gm;
   const sourceBlocks=[...item.prompt.matchAll(fences)].map(([,body])=>body.replace(/\r?\n$/,'').replace(/\r\n/g,'\n'));
   const renderedBlocks=await context.evaluate(el=>[...el.querySelectorAll('.preview-source-question pre code')].map(code=>code.textContent));
   check(JSON.stringify(renderedBlocks)===JSON.stringify(sourceBlocks),'Source code blocks '+anchor);
   const normalize=s=>s.replace(/\s|\+\+|\*\*/g,'');
   check(normalize(prompt).includes(normalize(item.prompt.replace(fences,'$1'))),'Source prompt '+anchor+' '+JSON.stringify({rendered:prompt,expected:item.prompt}));
   for(const fid of t.fieldIds)check(prompt.includes(item.fields.find(f=>f.id===fid).label),'Source field '+anchor+' '+fid);
   await page.reload();
   await page.waitForFunction(id=>document.activeElement.id===id,anchor);
   check(await heading.isVisible(),'Reload target '+anchor);
   const section=heading.locator('xpath=ancestor::*[contains(concat(" ",normalize-space(@class)," ")," preview-section ")][1]');
   await section.locator('.preview-return').click();
   await page.waitForFunction(id=>document.activeElement.id===id,c.id+'--questions');
   links.push({caseId:c.id,itemId:t.itemId,fieldIds:t.fieldIds,anchor,openJumpPromptReloadReturn:true});
  }
  await page.locator('#expand').click();
  check(await page.locator('.preview-case:visible details:not([open])').count()===0,'Expand all '+c.id);
  for(const width of [320,390,1440]){
   await page.setViewportSize({width,height:900});
   for(const scale of [1,1.4]){
    await page.evaluate(scale=>document.documentElement.style.setProperty('--study-text-scale',String(scale)),scale);
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Page overflow '+c.id+' '+width+' '+scale);
    layouts.push({caseId:c.id,width,studyTextScale:scale,pageOverflow:false});
   }
  }
  await page.evaluate(()=>document.documentElement.style.removeProperty('--study-text-scale'));
  await page.locator(`.preview-nav a[href="#${c.id}"]`).click();
  await page.reload();
  check(await page.locator('.preview-case:visible').getAttribute('id')===c.id,'Case reload '+c.id);
  const summary=page.locator('.preview-case:visible details.preview-section').first().locator(':scope > summary');
  await summary.focus();await page.keyboard.press('Enter');
  check(await summary.evaluate(el=>el.parentElement.open),'Keyboard expands '+c.id);
 }
 // Direct links also activate the correct exam; same-fragment clicks reopen a section.
 const a='ap-r07a-pm6--q5-i-join',b='ap-r07h-pm6--q2-d-join';
 await page.goto(url+'#'+a);await page.waitForFunction(id=>document.activeElement.id===id,a);
 await page.locator(`[id="${a}"]`).evaluate(el=>el.closest('details.preview-section').open=false);
 await page.locator(`.preview-question-link[href="#${a}"]`).click();
 check(await page.locator(`[id="${a}"]`).isVisible(),'Same fragment reopens');
 await page.locator('.preview-nav a[href="#ap-r07h-pm6"]').click();
 await page.locator(`.preview-question-link[href="#${b}"]`).click();
 await page.goBack();await page.goBack();
 await page.waitForFunction(id=>document.activeElement.id===id,a);
 await page.goForward();await page.goForward();
 await page.waitForFunction(id=>document.activeElement.id===id,b);
 for(const [anchor,width,name] of [['ap-r07a-pm1--q3-2-deterrence',320,'security-320'],['ap-r07a-pm6--q5-i-join',390,'database-390'],['ap-r07a-pm9--q3-1-d-days',1440,'management-1440'],['ap-r07a-pm3--q1-length',320,'algorithm-320'],['ap-r07a-pm5--q2-1-nat',390,'network-390'],['ap-r07a-pm11--q3-3-e-support',1440,'audit-1440'],['ap-r07a-pm2--q2-1-market',320,'strategy-320'],['ap-r07a-pm4--q4-1-energy',390,'edge-energy-390'],['ap-r07a-pm7--q3-3-g-increase',1440,'feeder-1440'],['ap-r07a-pm8--q1-2-regex',320,'mobile-ui-320'],['ap-r07a-pm10--q2-2-c-stop',390,'service-sla-390'],['ap-r07a-pm10--q4-1-frequency',1440,'service-faq-1440'],['ap-r06a-pm1--q6-1-pepper',320,'2024-password-320'],['ap-r06a-pm2--q1-1-ab-chain',390,'2024-chain-390'],['ap-r06a-pm2--q2-3-manual',1440,'2024-manual-1440'],['ap-r06a-pm3--q3-de-index',320,'2024-prime-index-320'],['ap-r06a-pm3--q4-l23-count',390,'2024-prime-count-390'],['ap-r06a-pm4--q2-2-e-reply',1440,'2024-placement-1440'],['ap-r06a-pm5--q1-2-source',320,'2024-gateway-source-320'],['ap-r06a-pm6--q2-h-like',390,'2024-recursive-sql-390'],['ap-r06a-pm6--q3-2-indexes',1440,'2024-indexes-1440'],['ap-r06a-pm7--q2-frequency',320,'2024-earphone-frequency-320'],['ap-r06a-pm8--q1-abc-oop',390,'2024-oop-390'],['ap-r06a-pm8--q2-3-gh-compose',1440,'2024-composition-1440'],['ap-r06a-pm9--q3-1-ab-risks',320,'2024-project-risks-320'],['ap-r06a-pm10--q4-effort',390,'2024-desk-effort-390'],['ap-r06a-pm10--q3-kpi',1440,'2024-desk-kpi-1440'],['ap-r06a-pm11--q1-2-c-level',320,'2024-audit-level-320'],['ap-r06h-pm1--q4-1-edr',390,'2024-remote-edr-390'],['ap-r06h-pm1--q4-2-b-mfa',1440,'2024-remote-mfa-1440'],['ap-r06h-pm2--q3-2-3pl',320,'2024-logistics-3pl-320'],['ap-r06h-pm3--q1-a-distance',390,'2024-dijkstra-trace-390'],['ap-r06h-pm3--q4-2-ku-cost',1440,'2024-dijkstra-cost-1440'],['ap-r06h-pm5--q2-2-update',320,'2024-weather-update-320'],['ap-r06h-pm4--q4-b-cpu',390,'2024-crm-cpu-390'],['ap-r06h-pm4--q2-2-json',1440,'2024-crm-json-1440'],['ap-r06h-pm7--q2-3-waveform',320,'2024-coffee-waveform-320'],['ap-r06h-pm7--q1-2-timer',390,'2024-coffee-timer-390'],['ap-r06h-pm6--q3-ef-view',1440,'2024-hr-view-1440'],['ap-r06h-pm8--q6-f-refresh',320,'2024-dashboard-refresh-320'],['ap-r06h-pm9--q2-3-bc-baselines',390,'2024-iot-baselines-390'],['ap-r06h-pm8--q4-de-dispatch',1440,'2024-dashboard-dispatch-1440'],['ap-r06h-pm10--q2-4-remote',320,'2024-telework-remote-320'],['ap-r06h-pm11--q4-h-offset',390,'2024-audit-offset-390'],['ap-r06h-pm11--q3-f-reconcile',1440,'2024-audit-reconcile-1440'],['ap-r05a-pm1--q2-2-encryption',320,'2023-mail-encryption-320'],['ap-r05a-pm2--q2-1-seci',390,'2023-seci-390'],['ap-r05a-pm2--q3-roe',1440,'2023-roe-1440'],['ap-r05a-pm3--q2-2-insertion',320,'2023-avl-320'],['ap-r05a-pm4--q1-2-interfaces',390,'2023-integration-390'],['ap-r05a-pm4--q3-saas',1440,'2023-accounting-saas-1440'],['ap-r05a-pm5--q2-dns',320,'2023-dns-320'],['ap-r05a-pm6--q2-3-reserved-stock',390,'2023-reserved-stock-390'],['ap-r05a-pm6--q3-window',1440,'2023-sql-window-1440'],['ap-r05a-pm7--q3-pwm',320,'2023-robot-pwm-320'],['ap-r05a-pm7--q4-echo',390,'2023-robot-echo-390'],['ap-r05a-pm8--q3-4-timing',1440,'2023-thread-timing-1440'],['ap-r05a-pm9--q2-1-vendors',320,'2023-vendors-320'],['ap-r05a-pm10--q2-3-recovery',390,'2023-service-recovery-390'],['ap-r05a-pm10--q3-2-faq',1440,'2023-service-faq-1440'],['ap-r05a-pm11--q4-cutover',320,'2023-audit-cutover-320'],['ap-r05h-pm1--s4-1-report',390,'2023-incident-report-390'],['ap-r05h-pm1--s4-2-backup',1440,'2023-malware-backup-1440'],['ap-r05h-pm2--s2-1-reallocate',320,'2023-strategy-staff-320'],['ap-r05h-pm3--s3-indexes',390,'2023-karatsuba-index-390'],['ap-r05h-pm3--s2-combine',1440,'2023-karatsuba-combine-1440'],['ap-r05h-pm4--s2-ef-article',390,'2023-news-calls-390'],['ap-r05h-pm5--s3-1-d-ttl',320,'2023-dns-ttl-320'],['ap-r05h-pm5--s3-3-sessions',1440,'2023-dns-sessions-1440'],['ap-r05h-pm6--s2-1-cd-joins',390,'2023-kpi-joins-390'],['ap-r05h-pm6--s2-1-hi-average',1440,'2023-kpi-average-1440'],['ap-r05h-pm7--s2-current',320,'2023-tag-current-320'],['ap-r05h-pm8--s3-revert',390,'2023-spring-revert-390'],['ap-r05h-pm9--s2-1-approval',320,'2023-spring-approval-320'],['ap-r05h-pm9--s3-1-risk',1440,'2023-spring-risk-1440'],['ap-r05h-pm10--s2-1-availability',390,'2023-spring-availability-390'],['ap-r05h-pm11--s5-fg-stocktake',320,'2023-spring-stocktake-320'],['ap-r05h-pm11',1440,'2023-spring-audit-intro-1440'],['ap-r04a-pm1--q2-1-hosts',320,'2022-autumn-hosts-320'],['ap-r04a-pm1--q2-3-spf',390,'2022-autumn-spf-390'],['ap-r04a-pm2--q4-2-financial-plan',1440,'2022-autumn-finance-1440'],['ap-r04a-pm3--q4-2-moves',320,'2022-autumn-maze-320'],['ap-r04a-pm4--q3-1-port',390,'2022-autumn-container-port-390'],['ap-r04a-pm4--q2-2-versions',1440,'2022-autumn-container-versions-1440'],['ap-r04a-pm5--q3-2-bandwidth',320,'2022-autumn-bandwidth-320'],['ap-r04a-pm6--q1-b-contract',390,'2022-autumn-contract-er-390'],['ap-r04a-pm6--q3-k-default',1440,'2022-autumn-plan-sql-1440'],['ap-r04a-pm7--q1-1-b-interval',320,'2022-autumn-sensor-320'],['ap-r04a-pm8--q1-1-methods',390,'2022-autumn-review-methods-390'],['ap-r04a-pm8--q3-2-zone',1440,'2022-autumn-review-zones-1440'],['ap-r04a-pm9--q3-2-expectation',320,'2022-autumn-risk-expectation-320'],['ap-r04a-pm10--q3-1-d-jobs',390,'2022-autumn-job-workload-390'],['ap-r04a-pm10--q3-2-budget',1440,'2022-autumn-service-budget-1440'],['ap-r04a-pm11--q3-loss-deadline',320,'2022-autumn-audit-deadline-320'],['ap-r04h-pm1--q2-waf',390,'2022-spring-incident-waf-390'],['ap-r04h-pm1--q4-5-siem',1440,'2022-spring-incident-siem-1440'],['ap-r04h-pm2--q2-2-strategy',320,'2022-spring-game-strategy-320'],['ap-r04h-pm3--q2-i-frame',390,'2022-spring-puzzle-frame-390'],['ap-r04h-pm3--q3-ab-restore',1440,'2022-spring-puzzle-restore-1440'],['ap-r04h-pm4--q3-efg-pricing',320,'2022-spring-cloud-pricing-320'],['ap-r04h-pm5--q1-3-firewall',390,'2022-spring-network-firewall-390'],['ap-r04h-pm5--q3-1-next-hop',1440,'2022-spring-network-next-hop-1440'],['ap-r04h-pm6--q3-lock',320,'2022-spring-coupon-lock-320'],['ap-r04h-pm7--q2-outage',390,'2022-spring-camera-outage-390'],['ap-r04h-pm7--q3-1-states',1440,'2022-spring-camera-states-1440'],['ap-r04h-pm8--q1-2-format',320,'2022-spring-bus-format-320'],['ap-r04h-pm9--q2-1-contracts',390,'2022-spring-contracts-390'],['ap-r04h-pm9--q3-3-browsers',1440,'2022-spring-browser-risk-1440'],['ap-r04h-pm10--q2-1-target',320,'2022-spring-incident-target-320'],['ap-r04h-pm11--q4-gh-inventory',390,'2022-spring-audit-inventory-390'],['ap-r04h-pm11--q4-ef-premise',1440,'2022-spring-audit-premise-1440']]){
  await page.setViewportSize({width,height:1000});await page.goto(url+'#'+anchor);
  await page.waitForFunction(id=>document.activeElement.id===id,name==='2023-spring-audit-intro-1440'?anchor+'-title':anchor);
  if(name==='2023-spring-audit-intro-1440'){
   const opening=page.locator('#ap-r05h-pm11 .explanation > p').first();
   const text=await opening.innerText();
   check(await opening.isVisible()&&text.includes('Y社')&&text.includes('監査の目的'),'Inventory audit introduction');
  }
  if(name==='2023-karatsuba-index-390'){
   const text=await page.locator('[id="ap-r05h-pm3--s3-indexes"]').locator('..').innerText();
   check(text.includes('「3*(i － 1)」')&&!text.includes('**3*'),'Karatsuba index expression');
  }
  if(name==='2022-spring-puzzle-frame-390'){
   const text=await page.locator('[id="ap-r04h-pm3--q2-i-frame"]').locator('..').innerText();
   check(text.includes('「mod(div(x, 9)*9, 27)」')&&!text.includes('**mod(div(x, 9)'),'Puzzle frame expression renders literally');
  }
  await page.screenshot({path:join(art,name+'.png')});
 }
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(url+'#ap-r07a-pm3--q1-length');
 const tableScroll=page.locator('[id="ap-r07a-pm3--q1-length"]').locator('..').locator('.question-table-scroll');
 await tableScroll.scrollIntoViewIfNeeded();
 await tableScroll.screenshot({path:join(art,'lcs-table-1440.png')});
 await page.setViewportSize({width:320,height:1000});
 check(await tableScroll.evaluate(el=>el.scrollWidth>el.clientWidth),'Mobile LCS table has local scrolling');
 await tableScroll.evaluate(el=>el.scrollLeft=el.scrollWidth);
 check(await tableScroll.evaluate(el=>el.scrollLeft>0),'Mobile LCS table can scroll horizontally');
 await tableScroll.screenshot({path:join(art,'lcs-table-320-scrolled.png')});
 await page.goto(url+'#ap-r05a-pm3--q2-2-insertion');
 const avlDiagram=page.locator('[id="ap-r05a-pm3--q2-2-insertion"]').locator('..').locator(':scope > .preview-detail > pre code');
 check((await avlDiagram.textContent()).trim()==='5\n├─ 左 3\n│  ├─ 左 1\n│  └─ 右 4\n└─ 右 8\n   ├─ 左 6\n   └─ 右 9','AVL diagram preserves the tree and connecting branches');
 await avlDiagram.screenshot({path:join(art,'2023-avl-diagram-320.png')});
 for(const [anchor,width,name,selector] of [['ap-r06a-pm3--q3-de-index',320,'2024-prime-index-scrolled','.question-table-scroll'],['ap-r06a-pm3--q4-l23-count',390,'2024-prime-count-scrolled','.question-table-scroll'],['ap-r06a-pm5--q1-2-source',320,'2024-gateway-source-scrolled','.question-table-scroll'],['ap-r06a-pm6--q2-h-like',390,'2024-recursive-sql-scrolled','pre'],['ap-r06a-pm6--q3-2-indexes',1440,'2024-indexes-scrolled','.question-table-scroll'],['ap-r06a-pm7--q2-frequency',320,'2024-earphone-frequency-scrolled','.question-table-scroll'],['ap-r06a-pm9--q3-1-ab-risks',320,'2024-project-risks-scrolled','.question-table-scroll'],['ap-r06a-pm10--q4-effort',390,'2024-desk-effort-scrolled','.question-table-scroll'],['ap-r06a-pm11--q2-1-e-performance',320,'2024-audit-performance-scrolled','.question-table-scroll'],['ap-r06h-pm1--q1-boundary',390,'2024-remote-boundary-scrolled','.question-table-scroll'],['ap-r06h-pm3--q1-a-distance',320,'2024-dijkstra-trace-scrolled','.question-table-scroll'],['ap-r06h-pm5--q2-2-update',320,'2024-weather-rules-scrolled','.question-table-scroll'],['ap-r06h-pm7--q2-3-waveform',320,'2024-coffee-waveform-scrolled','.question-table-scroll'],['ap-r06h-pm9--q2-4-scale',320,'2024-iot-test-cases-scrolled','.question-table-scroll'],['ap-r06h-pm10--q2-4-remote',320,'2024-telework-remote-scrolled','.question-table-scroll'],['ap-r05a-pm2--q2-1-seci',320,'2023-seci-scrolled','.question-table-scroll'],['ap-r05a-pm4--q1-2-interfaces',320,'2023-integration-scrolled','.question-table-scroll'],['ap-r05a-pm6--q3-window',320,'2023-sql-window-scrolled','pre'],['ap-r05a-pm8--q3-4-timing',320,'2023-thread-timing-scrolled','.question-table-scroll'],['ap-r05a-pm10--q2-3-recovery',320,'2023-service-recovery-scrolled','.question-table-scroll'],['ap-r05a-pm11--q4-cutover',320,'2023-audit-cutover-scrolled','.question-table-scroll'],['ap-r05h-pm3--s1-split',320,'2023-karatsuba-tree-scrolled','.question-table-scroll'],['ap-r05h-pm4--s2-ef-article',320,'2023-news-timing-scrolled','.question-table-scroll'],['ap-r05h-pm7--s2-current',320,'2023-tag-current-scrolled','.question-table-scroll'],['ap-r05h-pm9--s3-1-risk',320,'2023-spring-risk-scrolled','.question-table-scroll'],['ap-r05h-pm11--s2-source',320,'2023-spring-audit-source-scrolled','.question-table-scroll'],['ap-r04a-pm2--q4-2-financial-plan',320,'2022-autumn-finance-scrolled','.question-table-scroll'],['ap-r04a-pm3--q4-2-moves',320,'2022-autumn-maze-scrolled','.question-table-scroll'],['ap-r04a-pm5--q3-2-bandwidth',320,'2022-autumn-bandwidth-scrolled','.question-table-scroll'],['ap-r04a-pm7--q1-1-b-interval',320,'2022-autumn-sensor-scrolled','.question-table-scroll'],['ap-r04a-pm9--q3-2-expectation',320,'2022-autumn-risk-expectation-scrolled','.question-table-scroll'],['ap-r04a-pm11--q3-loss-deadline',320,'2022-autumn-audit-deadline-scrolled','.question-table-scroll:has-text("8月17日")'],['ap-r04h-pm2--q2-2-strategy',320,'2022-spring-game-strategy-scrolled','.question-table-scroll:has-text("1,200")'],['ap-r04h-pm4--q3-efg-pricing',320,'2022-spring-cloud-pricing-scrolled','.question-table-scroll:has-text("50ミリ秒")'],['ap-r04h-pm6--q3-lock',320,'2022-spring-coupon-lock-scrolled','.question-table-scroll:has-text("確認する場面")'],['ap-r04h-pm8--q1-2-format',320,'2022-spring-bus-format-scrolled','.question-table-scroll:has-text("G0030110")'],['ap-r04h-pm10--q2-1-target',320,'2022-spring-incident-target-scrolled','.question-table-scroll:has-text("130分")']]){
  await page.setViewportSize({width,height:1000});
  await page.goto(url+'#'+anchor);
  await page.waitForFunction(id=>document.activeElement.id===id,anchor);
  const table=page.locator(`[id="${anchor}"]`).locator('..').locator(selector).first();
  check(await table.evaluate(el=>el.scrollWidth>el.clientWidth),'Current prime table local overflow '+anchor);
  await table.evaluate(el=>el.scrollLeft=el.scrollWidth);
  check(await table.evaluate(el=>el.scrollLeft>0),'Current prime table can scroll '+anchor);
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Prime table keeps page inside viewport');
  await table.screenshot({path:join(art,name+'.png')});
 }
 await page.setViewportSize({width:390,height:1000});
 await page.goto(url+'#ap-r07a-pm4--q2-1-c-rate');
 const mathSource=page.locator('[id="ap-r07a-pm4--q2-1-c-rate"]').locator('..').locator('.preview-source-question');
 await mathSource.locator('summary').click();
 check(await mathSource.locator('.katex').count()===1,'One rendered power of ten');
 check(await mathSource.locator('annotation[encoding="application/x-tex"]').textContent()==='10^9','Original power of ten preserved');
 check(await mathSource.locator('.katex-mathml').evaluate(el=>getComputedStyle(el).position==='absolute'&&getComputedStyle(el).width==='1px'),'KaTeX accessibility math is visually hidden');
 check(await mathSource.locator('.katex-html').isVisible(),'KaTeX visual math is visible');
 await page.screenshot({path:join(art,'edge-math-390.png')});
 check(await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--navy').trim())==='#142d4e','Shared palette');
 check(errors.length===0,'Browser errors '+errors);check(failedRequests.length===0,'Failed requests '+failedRequests);
 check(sha(await readFile(new URL('preview.html',import.meta.url)))===previewSHA256,'Preview changed during browser checks');
 const result={status:'passed',previewSHA256,caseCount:cases.length,explanationLinks:links,layouts,deepLinksHistorySameFragmentKeyboard:true,lcsTableLocalScroll:true,currentPrimeTablesLocalScroll:true,currentGatewaySqlIndexLocalScroll:true,currentEarphoneLocalScroll:true,currentProjectDeskLocalScroll:true,currentAuditBoundaryLocalScroll:true,dijkstraTraceLocalScroll:true,weatherRulesLocalScroll:true,coffeeWaveformLocalScroll:true,iotTestCasesLocalScroll:true,teleworkRemoteLocalScroll:true,seciLocalScroll:true,integrationInterfacesLocalScroll:true,inventorySqlLocalScroll:true,threadTimingLocalScroll:true,serviceRecoveryLocalScroll:true,contingencyCutoverLocalScroll:true,karatsubaTreeLocalScroll:true,newsTimingLocalScroll:true,tagCurrentLocalScroll:true,migrationRiskLocalScroll:true,inventorySourceLocalScroll:true,financialPlanLocalScroll:true,bandwidthTableLocalScroll:true,sensorTableLocalScroll:true,riskCostTableLocalScroll:true,auditDeadlineTableLocalScroll:true,gameStrategyTableLocalScroll:true,cloudPricingTableLocalScroll:true,couponLockTableLocalScroll:true,busFormatTableLocalScroll:true,incidentTimelineLocalScroll:true,mathSourceAndStyles:true,consoleErrors:errors,failedRequests,screenshots:art,scope:'Local editorial library only; no app integration or learner testing.'};
 await writeFile(join(here,'browser-checks.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({status:result.status,cases:cases.length,links:links.length,fields:links.flatMap(x=>x.fieldIds).length,layouts:layouts.length,screenshots:art}));
}finally{
 await browser?.close();await new Promise(done=>server.close(done));
}
