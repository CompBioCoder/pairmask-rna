# structRFM 迷你复现：第0关完整报告

记录日期：2026-11-13（Asia/Shanghai）。第0关 notebook 已从头执行通过，没有训练任何模型。检查结果为 **33项通过、0项失败、3项提醒**。本地仓库完成；GitHub CLI未登录，公开远程未创建、未推送，按任务约定保留本地提交。

## 1．Mac 配置与 MPS

Apple M5，16GiB内存。启动时可用磁盘约443GiB，收尾时约438.28GiB。`torch.backends.mps.is_available()`为True；MPS张量运算及官方模型前向均成功，实际设备mps，没有退回CPU。
外置盘Backup_1t未挂载，本次权重与数据使用Mac本地目录；需要把大文件迁到外置盘时请接上硬盘。

## 2．现有环境与选择原因

共12个现有conda环境，安装前各项版本如下。



— 表示该发行包未安装。jupyter 一列指 jupyter 元包，缺失不一定表示没有 JupyterLab 或 nbconvert。只记录环境名，不记录用户路径。

| 环境 | Python | 架构 | torch | transformers | numpy | scipy | scikit-learn | matplotlib | pandas | jupyter |
|---|---|---|---|---|---|---|---|---|---|---|
| bigmhc | 3.10.22 | arm64 | 2.5.1 | — | 1.26.4 | — | — | — | 2.2.3 | — |
| base | 3.13.13 | arm64 | — | — | 2.5.3 | 1.18.1 | 1.9.1 | 3.11.2 | 3.0.6 | — |
| abeval | 3.11.17 | arm64 | — | — | 2.4.6 | 1.17.1 | — | 3.11.2 | 3.0.6 | — |
| abeval-torch | 3.11.17 | arm64 | 2.14.1 | 4.57.6 | 1.26.4 | 1.17.1 | 1.9.1 | 3.11.2 | 2.1.4 | — |
| fivepseq_env | 3.8.15 | x86_64 | — | — | 1.23.5 | 1.10.1 | — | 3.3.4 | 1.1.5 | — |
| grnade_proteinmpnn | 3.11.16 | arm64 | 2.1.0 | — | 1.26.4 | 1.17.1 | 1.9.1 | 3.11.2 | 3.0.6 | — |
| neoag | 3.10.15 | arm64 | 2.14.1 | — | 2.2.6 | 1.15.2 | 1.7.2 | 3.10.9 | 2.3.3 | 1.1.1 |
| pelechano | 3.11.16 | arm64 | — | — | 2.4.6 | 1.17.1 | 1.9.1 | 3.11.1 | 3.0.5 | — |
| pelechano_x64 | 3.11.16 | x86_64 | — | — | — | — | — | — | — | — |
| py311 | 3.11.15 | arm64 | 2.14.0 | 5.15.0 | 2.4.6 | 1.17.1 | — | 3.11.2 | 3.0.3 | — |
| py38 | 3.8.20 | arm64 | — | — | — | — | — | — | — | — |
| pymol | 3.11.14 | arm64 | — | — | 2.4.6 | — | — | — | — | — |




最终复用优先环境 **grnade_proteinmpnn**，Python3.11.16，没有新建环境。先做pip dry-run，保留torch2.1.0和numpy1.26.4，新增transformers4.45.1（官方参考版本），安装structRFM0.0.9、BPfold0.3.1、ViennaRNA2.8.0、datasets3.1.0和所需Jupyter/绘图工具。最终kernel名为`pairmask`。

pip初次选中的pyarrow26.0.1在真实导入时要求NumPy≥2；再次dry-run后只将pyarrow固定到17.0.0，解决冲突，关键包没有升级或降级。兼容依赖huggingface-hub、fsspec按解析要求调整；详见notes/00_env.md及results/level0/environment_final.json。没有系统级安装，没有改shell配置。

## 3．仓库与提交

本地目录名pairmask-rna，位于GitHub工作目录；未改为maskthepair。已完成git init、MIT许可证、README、目录结构、相对路径config.yaml、代码笔记与结果提交。data与checkpoints链接到相邻structRFM仓库，链接本身及全部大文件均已排除。

`gh auth status`结果：未登录。遵照任务要求，没有代填密码或token；没有配置origin，也没有声称已经建立公开远程。公开API查询CompBioCoder/pairmask-rna时返回404，但最终是否可创建以登录后的GitHub为准。

用户登录后，在本项目根目录执行：

```bash
conda activate grnade_proteinmpnn
gh auth login
gh repo create CompBioCoder/pairmask-rna --public --source=. --remote=origin --push
```

官方structRFM仓库只新增下载文件，并按任务要求补上.gitignore规则；源码未改动、未commit、未push。

## 4．官方模型、注意力与零样本体检

