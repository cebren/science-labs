// Usage: node _build/export_pptx.js <http url of a hosted deck page> <out.json> <imgdir>
// Measures every slide in a real browser and writes shapes, text runs and notes as JSON.
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const [url,out,imgdir]=process.argv.slice(2);
(async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 await p.goto(url,{waitUntil:'load'});
 await p.addStyleTag({content:'.dk-bar,.dk-ctrl,.dk-notes{display:none!important}.dk-stage-wrap{padding:0!important}.dk-stage{max-width:none!important;width:1920px!important;border-radius:0!important;box-shadow:none!important}.dk-scaler{transform:none!important}body{margin:0}'});
 const n=await p.evaluate(()=>document.querySelectorAll('.dk-scaler>section').length);
 fs.mkdirSync(imgdir,{recursive:true});
 const slides=[];
 for(let k=0;k<n;k++){
  await p.evaluate(k=>{document.querySelectorAll('.dk-scaler>section').forEach((s,i)=>s.classList.toggle('on',i===k));window.scrollTo(0,0);},k);
  await p.waitForTimeout(30);
  const data=await p.evaluate(()=>{
   const sec=document.querySelector('.dk-scaler>section.on');const R=sec.getBoundingClientRect();
   const rel=r=>({x:r.left-R.left,y:r.top-R.top,w:r.width,h:r.height});
   const col=c=>{const m=c&&c.match(/rgba?\(([^)]+)\)/);if(!m)return null;const v=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);if(v.length>3&&v[3]===0)return null;return {r:v[0],g:v[1],b:v[2],a:v.length>3?v[3]:1};};
   const shapes=[],texts=[],pics=[];let pid=0;
   const INLINE=new Set(['B','STRONG','I','EM','SPAN','A','SUB','SUP','BR','CODE','U','MARK','SMALL']);
   function runsOf(el){const runs=[];
     (function walk(node,inh){for(const c of node.childNodes){
       if(c.nodeType===3){if(c.textContent.length)runs.push({t:c.textContent,...inh});}
       else if(c.nodeType===1&&INLINE.has(c.tagName)){if(c.tagName==='BR'){runs.push({t:'\n',...inh});continue;}
         const cs=getComputedStyle(c);walk(c,{bold:+cs.fontWeight>=600,italic:cs.fontStyle==='italic',color:col(cs.color),size:parseFloat(cs.fontSize),font:cs.fontFamily.split(',')[0].replace(/["']/g,'').trim(),sup:c.tagName==='SUP',sub:c.tagName==='SUB'});}
     }})(el,(()=>{const cs=getComputedStyle(el);return {bold:+cs.fontWeight>=600,italic:cs.fontStyle==='italic',color:col(cs.color),size:parseFloat(cs.fontSize),font:cs.fontFamily.split(',')[0].replace(/["']/g,'').trim()};})());
     // collapse whitespace like HTML
     let s=runs.map(r=>({...r,t:r.t==='\n'?'\n':r.t.replace(/\s+/g,' ')}));
     if(s.length){s[0].t=s[0].t.replace(/^ /,'');s[s.length-1].t=s[s.length-1].t.replace(/ $/,'');}
     const tt=getComputedStyle(el).textTransform;if(tt==='uppercase')s.forEach(r=>r.t=r.t.toUpperCase());
     return s.filter(r=>r.t.length);}
   const all=[sec,...sec.querySelectorAll('*')];
   for(const el of all){
     if(el.closest('aside'))continue;
     const cs=getComputedStyle(el);if(cs.display==='none'||cs.visibility==='hidden')continue;
     const r=el.getBoundingClientRect();if(r.width<1||r.height<1)continue;
     const box=rel(r);
     if(['IMG','SVG','CANVAS','VIDEO','svg'].includes(el.tagName)||el.tagName.toLowerCase()==='svg'){el.setAttribute('data-pic',String(pid));pics.push({id:pid++,...box});continue;}
     if(el.closest('svg'))continue;
     if(el.tagName==='X-SHAPE'){shapes.push({kind:el.getAttribute('kind')||'rect',fill:col(cs.backgroundColor),...box});continue;}
     if(el!==sec){
      const bg=col(cs.backgroundColor);
      const bw=['Top','Right','Bottom','Left'].map(s=>parseFloat(cs['border'+s+'Width'])||0);
      const bc=['Top','Right','Bottom','Left'].map(s=>col(cs['border'+s+'Color']));
      const allSame=bw.every(w=>w===bw[0])&&bw[0]>0&&bc[0];
      const rad=parseFloat(cs.borderTopLeftRadius)||0;
      if(bg||allSame)shapes.push({kind:'rect',fill:bg,line:allSame?{w:bw[0],c:bc[0]}:null,rad,...box});
      if(!allSame){['Top','Right','Bottom','Left'].forEach((s,i)=>{if(bw[i]>0&&bc[i]){const L={kind:'line',c:bc[i],w:bw[i]};
        if(i===0)Object.assign(L,{x1:box.x,y1:box.y,x2:box.x+box.w,y2:box.y});
        if(i===2)Object.assign(L,{x1:box.x,y1:box.y+box.h,x2:box.x+box.w,y2:box.y+box.h});
        if(i===1)Object.assign(L,{x1:box.x+box.w,y1:box.y,x2:box.x+box.w,y2:box.y+box.h});
        if(i===3)Object.assign(L,{x1:box.x,y1:box.y,x2:box.x,y2:box.y+box.h});shapes.push(L);}});}
     }
     // text block: element with direct non-empty text or inline children, and not itself inline inside a text block
     if(INLINE.has(el.tagName)&&el.parentElement&&el.parentElement!==sec)continue;
     const hasText=[...el.childNodes].some(c=>(c.nodeType===3&&c.textContent.trim())||(c.nodeType===1&&INLINE.has(c.tagName)&&c.textContent.trim()));
     if(!hasText)continue;
     const pl=parseFloat(cs.paddingLeft)||0,pr=parseFloat(cs.paddingRight)||0,pt=parseFloat(cs.paddingTop)||0,pb=parseFloat(cs.paddingBottom)||0;
     const bl=parseFloat(cs.borderLeftWidth)||0,bt=parseFloat(cs.borderTopWidth)||0;
     const lh=cs.lineHeight==='normal'?1.2:parseFloat(cs.lineHeight)/parseFloat(cs.fontSize);
     texts.push({x:box.x+pl+bl,y:box.y+pt+bt,w:box.w-pl-pr-bl*2,h:box.h-pt-pb-bt*2,align:cs.textAlign,lh,ls:parseFloat(cs.letterSpacing)||0,runs:runsOf(el)});
   }
   const aside=sec.querySelector('aside');
   return {bg:col(getComputedStyle(sec).backgroundColor),shapes,texts,pics,notes:aside?aside.textContent.trim():''};
  });
  for(const pc of data.pics){const f=path.join(imgdir,`s${k}-p${pc.id}.png`);await p.locator(`.dk-scaler>section.on [data-pic="${pc.id}"]`).first().screenshot({path:f,omitBackground:true}).catch(()=>{});pc.file=f;}
  slides.push(data);
 }
 fs.writeFileSync(out,JSON.stringify({slides}));
 await b.close();console.log('measured',n,'slides');
})();
