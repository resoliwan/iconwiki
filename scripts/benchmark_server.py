import http.server, pathlib, gzip, time, threading, urllib.parse, json, argparse, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Local-only browser benchmark; this is not a production search server.')
parser.add_argument('--baseline',default='158100962b291034e9531e863bb06500e3ec2352')
parser.add_argument('--port',type=int,default=4175)
args=parser.parse_args()
baseline_dir=tempfile.TemporaryDirectory(prefix='iconwiki-baseline-')
BEFORE=pathlib.Path(baseline_dir.name)
for name in ['app.js','index.html','catalog.js','smart-search.js','styles.css']:
 (BEFORE/name).write_bytes(subprocess.check_output(['git','show',f'{args.baseline}:{name}'],cwd=ROOT))
lock=threading.Lock(); next_slot=0
RATE=1_250_000
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self):
  global next_slot
  url=urllib.parse.urlparse(self.path); path=url.path
  if path=='/benchmark':
   body=b'''<!doctype html><body><h1>Icon Wiki benchmark: 10 Mbps shared, 40 ms/request, gzip, no cache</h1><pre id="report">Running...</pre><iframe id="app" width="1200" height="750"></iframe><script>
   const runs=[]; let n=0; const frame=document.querySelector('iframe');
   function next(){if(n===6){document.querySelector('pre').textContent=JSON.stringify(runs,null,2); return;} frame.src=(n%2===0?'/before/':'/after/')+'?benchmark='+n; n++;}
   addEventListener('message',e=>{if(e.data.benchmark){runs.push(e.data);document.querySelector('pre').textContent=JSON.stringify(runs,null,2);next();}});next();</script>'''
   return self.send(body,'text/html',False)
  if path=='/bench.js': return self.send((ROOT/'scripts/benchmark_browser.js').read_bytes(),'text/javascript',False)
  variant='before' if path.startswith('/before/') else 'after'
  rel=path.removeprefix('/before/').removeprefix('/after/').lstrip('/') or 'index.html'
  file=(BEFORE/rel if variant=='before' and (BEFORE/rel).is_file() else ROOT/rel)
  if not file.resolve().is_relative_to(ROOT) and not file.resolve().is_relative_to(BEFORE): self.send_error(403);return
  if not file.is_file(): self.send_error(404);return
  body=file.read_bytes()
  if rel=='index.html' and 'benchmark=' in url.query:
   body=body.replace(b'<head>',b'<head><script src="/bench.js"></script>')
  mime='text/javascript' if file.suffix=='.js' else 'application/json' if file.suffix=='.json' else 'text/html' if file.suffix=='.html' else 'text/css' if file.suffix=='.css' else 'image/svg+xml' if file.suffix=='.svg' else 'font/woff2' if file.suffix=='.woff2' else 'application/octet-stream'
  self.send(body,mime,True)
 def send(self,body,mime,throttle):
  global next_slot
  body=gzip.compress(body,compresslevel=6)
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Encoding','gzip');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers()
  try:
   if throttle: time.sleep(.04)
   for i in range(0,len(body),16384):
    chunk=body[i:i+16384]
    if throttle:
     with lock:
      now=time.monotonic();slot=max(now,next_slot);next_slot=slot+len(chunk)/RATE
     time.sleep(max(0,slot-time.monotonic()))
    self.wfile.write(chunk)
  except (BrokenPipeError,ConnectionResetError): pass
print(f'Open http://127.0.0.1:{args.port}/benchmark',flush=True)
http.server.ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
