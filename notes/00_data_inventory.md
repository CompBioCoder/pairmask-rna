# 第0关：数据和权重清单

查询日期：2026-11-13（Asia/Shanghai）。下列是两个 Zenodo record API 返回的**全部文件**；GB 为十进制，GiB 为二进制。原始文件名、字节数、校验码和下载链接另存 results/level0/zenodo_*_inventory.json。

## 18272040：论文正式版：MUSES 结构标注

[record](https://zenodo.org/records/18272040)；[API](https://zenodo.org/api/records/18272040)。

| 文件 | 字节 | GB | GiB | 校验码 |
|---|---:|---:|---:|---|
| RNAcentral_512_MUSES_connects.csv.tar.gz | 5,654,000,185 | 5.654 | 5.266 | md5:651db6dc7b6d6aadece06a252831d1fe |
## 16754363：README 版：原有预训练数据和任务资源

[record](https://zenodo.org/records/16754363)；[API](https://zenodo.org/api/records/16754363)。

| 文件 | 字节 | GB | GiB | 校验码 |
|---|---:|---:|---:|---|
| RNAcentral_512_SS_connects.csv.tar.gz | 4,456,225,221 | 4.456 | 4.150 | md5:24c6c7789fe366299ae00640f5f1a744 |
| tasks_data.tar.gz | 3,709,424,795 | 3.709 | 3.455 | md5:d13d0bfb56867b1ce597ce2fb896304b |
| checkpoints.tar.gz | 2,244,264,123 | 2.244 | 2.090 | md5:e572a7781a8099ff45692fcd46f83043 |


## 下载策略与版本差别

- 正式版 MUSES 预训练包实际5.654 GB；README版 SS 包4.456 GB。不是同一个文件，不应混作同一套标注。
- 本关遵照“4.5GB包放后台”的要求下载 README 版，正式版只列清单，没有再下载第二份大包。本关 tRNA 推理不依赖任何预训练语料。
- 下游只提供 tasks_data.tar.gz 一个3.709 GB单体 gzip包，API没有可单独下载的 nRC、bpRNA、ArchiveII、zeroshot条目。gzip不能直接按内部文件名跳转。
- 为少占本地磁盘，使用 HTTP Range 并行预取，再按压缩流顺序解包；仅保留名字中包含所需类别的小文件，不保存整个下游压缩包。读取到后面的成员仍需要传输它前面的压缩数据，不能把节省磁盘说成等量节省网络流量。
- 单个成员上限64MiB，每类累计上限512MiB；超过限制的成员留在 skipped_large 清单。这一策略下载的是可用小子集，不承诺整个 bpRNA1m 训练集齐全。
- 避免路径穿越：拒绝绝对路径与含 .. 的成员，不解包软链接。下载状态及成员清单在 data/raw/tasks_download_status.json、data/raw/tasks_archive_inventory.csv。
- 预训练大包逐段续传，日志 data/raw/download.log。重启续传可运行 `python scripts/download_pretrain.py`；已有下载进程运行时不要重复启动。
- 启动时磁盘可用空间大于20GB，故没有跳过大包。外置盘未挂载，当前数据和权重均在本地。

## 官方权重

GitHub release v0.0.8 的三个目标文件如下。分段下载完毕会验证文件总大小及 release 提供的 SHA256（若有），预训练 tar.gz 再做完整解包检查。具体哈希见 data/raw/weights_download_status.json。

| 文件 | 字节 |
|---|---:|
| structRFM_checkpoint.tar.gz | 319,391,429 |
| structRFM_SSP_bpRNA1m.pt | 348,179,698 |
| structRFM_SSP_RNAStrAlign.pt | 348,179,375 |

官方预训练权重已可解压为 checkpoints/structRFM_checkpoint/，包含 config.json、tokenizer.json 和 model.safetensors。

## 参考资料

Nature 的公开页面已保存到 data/raw/references/nature_public_page.html。论文正文 PDF 地址返回的是 HTML 访问页面，未将它伪存为PDF。公开补充材料 supplementary_information.pdf 已下载；补充方法说明正文方法才包含语料、结构遮盖等主要定义。未绕过访问控制。

## 当前下载状态快照

下游流式筛选：完成；已保留16108个文件、143,450,762字节；已处理压缩流243,691,520字节。类别字节数：`{'zeroshot': 121666429, 'bprna': 12621913, 'archiveii': 7313620, 'nrc': 1848800}`。

预训练大包：22,619,768/4,456,225,221字节，0.51%；后台运行，未等待其完成。状态是写入时快照，实时进度以日志和文件大小为准。


本次已结束下游小文件筛选，没有扫描完整3.709GB包。已确认：zeroshot 11个文件、bpRNA 12,119个文件、ArchiveII 3,976个文件、nRC 2个文件，共16,108个文件、143,450,762字节。nRC的train.fa为6,320条，test.fa为2,600条。压缩流处理到243,691,520字节后停止；并行预取会多读少量后续分段，不能以这个值充当精确网络流量。完整的**已下载成员清单**在 results/level0/downloaded_task_files.json。bpRNA 数量含不同拆分/路径，不按此数字声称独立序列总数。
