# 第0关：环境与 Mac 配置

记录日期：2026-11-13（Asia/Shanghai）。只读查询得到 Apple M5，16 GiB 内存，启动时可用磁盘约443 GiB（约476 GB）。外置盘 Backup_1t 未挂载，本次使用本地目录；如需将大文件放到外置盘，请先接硬盘，再迁移目录并调整链接。

## 全部现有 conda 环境（安装前）

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


其他依赖的安装前版本见 `results/level0/conda_environments.json`。

## 环境选择与 dry-run

最终复用 `grnade_proteinmpnn`（Python 3.11.16，arm64），没有新建 conda 环境。
先对全部目标包做不限定版本的 pip dry-run，再按官方版本参考选择 transformers 4.45.1、datasets 3.1.0 重做 dry-run。
兼容方案未升级或降级 torch 2.1.0、numpy 1.26.4，transformers 原来没有安装；保留了原有这两个关键包。
参考 YAML 只用于选版本，没有直接据此创建环境。较新的 transformers 5.x 与旧 torch 的运行时要求不同，故不盲用最新版。
依赖解析同时会将 huggingface-hub 从1.32.0调整为0.36.2、fsspec从2026.9.0调整为2024.9.0；这些是选定 transformers/datasets 的兼容依赖，已保留安装前后记录。Jupyter 相关包按依赖解析补齐。

安装在该环境内部，不使用系统 Python，不更改 shell 配置。GitHub CLI 的 Homebrew 下载因命令行 DNS 问题失败，改用官方 macOS arm64 发布包，将可执行文件放入同一 conda 环境的 bin。

```bash
conda activate grnade_proteinmpnn
python -m ipykernel install --user --name pairmask --display-name "Python (pairmask)"
```

`pairmask` 是 kernel 名，所用 conda 环境仍叫 grnade_proteinmpnn。
权重、数据和输出路径见项目 `config.yaml`，全部为相对路径；data 和 checkpoints 是指向相邻官方仓库的链接。

## MPS

实际查询 `torch.backends.mps.is_available()` 为 True。notebook 还做 MPS 张量乘法和真实模型前向验证；实际设备及是否回退见 `results/level0/summary.json`。

## GitHub 状态

官方仓库不 commit/push。自己的仓库已本地 git init，提交作者采用公开 GitHub handle 及 noreply 地址。
用户已在浏览器手动授权 GitHub CLI，确认账号为 CompBioCoder。命令行显式使用现有系统代理后连接成功；公开远程 [CompBioCoder/pairmask-rna](https://github.com/CompBioCoder/pairmask-rna) 已创建并完成 main 首次推送，未改名。数据和权重继续本地存储，不纳入 Git；不记录密码或 token。


## 实际导入时发现的兼容问题

pip dry-run 未改动 torch/numpy，但它选中的 pyarrow 26.0.1 实际要求 NumPy≥2。包元数据未阻止该组合，所以直到导入 datasets 才出现错误。对 `pyarrow==17.0.0` 再次 dry-run，只需调整 pyarrow、不改变 torch/numpy/transformers，随后固定这一版本解决。
安装后的最终版本见 requirements.txt 和 results/level0/environment_final.json。保留已有关键包，未通过升级 NumPy 来绕开问题。
