"""Tests for core.i18n."""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from core.i18n import (
    DEFAULT_LOCALE,
    FALLBACK_LOCALE,
    MESSAGES,
    available_locales,
    list_keys,
    t,
)


class TestTranslate:
    def test_translates_known_key_default_locale(self) -> None:
        assert t(DEFAULT_LOCALE, "index.panorama.heading") == "## Panorama"

    def test_translates_known_key_en(self) -> None:
        assert t("en", "index.panorama.heading") == "## Overview"

    def test_substitutes_placeholders(self) -> None:
        out = t("en", "index.title", project="Acme")
        assert out == "Index — Acme"

    def test_substitutes_placeholders_ptbr(self) -> None:
        out = t(DEFAULT_LOCALE, "index.title", project="Acme")
        assert out == "Índice — Acme"

    def test_missing_kwargs_returns_literal(self) -> None:
        """If placeholders aren't filled, return the template unchanged."""
        out = t("en", "index.title")
        assert "{project}" in out

    def test_unknown_locale_falls_back_to_en(self) -> None:
        assert t("klingon", "index.panorama.heading") == "## Overview"

    def test_unknown_key_returns_key_literal(self) -> None:
        assert t("en", "nonexistent.key") == "nonexistent.key"

    def test_unknown_key_in_any_locale_returns_key(self) -> None:
        assert t(DEFAULT_LOCALE, "bogus.path") == "bogus.path"


class TestLocaleCoverage:
    def test_all_keys_translated_in_primary_locale(self) -> None:
        """Primary locale (pt-br) must have every key present in en."""
        en_keys = set(MESSAGES["en"].keys())
        pt_keys = set(MESSAGES["pt-br"].keys())
        missing = en_keys - pt_keys
        assert not missing, f"Missing pt-br translations: {sorted(missing)}"

    def test_all_keys_translated_in_en(self) -> None:
        """Fallback locale must have every key present in pt-br."""
        pt_keys = set(MESSAGES["pt-br"].keys())
        en_keys = set(MESSAGES["en"].keys())
        missing = pt_keys - en_keys
        assert not missing, f"Missing en translations: {sorted(missing)}"


class TestHelpers:
    def test_available_locales_has_primary_and_fallback(self) -> None:
        locales = available_locales()
        assert DEFAULT_LOCALE in locales
        assert FALLBACK_LOCALE in locales

    def test_list_keys_returns_sorted(self) -> None:
        keys = list_keys("en")
        assert keys == sorted(keys)
        assert len(keys) > 0


class TestTranslationPBT:
    @given(st.sampled_from(list(MESSAGES["en"].keys())))
    def test_every_en_key_resolves_nonempty(self, key: str) -> None:
        assert t("en", key) is not None
        assert t("en", key) != ""

    @given(st.sampled_from(list(MESSAGES["pt-br"].keys())))
    def test_every_ptbr_key_resolves_nonempty(self, key: str) -> None:
        assert t("pt-br", key) is not None
        assert t("pt-br", key) != ""

    @given(st.text(min_size=1, max_size=50))
    def test_unknown_key_always_returns_input(self, key: str) -> None:
        # Skip keys that happen to exist in the real dict.
        if key in MESSAGES["en"] or key in MESSAGES["pt-br"]:
            return
        assert t("en", key) == key
        assert t("pt-br", key) == key
