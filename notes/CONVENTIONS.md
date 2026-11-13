# 项目约定

面向生物背景读者，用中文解释代码在做什么、为什么做；每个 notebook 代码格正上方必须有中文 markdown。
每关以可从头执行的 notebook 为主体，关键步骤及中间结果直接展示；允许复用模块，但不把 notebook 写成脚本调用空壳。
每图一个文件，只存 PDF，不用 subplot。统一设置：

```python
plt.rcParams.update({'font.size': 18, 'font.family': 'Arial', 'pdf.fonttype': 42, 'ps.fonttype': 42})
```

优先复用已有 conda 环境，先做 pip dry-run，保护已有 torch/numpy/transformers。工具优先 brew/pip，不动系统 Python，不改 shell 配置。
权重和数据在被忽略的链接目录，路径使用相对路径和 config.yaml。官方仓库源码只读，不在其中 commit/push；只允许加入下载文件和任务明确要求的忽略规则。
公开文件不包含个人信息、用户名路径、求职或申请内容。提交作者用公开 GitHub 账号。
可自行解决的问题自行处理，并记录原因与解决办法；真正无法继续时再询问。第0关不训练模型。
