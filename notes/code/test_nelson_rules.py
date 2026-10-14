"""Each rule is checked against a short hand-made sequence (mean 0, sigma 1)."""

import numpy as np

from nelson_rules import check


def rules_hit(x):
    return {v.rule for v in check(np.array(x, dtype=float), 0.0, 1.0)}


def test_rule1_beyond_3_sigma():
    assert 1 in rules_hit([0.1, -0.2, 3.4, 0.0])


def test_rule2_nine_same_side():
    assert 2 in rules_hit([0.3] * 9)
    assert 2 not in rules_hit([0.3] * 8 + [-0.3])


def test_rule3_six_trending():
    assert 3 in rules_hit([-0.5, -0.3, -0.1, 0.1, 0.3, 0.5])
    assert 3 not in rules_hit([-0.5, -0.3, -0.1, 0.1, 0.3])


def test_rule4_fourteen_alternating():
    assert 4 in rules_hit([0.5 if i % 2 else -0.5 for i in range(14)])
    assert 4 not in rules_hit([0.5 if i % 2 else -0.5 for i in range(13)])


def test_rule5_two_of_three_beyond_2_sigma():
    assert 5 in rules_hit([2.3, 0.1, 2.4])
    assert 5 not in rules_hit([2.3, 0.1, -2.4])


def test_rule6_four_of_five_beyond_1_sigma():
    assert 6 in rules_hit([1.2, 1.3, 0.2, 1.4, 1.1])


def test_rule7_fifteen_within_1_sigma():
    assert 7 in rules_hit([0.2 if i % 3 else -0.2 for i in range(15)])


def test_rule8_eight_beyond_1_sigma_both_sides():
    assert 8 in rules_hit([1.5, -1.5, 1.6, -1.4, 1.3, -1.7, 1.2, -1.3])
    assert 8 not in rules_hit([1.5] * 8)          # one side only is not rule 8


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("pass", name)
