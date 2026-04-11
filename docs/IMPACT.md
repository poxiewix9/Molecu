# Impact & Sustainability

## The Problem at Scale

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         RARE DISEASE CRISIS                                │
│                                                                            │
│    7,000+           400M+            95%              50%                  │
│    Rare             People           Have NO          Of patients          │
│    Diseases         Affected         Treatment        are children         │
│                                                                            │
│    $2.6B            90%              $10K-$50K        Weeks                │
│    Avg cost of      Drug candidates  Annual cost of   Time for manual     │
│    new drug         fail trials      commercial tools cross-referencing    │
└────────────────────────────────────────────────────────────────────────────┘
```

## Who Benefits

### 1. College Researchers & Grad Students
**Before**: Can't afford Clarivate ($30K/yr). Spend weeks manually searching Open Targets, then ClinicalTrials.gov, then PubMed, then FAERS — in separate browser tabs, cross-referencing by hand.

**After**: Type a disease name. Get ranked candidates with scores, safety data, PubMed citations, and a PDF report ready for their advisor — in 60 seconds. For free.

**Time saved**: ~40 hours per disease investigation
**Money saved**: $10,000–$50,000/year in tool licensing

### 2. Rare Disease Patient Advocacy Organizations
Organizations like NORD, Global Genes, and disease-specific foundations lack pharma resources.

**Before**: Rely on volunteer researchers, can't systematically evaluate drug candidates.
**After**: Generate evidence reports to advocate for clinical trials with specific candidates, backed by real database evidence.

### 3. Academic Medical Centers
**Before**: Grant proposals require preliminary drug candidate identification — a months-long literature review.
**After**: Generate PDF reports with evidence scores, PubMed citations, and methodology documentation ready for grant applications.

### 4. Pharmaceutical Companies
**Before**: Shelved drug assets represent billions in sunk R&D cost.
**After**: Identify new indications for existing assets. Drug repurposing costs ~$300M vs. ~$2.6B for de novo development — a **~90% cost reduction**.

### 5. Patients & Families
**Impact**: Every drug candidate identified is a potential lifeline for patients who currently have zero treatment options.

---

## Economic Impact Analysis

### Cost of Drug Development

```
Traditional Drug Development:
┌──────────────────────────────────────────────────────────────────────────┐
│  Discovery → Preclinical → Phase 1 → Phase 2 → Phase 3 → Approval     │
│    2-4 yr      1-2 yr      1-2 yr    2-3 yr    2-4 yr    1-2 yr      │
│                                                                         │
│  Total: 10-15 years, $2.6 billion average                              │
│  Success rate: ~10%                                                     │
└──────────────────────────────────────────────────────────────────────────┘

Drug Repurposing (with PharmaSynapse):
┌──────────────────────────────────────────────────────────────────────────┐
│  AI Identification → Validation → Phase 2 → Phase 3 → Approval         │
│     60 seconds        1-2 yr      2-3 yr    2-4 yr    1-2 yr          │
│                                                                         │
│  Total: 6-10 years, ~$300 million average                              │
│  Potential savings per successful repurposing: $2+ billion             │
└──────────────────────────────────────────────────────────────────────────┘
```

### Paywall Disruption

PharmaSynapse replaces the functionality of tools costing $10K–$50K/year per seat:

| Commercial Tool | Cost/Year | PharmaSynapse Equivalent |
|----------------|----------|-------------------------|
| Clarivate Cortellis | ~$30,000 | Multi-agent pipeline with same data sources |
| Elsevier Pathway Studio | ~$15,000 | Target-drug-disease mapping via Open Targets + ChEMBL |
| BenchSci | ~$20,000 | Literature search via PubMed + evidence scoring |
| **Total replaced** | **$65,000/yr** | **$0** |

For a university with 10 researchers, that's **$650,000/year in potential savings**.

---

## Ethical Considerations

### Responsible AI Use

1. **Full Transparency**: Every score component traces to a specific database record
2. **No Black Box**: Evidence scoring is deterministic — no LLM involved in ranking
3. **Source Attribution**: Every claim includes a clickable link to the original database
4. **Uncertainty Acknowledgment**: Scores, not certainty. Candidates, not prescriptions.
5. **Disclaimer**: Prominent "Research tool — not medical advice" banner on every results page

### Not Replacing Human Judgment

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PharmaSynapse is a RESEARCH TOOL, not medical advice                   │
│                                                                          │
│  ✓ Generates hypotheses for expert evaluation                           │
│  ✓ Accelerates database cross-referencing                               │
│  ✓ Ranks candidates by evidence strength                                │
│  ✓ Links every claim to its source                                      │
│                                                                          │
│  ✗ Does NOT replace clinical trials                                     │
│  ✗ Does NOT provide treatment recommendations                           │
│  ✗ Does NOT guarantee drug efficacy                                     │
│  ✗ Does NOT use AI to generate safety assessments                       │
└──────────────────────────────────────────────────────────────────────────┘
```

### Data Privacy
- **No patient data**: We process zero PHI
- **No user accounts**: No personal information collected
- **Public data only**: Every API we query is publicly accessible
- **Local sessions**: Research data stays in the researcher's browser

---

## Empirical Validation

The economic and time savings claims above are architecturally plausible but require empirical backing. We have designed and documented a **self-validation protocol** (see [VALIDATION.md](./VALIDATION.md)) that tests the pipeline against diseases with known successful drug repurposings:

| Case Study | Disease | Known Drug | Expected Outcome |
|-----------|---------|------------|------------------|
| 1 | Pulmonary Arterial Hypertension | Sildenafil (Revatio) | Drug surfaces in top 3, score ≥ 60/100 |
| 2 | Multiple Myeloma | Thalidomide (Thalomid) | Drug surfaces + contradiction detector fires (efficacy vs safety conflict) |
| 3 | Polycystic Ovary Syndrome | Metformin | Drug surfaces via insulin resistance pathway targets |

**Why this matters**: If the scoring system reliably recovers drugs that have already been validated by clinical trials and FDA approval, it provides strong evidence that the "60 seconds vs. weeks" claim is not just architecturally plausible but empirically grounded. The full protocol, expected outcomes, and future calibration plans are documented in [VALIDATION.md](./VALIDATION.md).

---

## Sustainability

### Open Source Foundation
- Core platform free and open source (MIT License)
- Community contributions welcome
- Academic use unrestricted
- No vendor lock-in — all data sources are public APIs

### Future Revenue Streams (if needed)
| Stream | Description |
|--------|-------------|
| **NIH Grants** | SBIR/STTR grants for rare disease research tools |
| **Foundation Partnerships** | Sponsored analysis for specific rare diseases |
| **Enterprise API** | Rate-limited API access for biotech companies |
| **Consulting** | Custom integration for research institutions |

The core tool remains free forever. Revenue only needed for infrastructure scaling.
