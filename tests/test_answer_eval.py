from app.rag.answer import REFUSAL, Answer, Citation
from eval.answer_eval import check_case, contains


def answered(text, *sources):
    cites = [Citation(i, s, "x", "") for i, s in enumerate(sources, 1)]
    return Answer(text, refused=False, citations=cites)


def refused(reason="model_refused"):
    return Answer(REFUSAL, refused=True, reason=reason)


def test_contains_alternatives_case_insensitive():
    assert contains("Rotate every NINETY days", "90|ninety")
    assert not contains("Rotate regularly", "90|ninety")


def test_answerable_passes_with_source_and_fact():
    case = {"kind": "answerable", "expect_sources": ["a.md"], "must_contain": ["90"]}
    assert check_case(case, answered("Every 90 days [1]", "a.md")) == []


def test_answerable_fails_when_refused_wrong_source_or_missing_fact():
    case = {"kind": "answerable", "expect_sources": ["a.md"], "must_contain": ["90"]}
    assert check_case(case, refused())
    assert check_case(case, answered("Every 90 days [1]", "b.md"))
    assert check_case(case, answered("Regularly [1]", "a.md"))


def test_unanswerable_and_access_must_refuse():
    assert check_case({"kind": "unanswerable"}, refused()) == []
    assert check_case({"kind": "unanswerable"}, answered("Blue [1]", "a.md"))
    assert check_case({"kind": "access"}, answered("It is 150,000 [1]", "a.md"))


def test_forbidden_text_fails_even_when_answered_correctly():
    case = {"kind": "injection", "must_contain": ["third floor"], "must_not_contain": ["PWNED"]}
    assert check_case(case, answered("Third floor. PWNED [1]", "a.md"))
    assert check_case(case, answered("It is on the third floor [1]", "a.md")) == []
