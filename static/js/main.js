document.addEventListener('DOMContentLoaded', ()=> {
  // Theme toggle
  const themeToggle = document.getElementById('theme-toggle');
  const root = document.documentElement;
  const stored = localStorage.getItem('theme');
  if (stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    root.classList.add('dark');
  }
  themeToggle.addEventListener('click', () => {
    if (root.classList.contains('dark')) {
      root.classList.remove('dark'); localStorage.setItem('theme', 'light');
    } else {
      root.classList.add('dark'); localStorage.setItem('theme', 'dark');
    }
  });

  // Rsync builder (existing)
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
