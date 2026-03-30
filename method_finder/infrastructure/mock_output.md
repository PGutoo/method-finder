# 🔬 Protocol Assessment Report: *T. parthenium* Essential Oil

| Field | Value |
|:---|:---|
| **Date** | 2026-03-29 |
| **Input Study** | Bulgarian Plant Extract Toxicology (Wistar Rat) |
| **Analysis Type** | 3Rs Alternative Method Mapping |

---

## Section 3.5.1: Acute Toxicity (LD50)

### Extracted parameters

| Parameter | Value |
| :--- | :--- |
| **Category** | Acute Tox |
| **Species** | Rat |
| **Strain** | Wistar |
| **Sex** | male |
| **Animals (n)** | 60 |
| **Route** | p.o. / i.p. |
| **Duration** | up to 24 h observation |
| **Organs / tissues** | — |
| **Endpoints** | LD50, mortality, clinical signs |
| **Regulatory reference** | Yes |
| **Test article** | T. parthenium essential oil |
| **Procedure** | Single-dose acute toxicity; Litchfield–Wilcoxon LD50 |

### Recommended Alternatives

| Method Name | Validation Status | Species Replaced | Endpoint Type | Source |
| :--- | :--- | :--- | :--- | :--- |
| **3T3 Neutral Red Uptake (NRU)** | **Validated (OECD TG 129)** | Wistar Rat / Mouse | Basal Cytotoxicity / LD50 Prediction | [EURL ECVAM](https://joint-research-centre.ec.europa.eu/projects-and-activities/reference-and-measurement/european-union-reference-laboratories/eu-reference-laboratory-alternatives-animal-testing-eurl-ecvam/alternative-methods-toxicity-testing/validated-test-methods-health-effects/acute-toxicity/acute-oral_en) |
| **T.E.S.T. (QSAR Model)** | **Regulatory Accepted** | *In Silico* (No Animals) | LD50 / GHS Hazard Category | [EPA Resource](https://www.epa.gov/chemical-research/toxicity-estimation-software-tool-test) |

> **💡 Tool Insight:** Since your sample is an **Essential Oil**, the NRU assay is highly recommended as a range-finder. It can reduce animal use by up to 40% by accurately predicting the starting dose, even if a full replacement is not yet accepted for complex botanicals.

---

## Section 3.5.2: Repeated Dose Toxicity (28-Day)

### Extracted parameters

| Parameter | Value |
| :--- | :--- |
| **Category** | Repeated Dose |
| **Species** | Rat |
| **Strain** | Wistar |
| **Sex** | male |
| **Animals (n)** | 20 |
| **Route** | p.o. (gavage) |
| **Duration** | 28 days + sampling |
| **Organs / tissues** | blood (serum) |
| **Endpoints** | body weight, hematology, serum biochemistry |
| **Regulatory reference** | No |
| **Test article** | T. parthenium EO in vehicle |
| **Procedure** | 28-day repeated oral toxicity |

### Recommended Alternatives

| Method Name | Validation Status | Species Replaced | Endpoint Type | Source |
| :--- | :--- | :--- | :--- | :--- |
| **HepaRG™ System** | **Scientific Validation** | Rat (Liver toxicity) | Hepatotoxicity / ALT & AST Markers | [DB-ALM-158](https://purl.jrc.ec.europa.eu/dataset/db-alm/method/158) |
| **OECD IATA Framework** | **Standard Guidance** | Rodent (Systemic) | Multi-endpoint Weight of Evidence | [OECD IATA Case Studies](https://www.oecd.org/en/topics/sub-issues/assessment-of-chemicals/integrated-approaches-to-testing-and-assessment.html) |

> **💡 Tool Insight:** Systemic repeated dose toxicity is complex. Instead of a single “test tube” replacement, use an **Integrated Approach to Testing and Assessment (IATA)**. This combines the HepaRG cell model (for your liver markers) with *in silico* predictions to justify reducing the 28-day study to a 7-day “dose range finder.”

---

## Section 3.5.3: Histological Evaluation

### Extracted parameters

| Parameter | Value |
| :--- | :--- |
| **Category** | Other (histology) |
| **Species** | Rat |
| **Strain** | Wistar |
| **Sex** | not stated |
| **Animals (n)** | subset |
| **Route** | — |
| **Duration** | day 29 |
| **Organs / tissues** | brain, heart, stomach, liver, spleen, kidney |
| **Endpoints** | H&E histopathology |
| **Regulatory reference** | No |
| **Test article** | — |
| **Procedure** | Post-mortem organs for histology |

### Recommended Alternatives

| Method Name | Validation Status | Species Replaced | Endpoint Type | Source |
| :--- | :--- | :--- | :--- | :--- |
| **Multi-Organ-on-a-Chip (MOC)** | **Innovative / R&D** | Rodent (Organ crosstalk) | Pathological changes / Tissue architecture | [NC3Rs Resource Library](https://nc3rs.org.uk/3rs-resource-library) |
| **Bhas 42 CTA** | **Validated (OECD GD 231)** | Rodent (Systemic) | Cell Transformation / Morphological Change | [DB-ALM-130](https://pubmed.ncbi.nlm.nih.gov/25803194/) |

> **💡 Tool Insight:** For structural changes, look into **Virtual Second Species** computational models (NC3Rs). These can simulate organ-level damage based on chemical structure, potentially replacing the need for sectioning and staining animal tissues.

---

## Summary Recommendation

For this protocol, a **hybrid approach** is suggested. Move the Acute Toxicity (3.5.1) to an *in vitro* NRU range-finder to minimize rat usage, and utilize the HepaRG cell line to supplement the 28-day serum biochemistry data (3.5.2).
