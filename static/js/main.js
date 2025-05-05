document.addEventListener('DOMContentLoaded', ()=> {
  document.getElementById('preview-btn')?.addEventListener('click', ()=>{
    let opts = Array.from(document.querySelectorAll('input[name=opts]:checked'))
                    .map(i=>i.value).join(' ');
    let inc = document.getElementById('include').value
                    .split(',').filter(x=>x).map(x=>`--include='${x.trim()}'`).join(' ');
    let exc = document.getElementById('exclude').value
                    .split(',').filter(x=>x).map(x=>`--exclude='${x.trim()}'`).join(' ');
    let cmd = `rsync ${opts} ${inc} ${exc} <source> <destination>`;
    document.getElementById('cmd-preview').textContent = cmd;
  });
});
