"""make e2e: deepeval golden prompts against the deployed POST /chat (requirements §8).

- Contract invariants: must pass on every prompt.
- Golden expectations: at least 80% must pass (8 of 10 in the spec; 7 of 8 for MVP 1).
- LLM-judged quality (GEval on Bedrock): why specificity for recommendations, safe steering otherwise.
"""

import math

import pytest
from conftest import GOLDEN, render
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from metrics import ContractInvariants, GoldenExpectation, safe_steer, why_specificity

IDS = [f'golden-{p["n"]}' for p in GOLDEN]
EXPECTATIONS: dict[int, tuple[bool, str]] = {}


def case(run: dict) -> LLMTestCase:
    return LLMTestCase(
        name=f'golden-{run["n"]}',
        input=' → '.join(run['turns']),
        actual_output=render(run['bodies'][-1]),
        metadata={'expect': run['expect'], 'bodies': run['bodies']},
    )


@pytest.mark.parametrize('n', [p['n'] for p in GOLDEN], ids=IDS)
def test_invariants(runs, n):
    assert_test(case(runs[n]), [ContractInvariants()], run_async=False)


@pytest.mark.parametrize('n', [p['n'] for p in GOLDEN], ids=IDS)
def test_expectation(runs, n):
    metric = GoldenExpectation()
    metric.measure(case(runs[n]))
    EXPECTATIONS[n] = (metric.success, metric.reason)
    if not metric.success:
        pytest.xfail(f'expectation missed (counts toward the 80% bar): {metric.reason}')


def test_expectation_pass_bar(runs):
    for n in runs:
        if n not in EXPECTATIONS:
            metric = GoldenExpectation()
            metric.measure(case(runs[n]))
            EXPECTATIONS[n] = (metric.success, metric.reason)
    passed = sum(ok for ok, _ in EXPECTATIONS.values())
    need = math.ceil(0.8 * len(EXPECTATIONS))
    print('\n#  pass  secs  detail / message')
    for n, (ok, reason) in sorted(EXPECTATIONS.items()):
        r = runs[n]
        print(f'{n:<2} {"✓" if ok else "✗":<5} {r["secs"]:<5} {reason}\n            “{r["bodies"][-1]["message"][:100]}”')
    print(f'\nexpectations: {passed}/{len(EXPECTATIONS)} (need {need})')
    assert passed >= need


@pytest.mark.parametrize('n', [p['n'] for p in GOLDEN], ids=IDS)
def test_quality(runs, judge_model, n):
    run = runs[n]
    if run['kind'] == 'recommend':
        if not run['bodies'][-1]['matches']:
            pytest.skip('no matches to judge')
        metric = why_specificity(judge_model)
    else:
        metric = safe_steer(judge_model)
    assert_test(case(run), [metric], run_async=False)
