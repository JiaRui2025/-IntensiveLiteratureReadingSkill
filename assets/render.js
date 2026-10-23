
const ALL = UNITS.concat(UNITS_B);

/* ---- render units ---- */
function esc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function unitHTML(u){
  const cards = u.sent.map((s,idx)=>{
    const id = 'c-'+u.id+'-'+s.i;
    return '<div class="card" id="'+id+'" data-s="'+u.id+'-'+s.i+'">'
      + '<div class="sh"><span class="no">'+(idx+1)+'</span><span class="tx">'+esc(s.tx)+'</span></div>'
      + '<div class="row2 g"><div class="lb">语法骨架</div><div class="vv">'+s.g+'</div></div>'
      + '<div class="row2 l"><div class="lb">逻辑功能</div><div class="vv">'+s.l+'</div></div>'
      + '<div class="row2 t"><div class="lb">可复用模板</div><div class="vv"><span class="tpl">'+s.t+'</span><button class="copy" type="button">复制</button></div></div>'
      + (s.n ? '<div class="row2 n"><div class="lb">细节 · 提醒</div><div class="vv">'+s.n+'</div></div>' : '')
      + '</div>';
  }).join('');

  return '<section class="unit" id="'+u.id+'">'
    + '<div class="hd"><span class="u">'+u.tag+'</span><span class="t">'+u.zh+'</span><span class="e">'+u.en+'</span></div>'
    + '<div class="body">'
    + '<div class="job">'+u.job+'</div>'
    + '<p class="src">'+u.para+'</p>'
    + '<p class="srcmark">↑ 点击任意句子跳到分析　·　共 '+u.sent.length+' 句</p>'
    + '<div class="cards">'+cards+'</div>'
    + '</div></section>';
}
document.getElementById('unitlist').innerHTML = ALL.map(unitHTML).join('');

/* ---- nav ---- */
function navLabel(u){
  var t = u.zh.split(' · ').pop();
  t = t.replace(/（[^）]*）/g,'').trim();
  return u.tag + ' · ' + t;
}
document.getElementById('navunits').innerHTML = ALL.map(u =>
  '<a href="#'+u.id+'">'+navLabel(u)+'</a>').join('');

/* ---- bind sentences ---- */
document.querySelectorAll('.unit').forEach(unit=>{
  const uid = unit.id;
  unit.querySelectorAll('.src .sn').forEach(sn=>{
    const i = sn.getAttribute('data-i');
    if(i===null) return;
    sn.dataset.s = uid+'-'+i;
    sn.insertAdjacentHTML('beforeend','<sup class="ix">'+(parseInt(i,10)+1)+'</sup>');
    sn.addEventListener('click',()=>{
      const card = document.getElementById('c-'+uid+'-'+i);
      if(!card) return;
      document.querySelectorAll('.src .sn.active').forEach(e=>e.classList.remove('active'));
      sn.classList.add('active');
      card.classList.remove('flash');
      void card.offsetWidth;
      card.classList.add('flash');
      card.scrollIntoView({behavior:'smooth',block:'center'});
    });
  });
});

/* ---- copy ---- */
document.querySelectorAll('.copy').forEach(btn=>{
  btn.addEventListener('click',e=>{
    e.stopPropagation();
    const tpl = btn.parentElement.querySelector('.tpl');
    const txt = tpl ? tpl.textContent : '';
    navigator.clipboard.writeText(txt).then(()=>{
      btn.textContent='已复制';
      setTimeout(()=>btn.textContent='复制',1200);
    }).catch(()=>{
      btn.textContent='请手动选择';
      setTimeout(()=>btn.textContent='复制',1500);
    });
  });
});

/* ---- progress + nav highlight ---- */
const prog = document.getElementById('progress');
window.addEventListener('scroll',()=>{
  const h = document.documentElement;
  const p = h.scrollTop / (h.scrollHeight - h.clientHeight) * 100;
  prog.style.width = p + '%';
},{passive:true});

const links = Array.from(document.querySelectorAll('nav a'));
const targets = links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
const io = new IntersectionObserver(entries=>{
  entries.forEach(en=>{
    if(en.isIntersecting){
      links.forEach(a=>a.classList.remove('on'));
      const l = links.find(a=>a.getAttribute('href')==='#'+en.target.id);
      if(l) l.classList.add('on');
    }
  });
},{rootMargin:'-15% 0px -75% 0px'});
targets.forEach(t=>io.observe(t));
