"""Medical terminology table for peptide book retrieval.

Provides drug-name → drug-class mappings for query expansion.
Used by context_selector to cross-match medical terms that vector
similarity may miss (e.g., "semaglutide" → "GLP-1 receptor agonist").

This is a targeted enrichment — not a general embedding change.
"""

from __future__ import annotations

# Drug name → drug class / mechanism mapping
# Used for query expansion: when a query contains a drug name,
# also search for its class/mechanism
DRUG_TO_CLASS: dict[str, str] = {
    # GLP-1 agonists
    "semaglutide": "GLP-1 receptor agonist",
    "liraglutide": "GLP-1 receptor agonist",
    "dulaglutide": "GLP-1 receptor agonist",
    "exenatide": "GLP-1 receptor agonist",
    "lixisenatide": "GLP-1 receptor agonist",
    "tirzepatide": "GLP-1/GIP dual agonist",
    "retatrutide": "GLP-1/GIP/glucagon triple agonist",
    "zepbound": "GLP-1/GIP dual agonist",
    "mounjaro": "GLP-1/GIP dual agonist",
    "ozempic": "GLP-1 receptor agonist",
    "wegovy": "GLP-1 receptor agonist",
    "rybelsus": "GLP-1 receptor agonist",
    "victoza": "GLP-1 receptor agonist",
    "saxenda": "GLP-1 receptor agonist",
    # GHRH / GH secretagogues
    "sermorelin": "GHRH analog",
    "cjc-1295": "GHRH analog",
    "tesamorelin": "GHRH analog",
    "ipamorelin": "GH secretagogue",
    "tb-500": "synthetic peptide",
    "bpc-157": "gastric peptide",
    "ghrh": "growth hormone-releasing hormone",
    "ghsecretagogue": "GH secretagogue",
    # Other peptides
    "epitalon": "telomerase activator",
    "mots-c": "mitochondrial peptide",
    "ziconotide": "calcium channel blocker",
    "pipelotide": "synthetic peptide",
    "dsip": "Delta sleep-inducing peptide",
    "emideltide": "Delta sleep-inducing peptide",
    "melanotan": "melanocortin receptor agonist",
    "pt-141": "melanocortin receptor agonist",
    # Generic terms
    "glp-1": "GLP-1 receptor agonist",
    "gip": "glucose-dependent insulinotropic polypeptide",
    "glucagon": "glucagon receptor agonist",
    "tsh": "thyroid stimulating hormone",
    "t3": "triiodothyronine",
    "t4": "thyroxine",
    "hcg": "human chorionic gonadotropin",
    "hgh": "human growth hormone",
    "insulin": "peptide hormone",
    "oxytocin": "peptide hormone",
    "vasopressin": "peptide hormone",
    "ghrelin": "hunger hormone",
    "leptin": "satiety hormone",
}


def expand_query_with_terminology(query: str) -> str:
    """Expand a medical query with known drug class synonyms.

    For each drug name found in the query, append its class/mechanism
    to the query string. This helps BM25 and vector search cross-match
    between drug names and their therapeutic classes.

    Example:
        "How does semaglutide work?"
        → "How does semaglutide work? GLP-1 receptor agonist"
    """
    q_lower = query.lower()
    expansions: list[str] = []
    for drug, class_name in DRUG_TO_CLASS.items():
        if drug in q_lower and class_name.lower() not in q_lower:
            expansions.append(class_name)
    if expansions:
        return f"{query} {' '.join(expansions)}"
    return query


def get_drug_class(drug_name: str) -> str | None:
    """Get the drug class for a given drug name."""
    return DRUG_TO_CLASS.get(drug_name.lower())
