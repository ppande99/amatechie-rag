import pytest

from eval.metrics import mean, recall_at_k, reciprocal_rank


def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, k=2) == 0.5
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, k=3) == 1.0


def test_recall_requires_relevant():
    with pytest.raises(ValueError):
        recall_at_k(["a"], set(), k=1)


def test_reciprocal_rank():
    assert reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(["x"], {"a"}) == 0.0


def test_mean():
    assert mean([]) == 0.0
    assert mean([1.0, 0.0]) == 0.5
