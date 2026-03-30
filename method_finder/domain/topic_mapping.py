"""Map free-text research terms to DB-ALM-style topic labels."""

from __future__ import annotations

from rapidfuzz import fuzz, process


class TopicNormalizer:
    """Fuzzy and synonym-based mapping from protocol domain strings to catalogue topics."""

    def __init__(self) -> None:
        self.synonyms_to_topic: dict[str, str] = {
            "acute tox": "Acute Systemic Toxicity",
            "ld50": "Acute Systemic Toxicity",
            "repeated dose": "Repeated Dose Toxicity",
            "subacute": "Repeated Dose Toxicity",
            "liver": "Hepatotoxicity / Metabolism-mediated Toxicity",
            "skin": "Skin Irritation and Corrosivity",
            "skin irritation": "Skin Irritation and Corrosivity",
            "eye": "Eye Irritation",
            "eye irritation": "Eye Irritation",
            "eveit": "Eye Irritation",
            "ex vivo eye irritation test": "Eye Irritation",
            "perfusion corneal culture": "Eye Irritation",
            "acto e.v.": "Eye Irritation",
            "acto e.v": "Eye Irritation",
            "acto ev": "Eye Irritation",
            "endocrine": "Effects on Endocrine System",
            "cancer": "Carcinogenicity",
            "carcinogenicity": "Carcinogenicity",
            "histology": "Carcinogenicity and Histology",
            "genotoxicity": "Genotoxicity",
            "developmental toxicity": "Developmental toxicity",
            "developmental": "Developmental toxicity",
            "developmental / reproductive": "Developmental toxicity",
            "reproductive": "Developmental toxicity",
        }

        self.official_topic_labels: list[str] = [
            "Acute Systemic Toxicity",
            "Skin Irritation and Corrosivity",
            "Eye Irritation",
            "Repeated Dose Toxicity",
            "Hepatotoxicity / Metabolism-mediated Toxicity",
            "Effects on Endocrine System",
            "Genotoxicity",
            "Developmental toxicity",
            "Carcinogenicity",
        ]

    def normalize(self, raw_term: str) -> str:
        term = raw_term.lower().strip()

        if term in self.synonyms_to_topic:
            return self.synonyms_to_topic[term]

        best = process.extractOne(term, self.official_topic_labels, scorer=fuzz.WRatio)
        if best is None:
            return raw_term

        best_match, score, _ = best
        if score > 80:
            return best_match

        return raw_term
