import streamlit as st
import json
import itertools
from collections import defaultdict

with open("all_gecko_morphs_combined.json", "r", encoding="utf-8") as f:
    all_traits = sorted(list(set([t for t in json.load(f) if t and t.strip()])))

st.set_page_config(page_title="Calculadora Genética Gecko Leopardo", layout="centered")
st.title("🦎 Calculadora Genética Mendeliana - Gecko Leopardo Version 1.2")

EXPLICACIONES = {
    "Visual": "Expresa este gen o morph físicamente, se ve a simple vista.",
    "Het": "No se ve, pero porta el gen recesivo y puede transmitirlo.",
    "Pos Het": "Posible portador, no confirmado. Puede transmitir el gen o no.",
    "66% Het": "66% de probabilidad de ser portador recesivo.",
    "50% Het": "50% de probabilidad de ser portador recesivo.",
    "No porta": "No expresa ni transmite este gen.",
    "Super": "Tiene dos copias del gen co-dominante. Suele tener un fenotipo más intenso.",
}

def infer_tipo(trait):
    t = trait.lower()
    if t in ["wild", "wild type", "normal"]:
        return "base"
    if "het" in t or "patternless" in t or "albino" in t or "ecl...pher" in t or "rainwater" in t or "tremper" in t or "bell" in t:
        return "recesivo"
    elif "super" in t:
        return "co-dominante"
    else:
        return "dominante"

GENOTIPOS = {
    "recesivo": ["Visual", "Het", "Pos Het", "66% Het", "50% Het", "No porta"],
    "dominante": ["Visual", "No porta"],
    "co-dominante": ["Super", "Visual", "No porta"],
    "base": ["Visual"]
}

traits_padre = st.multiselect("Traits del Padre", options=all_traits, key="padre")
traits_madre = st.multiselect("Traits de la Madre", options=all_traits, key="madre")

def trait_inputs(label, traits):
    seleccion = {}
    for t in traits:
        tipo = infer_tipo(t)
        col1, col2 = st.columns([2, 3])
        with col1:
            sel = st.selectbox(f"{label}: {t}", GENOTIPOS[tipo], key=f"{label}_{t}")
        with col2:
            expl = EXPLICACIONES.get(sel, "")
            st.markdown(f"<span style='font-size:14px;color:#888;'>{expl}</span>", unsafe_allow_html=True)
        seleccion[t] = sel
    return seleccion

if traits_padre and traits_madre:
    st.write("----")
    st.write("Selecciona GENOTIPO para cada trait de cada progenitor:")
    padre_genos = trait_inputs("Padre", traits_padre)
    madre_genos = trait_inputs("Madre", traits_madre)
else:
    padre_genos = {}
    madre_genos = {}

def get_alleles(tipo, genotipo):
    if tipo == "recesivo":
        if genotipo == "Visual": return ["r", "r"]
        if genotipo == "Het": return ["R", "r"]
        if genotipo == "No porta": return ["R", "R"]
        if "het" in genotipo.lower(): return ["R", "r"]
    if tipo == "dominante":
        if genotipo == "Visual": return ["R", "r"]
        if genotipo == "No porta": return ["r", "r"]
    if tipo == "co-dominante":
        if genotipo == "Super": return ["R", "R"]
        if genotipo == "Visual": return ["R", "r"]
        if genotipo == "No porta": return ["r", "r"]
    if tipo == "base":
        return ["R", "R"]
    return ["R", "r"]

def resultado_trait(trait, tipo, geno_p, geno_m):
    """Devuelve diccionario {fenotipo: probabilidad} para un trait concreto."""
    # Caso base: Wild Type siempre al 100 %
    if tipo == "base":
        return {"Wild": 1.0}

    a1 = get_alleles(tipo, geno_p)
    a2 = get_alleles(tipo, geno_m)
    descendencia = [tuple(sorted([i, j])) for i in a1 for j in a2]
    n = len(descendencia)
    res = defaultdict(float)

    if tipo == "recesivo":
        for par in descendencia:
            if par == ("r", "r"):
                res["Visual"] += 1
            elif par.count("r") == 1 and par.count("R") == 1:
                res["Het"] += 1
            else:
                res["No porta"] += 1

    elif tipo == "co-dominante":
        for par in descendencia:
            if par == ("R", "R"):
                res["Super"] += 1
            elif par.count("R") == 1 and par.count("r") == 1:
                res["Visual"] += 1
            else:
                res["No porta"] += 1

    elif tipo == "dominante":
        for par in descendencia:
            if "R" in par:
                res["Visual"] += 1
            else:
                res["No porta"] += 1

    # Normalizar probabilidades
    for k in res:
        res[k] = res[k] / n
    return dict(res)

def cross_dicts(trait_results):
    keys = sorted(trait_results.keys())
    combs = [trait_results[k] for k in keys]
    combos = defaultdict(float)
    for prod in itertools.product(*combs):
        tags = []
        prob = 1.0
        for i, (fenotipo, p) in enumerate(prod):
            trait_name = keys[i]
            if fenotipo == "Visual":
                tag = f"<span style='background:#fa5757;color:white;padding:2px 8px;border-radius:8px;margin:2px'>Visual {trait_name}</span>"
            elif fenotipo == "Het":
                tag = f"<span style='background:#faaf45;color:white;padding:2px 8px;border-radius:8px;margin:2px'>Het {trait_name}</span>"
            elif fenotipo == "Super":
                tag = f"<span style='background:#7dd957;color:white;padding:2px 8px;border-radius:8px;margin:2px'>Super {trait_name}</span>"
            elif fenotipo == "No porta":
                tag = f"<span style='background:#bbbbbb;color:#222;padding:2px 8px;border-radius:8px;margin:2px'>Visual Wild (no porta {trait_name})</span>"
            elif fenotipo == "Wild":
                tag = f"<span style='background:#9ec3ff;color:#222;padding:2px 8px;border-radius:8px;margin:2px'>Wild Type</span>"
            else:
                tag = f"<span style='background:#dddddd;color:#222;padding:2px 8px;border-radius:8px;margin:2px'>{fenotipo} {trait_name}</span>"
            tags.append(tag)
            prob *= p
        combos[frozenset(tags)] += prob
    return combos

def calculate_full_cross(padre_genos, madre_genos):
    all_traits = sorted(set(list(padre_genos.keys()) + list(madre_genos.keys())))
    trait_results = {}
    for t in all_traits:
        tipo = infer_tipo(t)
        g1 = padre_genos.get(t, "No porta")
        g2 = madre_genos.get(t, "No porta")
        res = resultado_trait(t, tipo, g1, g2)
        trait_results[t] = list(res.items())
    return cross_dicts(trait_results)

if st.button("Calcular Descendencia") and padre_genos and madre_genos:
    st.subheader("Resultados posibles de la descendencia (combinaciones únicas):")
    resultados = calculate_full_cross(padre_genos, madre_genos)
    resultados = sorted(resultados.items(), key=lambda x: -x[1])
    for tags, prob in resultados:
        tags_str = " ".join(list(tags))
        st.markdown(f"**{prob*100:.0f}%** &nbsp; {tags_str}", unsafe_allow_html=True)
    st.caption("Calculadora actualizada con lógica real para Wild Type, Het y Visuales.")

st.info("Versión 1.2: lógica genética precisa, herencia recesiva, dominante, co-dominante y base (Wild Type) 🧬")
