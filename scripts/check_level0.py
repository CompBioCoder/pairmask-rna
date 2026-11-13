#!/usr/bin/env python
"""第0关检查：真实加载模型，并检查记录、PDF、笔记、下载和 Git。"""
from pathlib import Path
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import contextlib
import io
import importlib
import json
import subprocess
import sys
import warnings
import yaml

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((ROOT / 'config.yaml').read_text())
warnings.filterwarnings('ignore', message='.*return_dict_in_generate.*', category=UserWarning)
counts = {'✅': 0, '❌': 0, '⚠️': 0}

def emit(symbol, text):
    counts[symbol] += 1
    text = str(text).replace(str(ROOT.parent), '<workspace>').replace(str(Path.home()), '<home>')
    print(symbol, text)

def check(condition, text):
    emit('✅' if condition else '❌', text)

modules = {}
for name in ['torch', 'transformers', 'structRFM', 'RNA', 'BPfold']:
    try:
        modules[name] = importlib.import_module(name)
        emit('✅', f'import {name}')
    except Exception as exc:
        emit('❌', f'import {name}: {type(exc).__name__}: {exc}')
if 'torch' in modules:
    available = modules['torch'].backends.mps.is_available()
    emit('✅' if available else '⚠️', f'MPS 可用: {available}（不可用不算失败）')

try:
    from structRFM.infer import structRFM_infer
    modules['transformers'].logging.set_verbosity_error()
    warnings.filterwarnings('ignore', category=FutureWarning)
    with contextlib.redirect_stdout(io.StringIO()):
        model = structRFM_infer(str(ROOT / cfg['checkpoint']), device='cpu', max_length=514,
                               dim=768, layer=12, num_attention_heads=12)
        feats = model.extract_feature('GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA')
    shapes = {k: list(feats[k].shape) for k in ['cls_feat', 'seq_feat', 'mat_feat']}
    check(shapes == {'cls_feat':[768], 'seq_feat':[76,768], 'mat_feat':[76,76]}, f'官方权重实际加载与特征形状: {shapes}')
except Exception as exc:
    emit('❌', f'官方模型: {type(exc).__name__}: {exc}')

try:
    summary = json.loads((ROOT / 'results/level0/summary.json').read_text())
    err = summary['pair_vs_mat_max_abs_error']
    check(isinstance(err, (float, int)), f'自算成对特征对 mat_feat 最大误差已记录: {err:.9g}')
    err2 = summary['pair_vs_last_mean_attention_max_abs_error']
    check(err2 < 1e-5, f'对 last_mean_attn_feat 的最大误差: {err2:.9g}')
    if err > 1e-5:
        emit('⚠️', 'mat_feat 为碱基特征点积；公式7对应 last_mean_attn_feat，差异已解释')
    emit('✅', f'tRNA 最佳阈值={summary["best_threshold"]:.3f}, INF={summary["best_inf"]:.9f}（max对称化，严格大于）')
except Exception as exc:
    emit('❌', f'数值记录: {type(exc).__name__}: {exc}')

for name in ['fpair_mean_last_layer.pdf', 'attn_L11_H5.pdf', 'native_contact_tRNA_Phe.pdf', 'zeroshot_inf_scan_tRNA.pdf']:
    p = ROOT / 'figures/level0' / name
    check(p.exists() and p.read_bytes().startswith(b'%PDF-'), f'PDF: {name}')

p = ROOT / 'notes/00_code_map.md'
text = p.read_text() if p.exists() else ''
for label, keys in [('SGMLM / PairMatch', ['PairMatch','80/10/10']),
                    ('r(t) 与组合单位', ['r(t)','batch','1677890']),
                    ('MUSES / MEA', ['MUSES','4:1:7','mea_decode']),
                    ('同源分类 OR', ['overlap ratio','gaussian_kde']),
                    ('预训练参数', ['batch_size','mlm_structure','run.sh']),
                    ('tokenizer', ['[UNK]','T','N','514'])]:
    check(all(k in text for k in keys), f'源码笔记覆盖: {label}（关键词检查）')
for name in ['00_env.md','00_data_inventory.md','CONVENTIONS.md']:
    check((ROOT/'notes'/name).exists(), f'笔记: {name}')

for name, expected in [('structRFM_checkpoint.tar.gz',319391429),('structRFM_SSP_bpRNA1m.pt',348179698),('structRFM_SSP_RNAStrAlign.pt',348179375)]:
    p = ROOT/'checkpoints'/name
    check(p.exists() and p.stat().st_size == expected, f'完整权重: {name}')
raw = ROOT / cfg['data_raw']
p = raw / 'RNAcentral_512_SS_connects.csv.tar.gz'
n = p.stat().st_size if p.exists() else 0
state = '完成' if n == 4456225221 else ('进行中' if n else '未开始')
emit('✅' if state == '完成' else '⚠️', f'预训练大包: {state}, {n}/4456225221 bytes ({100*n/4456225221:.2f}%)；日志 data/raw/download.log')
s = raw/'tasks_download_status.json'
if s.exists():
    d = json.loads(s.read_text())
    emit('✅' if d['state']=='完成' else '⚠️', f'下游小文件: {d["state"]}, 已保留 {d["selected_files"]} 个文件、{d["selected_bytes"]} bytes；类别 {list(d["categories"])}')
    for category in ['nrc','bprna','archiveii','zeroshot']:
        check(d.get('category_files',{}).get(category,0)>0, f'下游类别 {category}: {d.get("category_files",{}).get(category,0)} 个小文件')
else:
    emit('⚠️','下游数据: 未开始')

def git(*args):
    return subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,text=True)
check(git('rev-parse','--git-dir').returncode == 0, 'Git 仓库已初始化')
r = git('rev-list','--count','HEAD')
check(r.returncode == 0 and int(r.stdout.strip() or 0) >= 1, '至少有一次 Git commit')
r = git('remote','get-url','origin')
emit('✅' if r.returncode==0 else '⚠️', 'Git origin: '+(r.stdout.strip() if r.returncode==0 else '未配置 origin'))
print(f'总结：{counts["✅"]} 项通过，{counts["❌"]} 项失败，{counts["⚠️"]} 项提醒。')
sys.exit(1 if counts['❌'] else 0)
