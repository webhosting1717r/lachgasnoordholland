#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle van de plaatsmodules (AREAS) voor lachgasnoordholland.nl.
Gebruik: python3 _build/check_content.py [_build/content/areas_*.py ...]   (zonder argumenten: alle areas_*.py)
Controleert schema, lengtes, interne links, slugs, coördinaten en de uniforme levertijd. Exitcode 1 bij fouten."""
import glob, importlib.util, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

HUBS = {
    "amsterdam": ["amsterdam", "amsterdam-centrum", "amsterdam-west", "amsterdam-nieuw-west", "amsterdam-zuid", "amsterdam-oost", "amsterdam-noord", "amsterdam-zuidoost", "weesp"],
    "amstelland-en-meerlanden": ["amstelveen", "hoofddorp", "nieuw-vennep", "badhoevedorp", "diemen", "uithoorn", "aalsmeer", "ouderkerk-aan-de-amstel"],
    "kennemerland": ["haarlem", "heemstede", "bloemendaal", "zandvoort", "ijmuiden", "velserbroek", "beverwijk", "heemskerk"],
    "zaanstreek-waterland": ["zaandam", "krommenie", "wormerveer", "assendelft", "purmerend", "volendam", "edam", "monnickendam", "landsmeer"],
    "regio-alkmaar": ["alkmaar", "heerhugowaard", "langedijk", "bergen", "schoorl", "egmond-aan-zee", "heiloo", "castricum", "uitgeest"],
    "west-friesland": ["hoorn", "enkhuizen", "medemblik", "bovenkarspel", "grootebroek", "hoogkarspel", "wognum", "obdam", "opmeer"],
    "kop-van-noord-holland": ["den-helder", "julianadorp", "schagen", "callantsoog", "anna-paulowna", "wieringerwerf", "hippolytushoef", "texel"],
    "gooi-en-vechtstreek": ["hilversum", "bussum", "naarden", "muiden", "huizen", "laren", "blaricum", "loosdrecht", "kortenhoef"],
}
PLACES = {s: h for h, ss in HUBS.items() for s in ss}
ARTICLES = ["wat-is-lachgas", "is-lachgas-legaal-in-nederland", "lachgas-regels-per-gemeente-noord-holland", "lachgas-en-vitamine-b12", "lachgas-bijwerkingen-en-eerste-hulp",
            "lachgas-en-alcohol", "lachgas-in-het-verkeer", "lachgastank-bewaren-en-vervoeren", "lege-lachgastank-inleveren-noord-holland", "lachgas-bij-kou-en-warmte",
            "tank-versus-patronen", "lachgas-en-het-milieu", "problematisch-lachgasgebruik-hulp", "geschiedenis-van-lachgas", "eerste-keer-lachgas-bestellen",
            "lachgas-mythes-en-feiten", "lachgas-voor-ouders", "de-dag-na-lachgas", "lachgas-en-mentale-gezondheid", "lachgas-op-festivals-en-evenementen",
            "betrouwbare-lachgas-bezorgservice-herkennen", "begrippenlijst-lachgas", "feest-thuis-zonder-overlast", "veiligheid-en-gezondheid", "regels-en-wetgeving"]
SERVICES = ["spoedbezorging", "nachtbezorging", "weekendbezorging", "feestdagen-en-evenementen", "betalen-bij-levering", "leeftijdscontrole-18-plus", "bestellen-via-whatsapp",
            "bezorgtijden-per-regio", "zakelijk-bestellen", "bezorgvoorwaarden", "bestelling-wijzigen-of-annuleren", "veilig-bestellen-oplichting-herkennen"]
FAQS = ["bestellen", "bezorgen", "betalen", "veiligheid", "regels"]
ALLOWED = {"/", "/bezorggebied/", "/lachgas-tanks/", "/lachgas-tanks/2kg/", "/lachgas-tanks/4kg/", "/lachgas-tanks/10kg/", "/informatie/", "/service/", "/veelgestelde-vragen/", "/contact/", "/over-ons/", "/algemene-voorwaarden/", "/privacy/", "/sitemap/"}
ALLOWED |= {"/informatie/%s/" % a for a in ARTICLES} | {"/service/%s/" % s for s in SERVICES} | {"/veelgestelde-vragen/%s/" % f for f in FAQS}
ALLOWED |= {"/bezorggebied/%s/" % h for h in HUBS} | {"/lachgas-bezorgen/%s/" % p for p in PLACES}
REQUIRED = ("slug", "name", "kind", "region", "gemeente", "title", "description", "h1", "lead", "intro", "levertijd", "faq", "nearby", "lat", "lon")
BAND = re.compile(r"\b(\d{1,2})( ?)(tot|en|-|–)( ?)(\d{2,3})( ?)(minuten|min)\b")
LEVERTIJD = "meestal binnen 15 tot 25 minuten"


def load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def words(s):
    return len(re.sub(r"<[^>]+>", "", s).split())


def check_text(label, s, errs, slug):
    for m in BAND.finditer(s):
        if not (m.group(1) == "15" and m.group(5) == "25"):
            errs.append("%s: andere tijdsband dan 15 tot 25 minuten: %r" % (label, m.group(0)))
    if "Brabant" in s or "brabant" in s:
        errs.append("%s: bevat 'Brabant'" % label)
    if re.search(r"€ ?\d|\d ?euro", s):
        errs.append("%s: noemt een prijs" % label)
    for href in re.findall(r'href="([^"]+)"', s):
        if href.startswith("http"):
            errs.append("%s: externe link %s (alleen interne links)" % (label, href))
        elif href not in ALLOWED:
            errs.append("%s: onbekende interne link %s" % (label, href))
    if re.search(r"<(?!/?a\b|/?strong\b|/?em\b)[a-z]", s):
        errs.append("%s: alleen <a>, <strong> en <em> zijn toegestaan in tekst" % label)


def check_entry(p, errs, fname):
    slug = p.get("slug", "?")
    L = "%s:%s" % (fname, slug)
    for k in REQUIRED:
        if k not in p:
            errs.append("%s: sleutel %r ontbreekt" % (L, k))
    if errs and any(e.startswith(L) and "ontbreekt" in e for e in errs):
        return
    if slug not in PLACES:
        errs.append("%s: slug staat niet in de plaatsenlijst" % L)
    elif p["region"] != PLACES[slug]:
        errs.append("%s: region %r, verwacht %r" % (L, p["region"], PLACES[slug]))
    if p["kind"] not in ("stad", "dorp", "wijk"):
        errs.append("%s: kind %r onbekend (stad/dorp/wijk)" % (L, p["kind"]))
    if p["kind"] in ("stad", "wijk") and "wijken" not in p:
        errs.append("%s: 'wijken' ontbreekt (verplicht bij stad/wijk)" % L)
    if p["kind"] == "dorp" and "kernen" not in p and "wijken" not in p:
        errs.append("%s: 'kernen' ontbreekt (verplicht bij dorp)" % L)
    if len(p["title"]) > 65:
        errs.append("%s: title te lang (%d > 65)" % (L, len(p["title"])))
    if not 110 <= len(p["description"]) <= 160:
        errs.append("%s: description %d tekens (110-160)" % (L, len(p["description"])))
    if not p["description"].rstrip().endswith("18+."):
        errs.append("%s: description eindigt niet op '18+.'" % L)
    if len(p["lead"]) > 240:
        errs.append("%s: lead te lang (%d > 240)" % (L, len(p["lead"])))
    if not (isinstance(p["intro"], list) and len(p["intro"]) == 3):
        errs.append("%s: intro moet een lijst van precies 3 alinea's zijn" % L)
    else:
        for i, para in enumerate(p["intro"]):
            w = words(para)
            if not 90 <= w <= 240:
                errs.append("%s: intro-alinea %d heeft %d woorden (90-240)" % (L, i + 1, w))
            check_text("%s intro %d" % (L, i + 1), para, errs, slug)
    if not (isinstance(p["faq"], list) and len(p["faq"]) == 3):
        errs.append("%s: faq moet precies 3 vragen bevatten" % L)
    else:
        for i, qa in enumerate(p["faq"]):
            if not (isinstance(qa, (list, tuple)) and len(qa) == 2):
                errs.append("%s: faq %d is geen [vraag, antwoord]" % (L, i + 1)); continue
            q, a = qa
            if not q.strip().endswith("?"):
                errs.append("%s: faq %d vraag eindigt niet op '?'" % (L, i + 1))
            w = words(a)
            if not 30 <= w <= 130:
                errs.append("%s: faq %d antwoord heeft %d woorden (30-130)" % (L, i + 1, w))
            check_text("%s faq %d" % (L, i + 1), a, errs, slug)
    for k in ("title", "description", "h1", "lead", "levertijd", "name", "gemeente"):
        check_text("%s %s" % (L, k), p[k], errs, slug)
        if "<" in p[k]:
            errs.append("%s: %s mag geen HTML bevatten" % (L, k))
    for k in ("wijken", "kernen"):
        if k in p:
            check_text("%s %s" % (L, k), p[k], errs, slug)
            if len(p[k].split(",")) < 5:
                errs.append("%s: %s noemt minder dan 5 namen" % (L, k))
    if slug != "texel" and p["levertijd"] != LEVERTIJD:
        errs.append("%s: levertijd moet exact %r zijn" % (L, LEVERTIJD))
    if slug == "texel" and "15 tot 25" in p["levertijd"]:
        errs.append("%s: Texel krijgt geen minutenband (bezorging rond de boot)" % L)
    nb = p["nearby"]
    if not (isinstance(nb, list) and 2 <= len(nb) <= 4):
        errs.append("%s: nearby moet 2 tot 4 slugs bevatten" % L)
    else:
        for s in nb:
            if s not in PLACES:
                errs.append("%s: nearby-slug %r bestaat niet" % (L, s))
            if s == slug:
                errs.append("%s: nearby verwijst naar zichzelf" % L)
    try:
        lat, lon = float(p["lat"]), float(p["lon"])
        if not (52.15 <= lat <= 53.25 and 4.4 <= lon <= 5.4):
            errs.append("%s: coördinaten %s,%s liggen buiten Noord-Holland" % (L, lat, lon))
    except (TypeError, ValueError):
        errs.append("%s: lat/lon geen getal" % L)


def main(paths):
    errs, seen = [], {}
    for path in paths:
        fname = os.path.basename(path)
        try:
            m = load(path)
        except Exception as e:  # noqa
            errs.append("%s: laadt niet: %s" % (fname, e)); continue
        areas = getattr(m, "AREAS", None)
        if not isinstance(areas, list) or not areas:
            errs.append("%s: AREAS ontbreekt of is leeg" % fname); continue
        for p in areas:
            if not isinstance(p, dict):
                errs.append("%s: item is geen dict" % fname); continue
            s = p.get("slug")
            if s in seen:
                errs.append("%s: slug %r komt ook voor in %s" % (fname, s, seen[s]))
            seen[s] = fname
            check_entry(p, errs, fname)
    if len(paths) >= len(HUBS):
        for s in PLACES:
            if s not in seen:
                errs.append("plaats %r (regio %s) ontbreekt" % (s, PLACES[s]))
    for e in errs:
        print("FOUT:", e)
    print("%d plaatsen gecontroleerd in %d bestand(en), %d fout(en)" % (len(seen), len(paths), len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    args = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "content", "areas_*.py")))
    sys.exit(main(args))
