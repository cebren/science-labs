(function(){
  var scaler=document.querySelector('.dk-scaler'),stage=document.querySelector('.dk-stage');
  var slides=[].slice.call(scaler.children).filter(function(n){return n.tagName==='SECTION'});
  var count=document.querySelector('.dk-count'),prev=document.querySelector('.dk-prev'),next=document.querySelector('.dk-next');
  var notesBtn=document.querySelector('.dk-notes-btn'),notes=document.querySelector('.dk-notes'),notesBody=document.querySelector('.dk-notes-body');
  var i=0;
  function fit(){var s=stage.clientWidth/1920;scaler.style.transform='scale('+s+')';}
  function show(n,push){
    i=Math.max(0,Math.min(slides.length-1,n));
    slides.forEach(function(s,k){s.classList.toggle('on',k===i);s.setAttribute('aria-hidden',k===i?'false':'true');});
    count.textContent=(i+1)+' / '+slides.length;
    prev.disabled=i===0;next.disabled=i===slides.length-1;
    var a=slides[i].querySelector('aside');notesBody.textContent=a?a.textContent.trim():'No notes for this slide.';
    if(push!==false){try{history.replaceState(null,'','#'+(i+1));}catch(e){location.hash=String(i+1);}}
  }
  function fromHash(){var n=parseInt((location.hash||'').slice(1),10);return isNaN(n)?0:n-1;}
  prev.addEventListener('click',function(){show(i-1)});
  next.addEventListener('click',function(){show(i+1)});
  notesBtn.addEventListener('click',function(){var on=notes.hidden;notes.hidden=!on;notesBtn.setAttribute('aria-pressed',on?'true':'false');});
  document.addEventListener('keydown',function(e){
    if(e.target&&/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;
    if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){e.preventDefault();show(i+1);}
    else if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();show(i-1);}
    else if(e.key==='Home'){show(0);}else if(e.key==='End'){show(slides.length-1);}
  });
  var x0=null;
  stage.addEventListener('touchstart',function(e){x0=e.touches[0].clientX},{passive:true});
  stage.addEventListener('touchend',function(e){if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)show(i+(dx<0?1:-1));x0=null;});
  window.addEventListener('hashchange',function(){show(fromHash(),false)});
  window.addEventListener('resize',fit);
  if(window.ResizeObserver)new ResizeObserver(fit).observe(stage);
  fit();show(fromHash(),false);
})();
