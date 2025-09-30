const routes=["home","simulate","summary","view"];
const navLinks=document.querySelectorAll('.nav-link');
navLinks.forEach(l=>l.addEventListener('click',e=>{
  navLinks.forEach(n=>n.classList.remove('active'));
  e.target.classList.add('active');
  const route=e.target.getAttribute('href').replace('#','');
  showRoute(route)
}));

function showRoute(id){
  routes.forEach(r=>{document.getElementById(r).classList.add('hidden')});
  document.getElementById(id).classList.remove('hidden')
}

async function uploadAndParse(endpoint,file){
  const form=new FormData();
  form.append('file',file);
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),30000);
  let res;
  try{
    res=await fetch(endpoint,{method:'POST',body:form,signal:controller.signal});
  } finally {
    clearTimeout(timeout);
  }
  if(!res.ok){
    const err=await res.json().catch(()=>({detail:'Unknown error'}));
    throw new Error(err.detail||'Upload failed')
  }
  return res.json()
}

document.getElementById('btnProcess').addEventListener('click',async()=>{
  const spec=document.getElementById('specFile').files[0];
  const edi=document.getElementById('ediFile').files[0];
  const error=document.getElementById('error');
  const btn=document.getElementById('btnProcess');
  error.textContent='';
  if(!spec||!edi){
    error.textContent='Please select both files.';
    return
  }
  try{
    btn.disabled=true; btn.textContent='Processing...';
    const [specXml,ediXml]=await Promise.all([
      uploadAndParse('/api/parse/spec',spec),
      uploadAndParse('/api/parse/edi',edi)
    ]);
    const compareRes=await fetch('/api/compare',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        edi_xml: ediXml.xml,
        spec_xml: specXml.xml,
        edi_fields: ediXml.fields || [],
        spec_requirements: specXml.requirements || {}
      })
    });
    if(!compareRes.ok){
      const err=await compareRes.json().catch(()=>({detail:'Compare failed'}));
      throw new Error(err.detail||'Compare failed')
    }
    const result=await compareRes.json();
    // store XML for viewing tab
    window.__lastSpecXml=specXml.xml;
    window.__lastEdiXml=ediXml.xml;
    renderSummary(result);
    showRoute('summary')
  }catch(e){
    error.textContent=e.message
  }finally{
    btn.disabled=false; btn.textContent='Process';
  }
});

function renderSummary(result){
  const summary=document.getElementById('summaryContent');
  window.__comparison=result;
  summary.innerHTML=`<div class="pill">810 Valid: ${result.is_810}</div>
<h3 id="summaryTitle">Mandatory (M)</h3>${tableFrom(result.mandatory_fields,'Mandatory')}`;
  // Default view shows mandatory fields
  activateFilters();
  // Viewing: show XML side-by-side
  document.getElementById('specXML').textContent=(window.__lastSpecXml||'').trim();
  document.getElementById('ediXML').textContent=(window.__lastEdiXml||'').trim();
}

function tableFrom(items,label){
  if(!items||items.length===0){return '<p class="pill">None</p>'}
  const rows=items.map(i=>`<tr><td>${i}</td><td>${label}</td></tr>`).join('');
  return `<table class="table"><thead><tr><th>Field</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`
}

function activateFilters(){
  const result=window.__comparison||{};
  const map={
    mandatory:{list:result.mandatory_fields||[], label:'Mandatory (M)'},
    optional:{list:result.optional_fields||[], label:'Optional (O)'},
    missing:{list:result.missing_mandatory||[], label:'Missing'},
  };
  const buttons=[...document.querySelectorAll('.filter-btn')];
  const search=document.getElementById('searchField');
  const out=document.getElementById('summaryContent');
  const title=document.getElementById('summaryTitle');
  function render(type){
    buttons.forEach(b=>b.classList.toggle('active', b.dataset.type===type));
    const q=(search.value||'').trim().toUpperCase();
    const items=(map[type]?.list||[]).filter(x=>!q || x.toUpperCase().includes(q));
    title.textContent=map[type]?.label||'Summary';
    out.innerHTML=`<div class="pill">810 Valid: ${result.is_810}</div>`+tableFrom(items, map[type]?.label||'');
  }
  buttons.forEach(b=>b.onclick=()=>render(b.dataset.type));
  search.oninput=()=>{
    const active=(buttons.find(b=>b.classList.contains('active'))?.dataset.type)||'mandatory';
    render(active)
  };
  render('mandatory');
}


