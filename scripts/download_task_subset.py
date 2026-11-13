from range_reader import ParallelRangeReader
import tarfile,urllib.request,pathlib,json,time,shutil,csv,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
import yaml
cfg=yaml.safe_load((ROOT/'config.yaml').read_text())
root=ROOT/cfg['data_raw']
root.mkdir(parents=True,exist_ok=True)
url='https://zenodo.org/api/records/16754363/files/tasks_data.tar.gz/content'
status={'state':'进行中','source':url,'compressed_bytes_read':0,'selected_files':0,'selected_bytes':0,'categories':{},'skipped_large':[],'category_files':{}}
class Counter:
 def __init__(self,f):self.f=f;self.n=0
 def read(self,n=-1):
  b=self.f.read(n);self.n+=len(b);return b
out=root/'tasks_selected';out.mkdir(exist_ok=True)
last=0
try:
 with open(root/'tasks_archive_inventory.csv','w',buffering=1) as inv:
  r=ParallelRangeReader(url,3709424795);writer=csv.writer(inv);writer.writerow(['path','bytes','selected'])
  with tarfile.open(fileobj=r,mode='r|gz') as archive:
   for m in archive:
    if m.name.startswith('tasks_data/Zfold') and all(c in status['categories'] for c in ['nrc','bprna','archiveii','zeroshot']):
     status['archive_fully_scanned']=False
     status['stop_reason']='四类小文件已取得，停止后续 Zfold 大文件流'
     break
    low=m.name.lower();parts=pathlib.PurePosixPath(low).parts
    category=next((c for c in ['zeroshot','archiveii','bprna'] if c in low),None)
    if 'nrc' in parts:category='nrc'
    safe=not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts
    selected=bool(category and safe and m.isfile() and m.size<=64*1024**2 and status['categories'].get(category,0)+m.size<=512*1024**2)
    writer.writerow([m.name,m.size,selected])
    if selected:
     dest=out/m.name;dest.parent.mkdir(parents=True,exist_ok=True)
     with archive.extractfile(m) as source,open(dest,'wb') as target:shutil.copyfileobj(source,target)
     status['category_files'][category]=status['category_files'].get(category,0)+1
     status['selected_files']+=1;status['selected_bytes']+=m.size;status['categories'][category]=status['categories'].get(category,0)+m.size
    elif category and m.isfile():status['skipped_large'].append({'path':m.name,'bytes':m.size})
    if time.time()-last>5:
     status['compressed_bytes_read']=r.n;(root/'tasks_download_status.json').write_text(json.dumps(status,indent=2,ensure_ascii=False));last=time.time()
  status['compressed_bytes_read']=r.n;status['state']='完成';r.close()
except Exception as e:status['state']='失败';status['error']=str(e)
(root/'tasks_download_status.json').write_text(json.dumps(status,indent=2,ensure_ascii=False))
print(json.dumps(status,ensure_ascii=False))
