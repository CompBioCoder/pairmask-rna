"""按无向碱基对计算 INF，不重复计算镜像位置。"""
import numpy as np


def contact_metrics(scores, native, threshold=0.5, symmetrize="max"):
    """先合并两个方向，再仅统计 i<j；阈值采用严格大于。

    默认 max：任一方向超过阈值即报告该配对。可选 mean/upper，便于比较。
    不额外施加配对类型、最短环、一碱基一伙伴或非交叉限制。
    空预测或空真值的 precision/recall/INF 定义为 0。
    """
    scores = np.asarray(scores, dtype=float)
    native = np.asarray(native, dtype=bool)
    if scores.ndim != 2 or scores.shape[0] != scores.shape[1] or scores.shape != native.shape:
        raise ValueError("预测和真值必须是相同大小的方阵")
    if not np.isfinite(scores).all():
        raise ValueError("预测含非有限值")
    if symmetrize == "max":
        scores = np.maximum(scores, scores.T)
    elif symmetrize == "mean":
        scores = (scores + scores.T) / 2
    elif symmetrize != "upper":
        raise ValueError("symmetrize 必须是 max、mean 或 upper")
    ix = np.triu_indices(len(scores), k=1)
    pred = scores[ix] > threshold
    truth = (native | native.T)[ix]
    tp = int(np.sum(pred & truth))
    fp = int(np.sum(pred & ~truth))
    fn = int(np.sum(~pred & truth))
    ppv = tp / (tp + fp) if tp + fp else 0.0
    sty = tp / (tp + fn) if tp + fn else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "PPV": ppv, "STY": sty,
            "INF": float(np.sqrt(ppv * sty))}
