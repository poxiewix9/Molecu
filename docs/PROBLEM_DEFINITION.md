# Problem Definition

## Executive Summary

**Problem**: 95% of rare diseases have no approved treatment, affecting 400 million people globally. Meanwhile, pharmaceutical companies have shelved thousands of drugs that passed human safety trials — many of which could treat rare diseases.

**Gap**: The tools that cross-reference biomedical databases to find these matches cost $10,000–$50,000/year per researcher. The data itself is public and free. The analysis shouldn't be paywalled.

**Our Solution**: A free, open-source multi-agent AI system that queries 6 public biomedical databases, applies transparent evidence-based scoring, and provides a persistent research workbench with PDF export — replacing $50K/year commercial tools with a $0 open-source alternative.

---

## Problem Deep Dive

### The Rare Disease Crisis

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        RARE DISEASE STATISTICS                           │
├──────────────────────────────────────────────────────────────────────────┤
│  7,000+     Identified rare diseases            (NORD, rarediseases.org) │
│  400M+      People affected globally           (Global Genes, 2023)     │
│  95%        Diseases with NO approved treatment (FDA Orphan Drug Report) │
│  50%        Patients are children               (Eurordis, 2024)        │
│  30%        Won't live to age 5                 (Eurordis, 2024)        │
│  7 years    Average time to diagnosis           (NORD, 2022)            │
│  <10%       NIH funding goes to rare diseases   (NCATS, nih.gov)        │
└──────────────────────────────────────────────────────────────────────────┘
```

### The Failed Drug Paradox

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        FAILED DRUG STATISTICS                            │
├──────────────────────────────────────────────────────────────────────────┤
│  90%        Drug candidates fail clinical trials  (DiMasi et al., 2016)  │
│  $2.6B      Average cost per successful drug     (Tufts CSDD, 2016)     │
│  ~50%       Fail for efficacy (not safety)       (Arrowsmith, 2011)     │
│  Billions   In R&D investment on shelves         (PhRMA, 2023)          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key insight**: A drug that failed for one indication may still be:
- ✅ Safe for human use (passed Phase 1/2 safety trials)
- ✅ Manufactured and available
- ✅ Fully characterized pharmacologically
- ✅ Potentially effective for different disease mechanisms

### The Paywall Problem

A researcher trying to evaluate drug repurposing candidates needs to cross-reference data from:

1. **Open Targets** — Which proteins are involved in the disease?
2. **ClinicalTrials.gov** — Which drugs targeted those proteins but failed?
3. **ChEMBL** — What other drugs bind to those protein targets?
4. **FDA FAERS** — Are those drugs safe? What adverse events were reported?
5. **PubMed** — Has anyone published evidence linking drug X to disease Y?
6. **PubChem** — What's the molecular structure?

Each database has its own interface, query language, and data format. **Doing this manually takes days to weeks per disease.**

The commercial tools that automate this:
| Tool | Cost | Accessible to a grad student? |
|------|------|------|
| Clarivate Cortellis | ~$30,000/yr | No |
| Elsevier Pathway Studio | ~$15,000/yr | No |
| BenchSci | ~$20,000/yr | No |

**PharmaSynapse queries the same underlying public databases for $0.**

---

## Our Hypothesis

> If we automate multi-source biomedical data synthesis with specialized AI agents and apply transparent, deterministic scoring, we can generate research-grade drug repurposing hypotheses at scale — for free.

### Validation Criteria (All Implemented)

1. **Biological plausibility**: Drug mechanism addresses disease target (Open Targets association score)
2. **Safety clearance**: Drug has acceptable safety profile (FDA FAERS rule-based classification)
3. **Evidence support**: Literature provides supporting rationale (PubMed paper count)
4. **Trial progression**: Drug reached advanced human trials (ClinicalTrials.gov phase data)
5. **Logical consistency**: No contradictions between data sources (DeBERTa NLI detection)

---

## User Personas

### Primary: College Researcher / Grad Student
- **Goal**: Find drug repurposing candidates for their thesis or lab project
- **Pain point**: Can't afford commercial tools, spends weeks on manual database searches
- **Needs**: Free tool, ranked results, exportable for advisor review
- **PharmaSynapse delivers**: $0 cost, 60-second analysis, PDF reports for advisors

### Secondary: Rare Disease Foundation Researcher
- **Goal**: Identify promising treatments to advocate for clinical trials
- **Pain point**: Limited technical resources, no pharma-grade database access
- **Needs**: Accessible interface, evidence-backed candidates, shareable reports
- **PharmaSynapse delivers**: Plain-English summaries, source links, downloadable PDFs

### Tertiary: Biotech R&D Scientist
- **Goal**: Find new indications for shelved pipeline assets
- **Pain point**: Internal data silos, manual cross-referencing
- **Needs**: Systematic search, transparent scoring, JSON export for pipelines
- **PharmaSynapse delivers**: Evidence scores, API endpoints, structured JSON export

---

## Competitive Differentiation

| Feature | Manual Search | Generic LLM Chatbot | Commercial Platforms | **PharmaSynapse** |
|---------|--------------|---------------------|---------------------|-------------------|
| Cost | Free (but slow) | $20/mo | $10K–$50K/yr | **Free** |
| Speed | Days–weeks | Minutes | Minutes | **60 seconds** |
| Source attribution | Manual | None (hallucination risk) | Yes | **Yes (every claim)** |
| Transparent scoring | N/A | No | Proprietary | **Yes (open formula)** |
| PDF reports | Manual formatting | No | Yes | **Yes (client-side)** |
| Persistent sessions | Browser tabs | Chat history | Yes | **Yes (localStorage)** |
| Researcher annotations | Paper notes | No | Some | **Yes (stars + notes)** |
| Drug comparison | Manual | No | Some | **Yes (side-by-side)** |
| Real databases | Yes | No | Yes | **Yes (6 APIs)** |
| Open source | N/A | No | No | **Yes (MIT)** |

### Why Existing Free/Open-Source Tools Don't Solve This

Several free tools exist in the drug repurposing space. Here's why PharmaSynapse fills a different gap:

| Tool | What It Does | Gap PharmaSynapse Fills |
|------|-------------|------------------------|
| **OpenTargets Platform** ([targetvalidation.org](https://platform.opentargets.org/)) | Disease-target association browser | Single database only — no drug candidates, no safety data, no literature synthesis, no cross-referencing. PharmaSynapse *uses* Open Targets as one of six data sources and adds automated pipeline logic |
| **RepurposeDB** ([repurposedb.com](http://repurposedb.com/)) | Static database of known drug-disease pairs from literature | Read-only catalog, not a discovery engine. No scoring, no safety analysis, no real-time API queries, no research workbench. PharmaSynapse identifies *new* candidates from live clinical trial data |
| **Drug Repurposing Hub** (Broad Institute) | Curated library of ~6,000 compounds with annotations | Focused on compound library screening, not evidence synthesis. No cross-database pipeline, no scoring, no literature aggregation |
| **Pharos** ([pharos.nih.gov](https://pharos.nih.gov/)) | NIH target knowledge browser | Target-centric, not drug-repurposing-centric. No failed trial search, no safety pipeline, no PDF export. Complementary data source, not a workflow tool |
| **OpenFDA** ([open.fda.gov](https://open.fda.gov/)) | Raw adverse event search API | API only — no disease-to-drug pipeline, no scoring, no UI. PharmaSynapse integrates FAERS data as one input to a multi-agent pipeline |

| **Hetionet** ([het.io](https://het.io)) | Network medicine knowledge graph linking genes, diseases, compounds, and anatomies via 24 relationship types | Static pre-computed graph — powerful for exploring known relationships, but doesn't query live clinical trial data, doesn't provide real-time safety analysis from FDA FAERS, and doesn't score candidates for repurposing potential. Complementary data source, not a discovery workflow |
| **OpenPrescribing** ([openprescribing.net](https://openprescribing.net/)) | NHS prescribing data analytics (UK) | Focused on prescribing patterns, not drug repurposing. Useful for understanding real-world drug usage but doesn't connect diseases to targets, doesn't search failed trials, and has no scoring system. Geography-limited (UK NHS data only) |

### Addressing Institutional Access

Some well-resourced academic institutions have **institutional Cortellis or Pathway Studio licenses**, which reduces the addressable market among top-tier research universities. However:

1. **Access inequality persists**: Institutional licenses typically cover 5-20 seats. A university with 200 biomedical researchers still has the majority without access. Junior researchers, visiting scholars, and students are often excluded from seat allocations.
2. **Global majority lacks access**: Institutions in low- and middle-income countries — where rare disease burden is highest — rarely have institutional licenses. PharmaSynapse serves this underserved global majority.
3. **Different workflow**: Even researchers with Cortellis access benefit from PharmaSynapse's automated pipeline that generates a complete analysis in 60 seconds. Cortellis requires manual query construction across multiple modules.
4. **Open science alignment**: Institutional licenses create knowledge silos. PharmaSynapse's open-source approach means any analysis can be reproduced and verified by anyone.

**The core differentiator**: None of these tools provide an end-to-end automated pipeline that starts from a disease name and produces ranked, scored, safety-checked drug candidates with literature evidence — in a single interface — for free. PharmaSynapse is a *workflow tool* that chains these data sources together, not just another database browser.