| 项目 | 实测结果 |
|---|---|
| cls_feat | 768 |
| seq_feat | 76×768 |
| mat_feat | 76×76 |
| 平均注意力对mat_feat最大误差 | 120.678871155 |
| 平均注意力对last_mean_attn_feat最大误差 | 2.23517418e-08 |
| 两条加载路径的碱基特征最大误差 | 0.0 |
| NumPy复算点积对mat_feat最大误差 | 0.000106811523 |
| tRNA最佳阈值 | 0.249 |
| tRNA最佳INF | 0.818317088 |
| TP / FP / FN | 15 / 1 / 6 |

差异已经定位：本次官方封装的mat_feat是碱基特征点积；公式7对应last_mean_attn_feat。形状相同不代表同一种特征。没有通过改官方源码消除这个差异。

主评估采用max(A,Aᵀ)合并方向，只数i<j、不数对角线，分数严格大于阈值；阈值0到0.999、步长0.001，不做额外配对合法性或结构解码。另存mean/upper约定的完整扫描，避免混淆。最佳阈值在这条tRNA本身选择，不能视作外部测试性能，也不能直接与论文116条序列结果等同。

四张图均为独立PDF，字号18、Arial、TrueType字体嵌入。均已用Poppler渲染并逐图检查。头5在受体臂、反密码子臂和T臂能看到配对条纹，D臂信号较弱。

## 5．源码六问的答案

1. **SGMLM/PairMatch**：`src/structRFM/data/collator.py:212–240`先用15%概率抽非特殊位置，再把抽中配对位置的伙伴加入标签集合。第81–92行按位置应用80%[MASK]/10%全词表随机token/10%保持原样。因此“伙伴一起进入预测集合”不等于“两端必定都显示[MASK]”，结构分支最终选中率也不再固定15%。
2. **r(t)与组合单位（重点）**：第23–32行实现前15%为0，中间70%线性升到0.5，最后15%保持0.5；但第59–60行每次collator处理**整个batch只抽一次策略**。抽中tokens时，本批每条RNA都用普通随机遮盖；抽中structure时，本批每条RNA都抽种子并补伙伴。不是每条序列单独二选一，也不是一条序列里按位置混合两种分支。举例：一个batch有8条RNA、r=0.5，则一次抽签决定这8条是否都进行PairMatch，碱基种子仍各自随机。另需注意：调度分母写死total_steps=1,677,890，第59行没有把当前训练器总步数传进去；计数是collator调用次数，不能直接等同任意迷你训练的优化器步数。
3. **MUSES**：实现位于`src/structRFM/util/MUSES.py`。上三角矩阵加权平均后，用不交叉区间动态规划回溯，默认环内至少3个碱基。代码的配对得分是γPij，未显式加入未配对概率项，所以是MEA-style，不能直接断言完全等于论文公式2。固定4:1:7在仓库中未找到，需另找正式方法或生成配置核实；按题目列出的待核实顺序，RNAfold/CONTRAfold/BPfold为4/1/7，而源码默认输入顺序BPfold/RNAfold/CONTRAfold应重排成7/4/1。源码默认等权并做权重网格搜索，不能说默认就是论文最优值。
4. **OR**：`tasks/zeroshot/extract_embs/tools.py:34–47`对两组相似度做Gaussian KDE，在给定范围的100个等距点计算Σmin/Σmax；越低表示两组相似度分布越分离。
5. **训练入口**：main.py转到pretrain；batch_size是每设备批量，lr是学习率，max_length含特殊token，base为768维/12层/12头，mlm_structure切换结构collator。run.sh含作者Linux路径，训练配置含fp16，不适合直接在Mac照抄运行。本关没有训练。
6. **tokenizer**：5个特殊token[UNK]/[CLS]/[SEP]/[PAD]/[MASK]，加A/U/C/G/N，共10个。N独占正常token；T在预处理函数中换成U，裸tokenizer不会替换T；514=512个碱基加两端特殊token。

六问的逐条路径、行号及实现边界见notes/00_code_map.md，基于官方提交13be9088d5201051abebcf31896cf370ae395c5f。

## 6．两个Zenodo record的全部文件与下载状态

| Record | 全部文件名 | 大小（字节） | GB |
|---|---|---:|---:|
| 18272040 | RNAcentral_512_MUSES_connects.csv.tar.gz | 5,654,000,185 | 5.654 |
| 16754363 | RNAcentral_512_SS_connects.csv.tar.gz | 4,456,225,221 | 4.456 |
| 16754363 | tasks_data.tar.gz | 3,709,424,795 | 3.709 |
| 16754363 | checkpoints.tar.gz | 2,244,264,123 | 2.244 |


三个官方权重均已下载、按大小和SHA256校验，预训练权重已解压。正式版5.654GB MUSES数据包只列清单，未下载第二份大包。

