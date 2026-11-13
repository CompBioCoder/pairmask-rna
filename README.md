# pairmask-rna

公开仓库：[CompBioCoder/pairmask-rna](https://github.com/CompBioCoder/pairmask-rna)。代码、notebook、笔记和结果图表在此公开；原始数据与模型权重保留本地，不进入Git版本控制。

一周在 Mac 上迷你复现 structRFM 的结构引导遮盖机制。面向生物背景读者，采用中文 Jupyter notebook，一格一格展示中间结果。

当前硬件：Apple M5，16 GiB 内存；第0关只做 76 nt tRNA 推理。后续使用小模型、小数据学习机制，不承诺复现论文 21M 序列的训练规模或原始性能。

| 关卡 | 内容 | 状态 |
|---|---|---|
| 0 | 看清终点：环境、官方模型、注意力与评估 | 已实现 |
| 1 | 整理小规模序列和配对数据 | 规划 |
| 2 | 实现普通遮盖与配对遮盖 | 规划 |
| 3 | 小模型与最小预训练 | 规划 |
| 4 | 公平比较与消融 | 规划 |
| 5 | 汇总结果与局限 | 规划 |

后五关为学习路线草案，随任务调整。

## 从第0关开始

使用已配置环境中的 `pairmask` Jupyter kernel，打开 `notebooks/level0_setup_and_official_model.ipynb`。
`config.yaml` 使用相对路径。`data/` 和 `checkpoints/` 指向相邻的官方仓库，均不进入版本控制。

```bash
conda activate grnade_proteinmpnn
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=pairmask notebooks/level0_setup_and_official_model.ipynb
python scripts/check_level0.py
```

查看 `notes/00_env.md` 的版本信息、`notes/00_code_map.md` 的源码解读及 `notes/00_data_inventory.md` 的资源清单。
`results/level0/` 保存扫描表与数值记录；`figures/level0/` 保存四张独立 PDF。

## 引用

Zhu et al. *An open structure-guided RNA foundation model for generalizable prediction*. Nature (2026). [论文](https://doi.org/10.1038/s41586-026-11210-2)；[官方仓库](https://github.com/heqin-zhu/structRFM)。

本项目是独立学习笔记，官方模型与数据的权利和使用条款以各自来源为准。本项目原创代码和笔记采用 MIT License，见 LICENSE。
