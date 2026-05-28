from fun_comment_locales import (
    derive_italian_from_spanish,
    derive_spanish_from_portuguese,
    locales_for_comment_bundle,
)


def test_native_es_it_used_when_present():
    bundle = {
        "en": "Mexico opens at home",
        "pt": "O México abre em casa",
        "es": "México abre en casa",
        "it": "Il Messico apre in casa",
    }
    it, es = locales_for_comment_bundle(bundle)
    assert es == "México abre en casa"
    assert it == "Il Messico apre in casa"


def test_italian_commentary_fallback_when_no_native_keys():
    bundle = {
        "en": "Mexico opens at home against South Africa — the vuvuzelas against the Mexican wave!",
        "pt": "O México abre em casa contra a África do Sul — as vuvuzelas contra a ola mexicana!",
        "nl": "x",
        "de": "x",
    }
    it, es = locales_for_comment_bundle(bundle)
    assert it != bundle["en"]
    assert es != bundle["pt"]
    assert "México" in es or "Mexico" in es
    assert "Messico" in it or "calcio" in it or "casa" in it


def test_italian_from_spanish_changes_romance_words():
    es = "Partido eliminatorio en el estadio — los equipos juegan fútbol."
    it = derive_italian_from_spanish(es)
    assert "Partita" in it
    assert "stadio" in it
    assert "squadre" in it or "calcio" in it