下游从3.709GB单体gzip流中选择性保留：zeroshot11个、bpRNA12,119个、ArchiveII3,976个、nRC2个，共16,108个文件、143,450,762字节（约143.45MB）。nRC训练6,320条、测试2,600条。没有保存整个下游tar.gz，也没有下载后面的Zfold大特征；累计处理到压缩流243,691,520字节，预取可能多传少量数据。完整已下载文件清单在results/level0/downloaded_task_files.json。

预训练README大包后台断点续传：写本报告时26,814,072/4,456,225,221字节，**0.60%**。日志data/raw/download.log；未等待它完成。已有下载进程运行时不要重复启动脚本。磁盘空间满足20GB门槛，没有跳过。

清单来自[正式版Zenodo API](https://zenodo.org/api/records/18272040)和[README版Zenodo API](https://zenodo.org/api/records/16754363)；权重来自[官方release](https://github.com/heqin-zhu/structRFM/releases/tag/v0.0.8)。

## 7．check_level0.py完整输出

下面是实际执行输出，不是手工勾选；后台下载进度为执行时快照。

```text
✅ import torch
✅ import transformers
✅ import structRFM
✅ import RNA
✅ import BPfold
✅ MPS 可用: True（不可用不算失败）
✅ 官方权重实际加载与特征形状: {'cls_feat': [768], 'seq_feat': [76, 768], 'mat_feat': [76, 76]}
✅ 自算成对特征对 mat_feat 最大误差已记录: 120.678871
✅ 对 last_mean_attn_feat 的最大误差: 2.23517418e-08
⚠️ mat_feat 为碱基特征点积；公式7对应 last_mean_attn_feat，差异已解释
✅ tRNA 最佳阈值=0.249, INF=0.818317088（max对称化，严格大于）
✅ PDF: fpair_mean_last_layer.pdf
✅ PDF: attn_L11_H5.pdf
✅ PDF: native_contact_tRNA_Phe.pdf
✅ PDF: zeroshot_inf_scan_tRNA.pdf
✅ 源码笔记覆盖: SGMLM / PairMatch（关键词检查）
✅ 源码笔记覆盖: r(t) 与组合单位（关键词检查）
✅ 源码笔记覆盖: MUSES / MEA（关键词检查）
✅ 源码笔记覆盖: 同源分类 OR（关键词检查）
✅ 源码笔记覆盖: 预训练参数（关键词检查）
✅ 源码笔记覆盖: tokenizer（关键词检查）
✅ 笔记: 00_env.md
✅ 笔记: 00_data_inventory.md
✅ 笔记: CONVENTIONS.md
✅ 完整权重: structRFM_checkpoint.tar.gz
✅ 完整权重: structRFM_SSP_bpRNA1m.pt
✅ 完整权重: structRFM_SSP_RNAStrAlign.pt
⚠️ 预训练大包: 进行中, 24716920/4456225221 bytes (0.55%)；日志 data/raw/download.log
✅ 下游小文件: 完成, 已保留 16108 个文件、143450762 bytes；类别 ['zeroshot', 'bprna', 'archiveii', 'nrc']
✅ 下游类别 nrc: 2 个小文件
✅ 下游类别 bprna: 12119 个小文件
✅ 下游类别 archiveii: 3976 个小文件
✅ 下游类别 zeroshot: 11 个小文件
✅ Git 仓库已初始化
✅ 至少有一次 Git commit
⚠️ Git origin: 未配置；gh 未登录，按要求只建本地仓库
总结：33 项通过，0 项失败，3 项提醒。
```

## 8．问题及处理

- 外置盘未挂载：使用本地目录和相对链接，提示后续接盘迁移。
- gh不存在，Homebrew下载又遇DNS失败：改用GitHub CLI官方arm64发布包，安装到项目所用conda环境bin；查询后确认未登录，停止于本地提交。
- curl不能解析GitHub/Zenodo域名，而Python网络可以访问：改用Python HTTP Range、失败重试与分段校验；权重全部完成，预训练大包继续后台续传。
- pip dry-run未发现pyarrow/NumPy运行时冲突：将pyarrow固定为17.0.0，保留torch/numpy，随后真实导入、MPS运算和整本notebook执行均通过。
- 官方mat_feat与题目对公式7的字段称呼不同：保留原始定义，独立计算并验证真正对应的last_mean_attn_feat，记录两个误差。
- 下游仅提供单体gzip：并行预取压缩分段、顺序解包、只保留目标小文件，及时停止大任务数据；初始长连接中断后改为可重试的Range读取。
- 普通生成配置警告会打印本机库路径：仅屏蔽与本次特征推理无关的生成配置提示，重跑notebook；公开文本和notebook输出已扫描，无用户名绝对路径。所有代码格上方均有中文说明。
- MUSES固定权重与完整论文目标无法仅从本仓库证明：在笔记明确区分源码证据和待核实的论文表述，没有编造“已经找到”的结论。

复现主体：notebooks/level0_setup_and_official_model.ipynb。数据与权重不纳入公开仓库或交付压缩包；本机已有链接可直接从头重跑。
