addEventListener('DOMContentLoaded', async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const wait = async fn => { const start = performance.now(); while (!fn()) { if (performance.now()-start>120000) throw Error('timeout'); await sleep(20); } };
  const grid = document.querySelector('#grid');
  const longTasks=[];
  try { new PerformanceObserver(list => longTasks.push(...list.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({type:'longtask',buffered:true}); } catch {}
  const result={ benchmark:true, variant:location.pathname, firstCards:0, firstVisible:0, allReady:0, searches:[] };
  try {
    await wait(()=>grid.children.length && grid.querySelector('button'));
    result.firstCards=performance.now();
    if(grid.querySelector('.material-symbol')) await document.fonts.load('40px "Material Symbols Outlined Local"');
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    result.firstVisible=performance.now();
    await wait(()=> !document.querySelector('#library-load-status') || /48\/48/.test(document.querySelector('#library-load-status').textContent));
    await wait(()=>grid.getAttribute('aria-busy')==='false');
    result.allReady=performance.now();
    // Turn off stored AI expansion in both runs via the app's own control.
    const ai=document.querySelector('#smart-search');if(ai.checked){ai.checked=false;ai.dispatchEvent(new Event('change',{bubbles:true}));await sleep(300);}
    const input=document.querySelector('#search');
    for(const q of ['cat','arrow','arrow down','home','face','a','search','heart','zznonexistent','']) {
      await sleep(100);
      const start=performance.now();
      const rendered=new Promise(resolve=>{
        const observer=new MutationObserver(()=>{if(grid.getAttribute('aria-busy')==='false'){observer.disconnect();requestAnimationFrame(()=>resolve(performance.now()));}});
        observer.observe(grid,{childList:true,attributes:true});
      });
      input.value=q;input.dispatchEvent(new Event('input',{bubbles:true}));
      const handler=performance.now()-start;
      const end=await rendered;
      result.searches.push({q,handlerMs:handler,resultMs:end-start,count:document.querySelector('#result-count').textContent});
    }
    result.longTasks=longTasks;
  } catch(error){result.error=error.message;}
  parent.postMessage(result,'*');
});
