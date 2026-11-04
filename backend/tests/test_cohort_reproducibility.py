"""Issue #751: cohort construction reproducibility knobs.

MIROFISH_COHORT_TEMPERATURE overrides the LLM temperatures used in ontology,
profile and simulation-config generation. MIROFISH_COHORT_SEED makes the
profile generator's random numbers (karma, follower counts, username suffixes)
reproducible. Both default to the previous behavior when unset.
"""

import random

from app.config import Config
from app.services.oasis_profile_generator import OasisProfileGenerator


class TestCohortTemperature:
    def test_default_behavior_when_unset(self, monkeypatch):
        monkeypatch.setattr(Config, "COHORT_TEMPERATURE", None)
        assert Config.cohort_temperature(0.3) == 0.3
        assert Config.cohort_temperature(0.7) == 0.7

    def test_override_when_set(self, monkeypatch):
        monkeypatch.setattr(Config, "COHORT_TEMPERATURE", 0.0)
        assert Config.cohort_temperature(0.3) == 0.0
        assert Config.cohort_temperature(0.7 - 1 * 0.1) == 0.0

    def test_nonzero_override(self, monkeypatch):
        monkeypatch.setattr(Config, "COHORT_TEMPERATURE", 0.2)
        assert Config.cohort_temperature(0.7) == 0.2


class TestCohortSeed:
    @staticmethod
    def _generator_with_rng(seed):
        gen = OasisProfileGenerator.__new__(OasisProfileGenerator)
        gen._rng = random.Random(seed)
        return gen

    def test_same_seed_gives_identical_usernames(self):
        gen1 = self._generator_with_rng(42)
        gen2 = self._generator_with_rng(42)
        names = ["Alice Smith", "Bob-Lee", "王小明"]
        assert [gen1._generate_username(n) for n in names] == [
            gen2._generate_username(n) for n in names
        ]

    def test_different_seeds_diverge(self):
        gen1 = self._generator_with_rng(1)
        gen2 = self._generator_with_rng(2)
        results1 = [gen1._generate_username("alice") for _ in range(5)]
        results2 = [gen2._generate_username("alice") for _ in range(5)]
        assert results1 != results2

    def test_rule_based_profile_is_reproducible_with_seed(self):
        gen1 = self._generator_with_rng(7)
        gen2 = self._generator_with_rng(7)
        p1 = gen1._generate_profile_rule_based(
            entity_name="Alice", entity_type="Student",
            entity_summary="", entity_attributes={},
        )
        p2 = gen2._generate_profile_rule_based(
            entity_name="Alice", entity_type="Student",
            entity_summary="", entity_attributes={},
        )
        assert p1 == p2
