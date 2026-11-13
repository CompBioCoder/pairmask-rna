# 第0关：官方源码地图

核对的本地官方仓库提交：`13be9088d5201051abebcf31896cf370ae395c5f`。下面路径都以相邻的 `structRFM/` 为根；行号针对这一提交。笔记只解释实现，不复制官方源码。

## 1．SGMLM / SgMLM：15% 随机种子、PairMatch 和 80/10/10

入口是 `src/structRFM/data/collator.py:14` 的 `PretrainDataCollatorWithStructure`，结构分支函数 `torch_mask_structure` 在同文件第 212–240 行。

- 第 218、227–228 行：每个非特殊 token 独立以 `mlm_probability` 抽样，预训练参数默认 0.15（`src/structRFM/pretrain.py:50–51`）。这是平均 15%，不是每条恰好 15%。
- 第 232–236 行：`connects != 0` 表示有配对伙伴；被抽中的配对碱基会通过 `connects[row,col]` 把另一端加入集合。这就是 PairMatch：先抽种子，再把配对伙伴一起加入，未配对位置保留原抽样结果。
- `src/structRFM/data/RNAdata.py:27–43` 在两端加入连接值 0，对应 [CLS]/[SEP]。原连接值为 1-based，加入起始 token 后恰好可以作为 token 下标使用。
- 第 239 行：扩展后两端都进入预测标签；没有被选中的标签置为 -100，不计算其损失。
- 第 81–92 行 `mask_transform`：选中位置 80% 换 [MASK]，剩下 20% 中再抽一半换随机 token，所以总体为 80/10/10，沿用 BERT 做法。随机 token 从**整个词表**抽取，未限制为 A/U/C/G，也可能碰巧抽回原 token。

不能把“配对双方一起纳入预测集合”理解成“双方一定同时显示 [MASK]”：80/10/10 是后续按位置独立处理的。配对两端至少一端成为随机种子的概率是 `1-(1-0.15)^2=0.2775`，因此结构分支最终选中的配对位置比例可超过 15%。这只是从代码推导的期望值，没有做训练。

## 2．动态比例 r(t)：最重要的组合单位是整个 batch

`src/structRFM/data/collator.py:23–32` 的 `set_ratio`：

- 前 15%：r=0；
- 15% 到 85%：r=0.5×(step−0.15×total_steps)/(0.7×total_steps)；
- 85% 之后：r=0.5。

**实际是每个 batch 二选一，并非每条序列单独抽一次，也不是同一条序列内按位置混合两种策略。** 第 35 行每次 `__call__` 加一次计数；第 59–60 行在处理整个 batch 之前只执行一次随机选择，普通 tokens 的概率是 1−r，structure 的概率是 r，subseq 和 motif 概率都是 0。第 61–76 行把**整个 batch 的二维输入**交给这一次选出的函数。

例如 r=0.5、一个 batch 有 8 条 RNA：抽到普通分支，8 条都只随机抽种子；抽到结构分支，8 条都随机抽种子再补配对伙伴。各条、各位置的种子依然各自随机，但“本批是否补伙伴”是共享的。

还有一个容易漏看的差异：第 23 行默认 `total_steps=1677890`；第 59 行只传 `step_cnt`，没有传训练器实际总步数。`src/structRFM/pretrain.py:103–106` 虽计算本数据每轮 batch 数，却没有接入 `set_ratio`。所以源码的 15%/85% 是相对于这个写死的常数，而不能直接认定是任何新训练任务的前 15%/85%。计数属于 collator 调用次数，不是 Trainer 的全局优化器步数；重复构造、恢复任务和多进程情形也需要另行处理。后续复现应显式定义调度基准，这一关只读代码。

## 3．MUSES：来源顺序、权重和 MEA 的实现边界

`src/structRFM/util/MUSES.py:17–39` 的 `average_matrices` 按传入 weights 对上三角矩阵求加权平均。第 129–142 行读取三种来源：ViennaRNA/RNAfold 的 ps 概率矩阵、CONTRAfold 的 BPPM、BPfold 的 bpseq 硬配对矩阵（0/1）。

按任务给出的论文表述，待核实的顺序是 ViennaRNA RNAfold、CONTRAfold、BPfold，对应 4:1:7；**这组固定值在本地仓库中未找到，需另找正式论文方法段或数据生成配置核实。** 不应说源码默认就是 4:1:7。代码第 279 行默认来源顺序却是 `[BPfold, RNAfold, CONTRAfold]`，若按前述论文权重调用，参数应重排为 `[7,4,1]`。第 287–296 行默认权重先设全 1，随后枚举网格，并未写死论文最优组合。当前可访问的 Nature 页面未开放方法全文，故不能把论文权重映射伪称为已由源码证明。

