import urllib.request,concurrent.futures,time
class ParallelRangeReader:
 def __init__(self,url,size,workers=48,block=2*1024**2):
  self.url=url;self.size=size;self.block=block;self.pool=concurrent.futures.ThreadPoolExecutor(workers);self.next=0;self.pos=0;self.buf=b'';self.idx=0;self.futures={};self.total=(size+block-1)//block
  for _ in range(min(workers,self.total)):self._submit()
 def _submit(self):
  i=self.next;self.next+=1;self.futures[i]=self.pool.submit(self._fetch,i)
 def _fetch(self,i):
  start=i*self.block;end=min(start+self.block,self.size)-1
  for attempt in range(12):
   try:
    req=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}'})
    with urllib.request.urlopen(req,timeout=90) as r:
     if r.status!=206:raise IOError('Range unsupported')
     expected=f'bytes {start}-{end}/{self.size}'
     if r.headers.get('Content-Range')!=expected:raise IOError('Content-Range mismatch')
     b=r.read()
    if len(b)!=end-start+1:raise IOError(f'short {len(b)} vs {end-start+1}')
    return b
   except Exception:
    if attempt==11:raise
    time.sleep(2)
 def read(self,n):
  out=bytearray()
  while len(out)<n:
   if not self.buf:
    if self.idx>=self.total:break
    self.buf=self.futures.pop(self.idx).result();self.idx+=1
    if self.next<self.total:self._submit()
   k=min(n-len(out),len(self.buf));out.extend(self.buf[:k]);self.buf=self.buf[k:];self.pos+=k
  return bytes(out)
 @property
 def n(self):return self.pos
 def close(self):self.pool.shutdown(wait=False,cancel_futures=True)
