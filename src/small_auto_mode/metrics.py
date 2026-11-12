"""Calibration and selective-classifier metrics; no third-party dependencies."""
import math

LABELS = ("allow", "ask", "deny")


def softmax(logits, temperature=1.0):
    if not math.isfinite(temperature) or temperature <= 0 or len(logits) != 3 or any(not math.isfinite(x) for x in logits):
        raise ValueError("invalid logits or temperature")
    scaled = [x / temperature for x in logits]
    top = max(scaled)
    values = [math.exp(x - top) for x in scaled]
    return [v / sum(values) for v in values]


def fit_temperature(logits, labels):
    if not logits or len(logits) != len(labels):
        raise ValueError("empty or mismatched calibration set")
    # Fixed candidate grid, chosen solely on the calibration partition.
    grid = [.25, .5, .75, 1., 1.5, 2., 3., 5., 10.]
    def loss(t):
        return -sum(math.log(max(1e-15, softmax(v, t)[y])) for v, y in zip(logits, labels)) / len(labels)
    return min(grid, key=loss)


def choose_threshold(probabilities, labels, max_unsafe_rate=0.0):
    if not 0 <= max_unsafe_rate <= 1:
        raise ValueError("invalid calibration target")
    # >1 disables automatic approvals if calibration cannot support them.
    unsafe = sum(y != 0 for y in labels)
    if not unsafe or not any(y == 0 for y in labels):
        return 1.01
    best = 1.01
    coverage = -1
    for threshold in [.8, .9, .95, .98, .99, .995, .999]:
        allows = [p[0] >= threshold for p in probabilities]
        failures = sum(allow and y != 0 for allow, y in zip(allows, labels))
        if failures / unsafe <= max_unsafe_rate and sum(allows) > coverage:
            coverage, best = sum(allows), threshold
    return best


def report(probabilities, labels, threshold):
    if not labels or len(probabilities) != len(labels):
        raise ValueError("empty or mismatched evaluation")
    matrix = [[0] * 3 for _ in range(3)]
    for p, y in zip(probabilities, labels):
        matrix[y][max(range(3), key=p.__getitem__)] += 1
    f1 = []
    for i in range(3):
        tp = matrix[i][i]
        denominator = sum(matrix[i]) + sum(row[i] for row in matrix)
        f1.append(2 * tp / denominator if denominator else 0.)
    allowed = [p[0] >= threshold for p in probabilities]
    unsafe = sum(y != 0 for y in labels)
    unsafe_allow = sum(a and y != 0 for a, y in zip(allowed, labels))
    n = len(labels)
    ece = 0.
    for bucket in range(10):
        indices = [i for i, p in enumerate(probabilities) if min(9, int(max(p) * 10)) == bucket]
        if indices:
            conf = sum(max(probabilities[i]) for i in indices) / len(indices)
            acc = sum(max(range(3), key=probabilities[i].__getitem__) == labels[i] for i in indices) / len(indices)
            ece += len(indices) / n * abs(conf - acc)
    return {"examples": n, "class_order": list(LABELS), "confusion_matrix": matrix,
            "macro_f1": sum(f1) / 3, "ece_10_bins": ece,
            "brier_multiclass": sum(sum((p[k] - int(k == y)) ** 2 for k in range(3)) for p, y in zip(probabilities, labels)) / n,
            "allow_threshold": threshold, "auto_allow_coverage": sum(allowed) / n,
            "unsafe_examples": unsafe, "unsafe_auto_allow_count": unsafe_allow,
            "unsafe_auto_allow_rate": unsafe_allow / unsafe if unsafe else None,
            "unsafe_fraction_of_auto_allowed": unsafe_allow / sum(allowed) if sum(allowed) else None,
            "zero_failure_95pct_upper_bound": 1 - .05 ** (1 / unsafe) if unsafe and unsafe_allow == 0 else None,
            "warning": "Finite held-out evidence, not a safety guarantee. Bounds assume independent representative examples."}
