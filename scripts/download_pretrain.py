#!/usr/bin/env python
"""断点续传 README 版预训练包。只下载，不解压，不训练。"""
from pathlib import Path
import urllib.request
import hashlib
import shutil
import time
import yaml

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((ROOT/'config.yaml').read_text())
raw = ROOT/cfg['data_raw']
raw.mkdir(parents=True,exist_ok=True)
if shutil.disk_usage(raw).free < 20*10**9:
    raise SystemExit('可用空间不足20GB，跳过大包')
name = 'RNAcentral_512_SS_connects.csv.tar.gz'
size = 4456225221
path = raw/name
url = 'https://zenodo.org/api/records/16754363/files/'+name+'/content'
with (raw/'download.log').open('a',buffering=1) as log:
    failures = 0
    while True:
        try:
            n = path.stat().st_size if path.exists() else 0
            if n == size:
                expected = '24c6c7789fe366299ae00640f5f1a744'
                md5 = hashlib.md5()
                with path.open('rb') as inp:
                    for chunk in iter(lambda: inp.read(8*1024**2), b''):
                        md5.update(chunk)
                digest = md5.hexdigest()
                if digest != expected:
                    raise ValueError('完整文件 MD5 不匹配，请保留日志后重新下载')
                log.write('\nCOMPLETE; MD5 verified\n')
                break
            if n > size:
                raise ValueError('本地文件超出预期大小，请检查来源')
            end = min(n+2*1024**2,size)-1
            req = urllib.request.Request(url,headers={'Range':f'bytes={n}-{end}'})
            with urllib.request.urlopen(req,timeout=90) as response:
                if response.status != 206:
                    raise IOError('服务器没有接受断点 Range 请求')
                data = response.read()
            if len(data) != end-n+1:
                raise IOError('当前分段不完整，重试')
            with path.open('ab') as out:
                out.write(data)
            failures = 0
            n += len(data)
            log.write(f'\n{time.strftime("%Y-%m-%d %H:%M:%S")} {n}/{size} bytes {100*n/size:.2f}%\n')
        except ValueError:
            raise
        except Exception as exc:
            failures += 1
            log.write(f'\nretry {failures}: {exc}\n')
            if failures >= 100:
                raise
            time.sleep(10)