`mea_decode` 在同文件第 42–99 行：用动态规划比较左端不配、右端不配、两端配对、把区间分成两段，保存最佳选择并回溯。默认至少留 3 个环内碱基，只输出不交叉配对。第 64 行每对得分为 `gamma*P[i,j]`；第 47–48 行注释明确说这只是 MEA-style。未配对状态没有显式加 `q_i=1−Σ_j P_ij` 得分，不能无条件认定其与包含未配对项的标准 MEA 目标或论文公式 2 完全等价。gamma 默认 1；在当前仅给配对正分的目标里，统一改变 gamma 不会改变最优排序（正 gamma 时）。

## 4．零样本同源分类的 overlap ratio（OR）

`tasks/zeroshot/extract_embs/tools.py:34–47`：`cal_or_by_gaussian_kde` 分别对同源正样本和非同源负样本的相似度做 Gaussian KDE；在给定 xlim 中均匀取默认 100 个点，求 `Σ min(f_pos,f_neg) / Σ max(f_pos,f_neg)`。步长相同，所以积分近似的步长抵消。

它比较的是两条**相似度分布**的重合程度，不是碱基配对集合的 Jaccard，也不是只除以某一条密度的面积。越低说明分布分离越好；受 KDE 带宽、xlim 和采样点影响。Rfam 使用位点见同文件第 153–160 行，ArchiveII 位点见第 290–297 行；`tasks/zeroshot/demo_task2_rfam.py:104–142` 汇总多次结果。

## 5．预训练入口与参数

`main.py:1–5` 把命令行参数交给 `structRFM.pretrain.main`。`src/structRFM/pretrain.py:28–53` 定义参数，第 56–74 行按 model_scale 建模型，第 103–126 行计算步数和配置训练器。

| 参数 | 人话含义及实际用法 |
|---|---|
| batch_size | 每张设备每次送入多少条；默认128，第119行交给 per_device_train_batch_size。不是多卡总 batch。 |
| lr | 学习率，默认0.0001；第112行交给训练器。 |
| epoch | 遍历训练集多少轮，默认30；max_steps 用每轮 batch 数乘轮数。 |
| max_length | 总 token 长度上限，默认514，包含两端特殊 token。 |
| model_scale | base=768维/12层/12头，large=1024维/24层/16头；custom才保留用户给出的 dim/layer/heads。定义在 model/structRFM.py:12–17。 |
| tag | mlm 是双向掩码预测；ar 是另一条自回归路线；本项目使用mlm。 |
| mlm_structure | 开启结构 collator，并要求数据有连接信息；关闭时用 transformers 普通 MLM collator。 |
| mlm_probability | 结构分支种子概率，默认0.15；注意关闭结构分支时第101行没有显式传它，普通 collator 沿用库默认0.15。 |
| data_path | 序列数据 CSV 或预处理后的数据目录；包含结构时需 connects 字段。 |
| from_pretrained | 给模型读取已有权重，不等价于恢复训练器状态。 |
| resume_from_checkpoint | 用于恢复训练器及其 checkpoint，需另查是否包含自定义 collator 状态。 |
| use_DDP | 多 NVIDIA GPU 分布式路线；本次 Mac 推理不用。 |

`scripts/run.sh:2–6` 写死了作者的 Linux conda 和项目路径，不能直接在本 Mac 上运行；第 9–18 行有 DDP 就用两进程 torchrun，否则 python3 调 main.py。第0关没有运行训练入口。训练器第130行还写了 fp16=True，也不能把这份训练脚本不加检查就当作 Mac 训练配置。

## 6．tokenizer：T、N 与 514

`src/structRFM/data/tokenizer_mlm.json:1–91` 定义 10 个 token，ID 按顺序是 `[UNK]=0, [CLS]=1, [SEP]=2, [PAD]=3, [MASK]=4, A=5, U=6, C=7, G=8, N=9`。无 BPE merge，碱基逐字编码；N 是独立的正常 token，不等于 [UNK]。其他不在词表中的字符变成 [UNK]。

`src/structRFM/data/RNAdata.py:9–13` 的 `process_mlm_input_seq` 先大写，再把 T 换成 U，最后添加 [CLS]/[SEP]。**T→U 是预处理函数完成的；裸 tokenizer 自己没有这个 normalizer，直接输入 T 会成为 [UNK]。** `src/structRFM/data/tokenizer.py:10–29` 只配置特殊 token 和长度，没有把 T 换成 U。

514 = 512 个真实碱基 + [CLS] + [SEP]；`src/structRFM/model/structRFM.py:49–65` 用 tokenizer 的上限建位置嵌入；`infer.py:124–131` 抽逐碱基特征和注意力时再去掉特殊 token。

## 额外核查：公式7与封装字段不是同一件事

`src/structRFM/infer.py:116–138` 的 `extract_feature`：cls_feat 取最后层第一个 token，seq_feat 取中间真实碱基；第126行 mat_feat 是特征点积；第131行 last_mean_attn_feat 才是最后层平均注意力。notebook 实际比较两次加载的结果并记录误差，不能因为都是 L×L 就混用。

## 来源

[官方仓库](https://github.com/heqin-zhu/structRFM)、[正式论文](https://doi.org/10.1038/s41586-026-11210-2)。以上具体实现结论来自本地源码和固定提交，不把论文描述视为实现证据。
