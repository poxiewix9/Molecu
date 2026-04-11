"""Agent 4: Evidence Agent — searches PubMed for literature supporting each drug-disease pair."""

from backend.models import DrugCandidate, PaperCitation, EvidenceSummary
from backend.services.pubmed import search_drug_disease_literature
from backend.services.llm import ask_llm


async def gather_evidence(
    candidates: list[DrugCandidate],
    disease_name: str,
) -> list[EvidenceSummary]:
    """Search PubMed for each candidate and return structured evidence summaries."""
    summaries = []

    for drug in candidates:
        result = await search_drug_disease_literature(drug.drug_name, disease_name)

        papers = [
            PaperCitation(
                pmid=p["pmid"],
                title=p["title"],
                authors=p["authors"],
                journal=p["journal"],
                year=p["year"],
                url=p["url"],
            )
            for p in result["papers"][:3]
        ]

        if papers and result.get("abstracts"):
            abstract_text = "\n\n".join(
                f"[PMID:{pmid}] {text[:500]}"
                for pmid, text in list(result["abstracts"].items())[:3]
            )
            summary_text = await ask_llm(
                system_prompt=(
                    "You are a biomedical research assistant. Summarize the key findings "
                    "from these paper abstracts in 2-3 sentences. Focus on what evidence "
                    "supports or contradicts using this drug for this disease. Be factual."
                ),
                user_prompt=(
                    f"Drug: {drug.drug_name}\n"
                    f"Disease: {disease_name}\n\n"
                    f"Abstracts:\n{abstract_text}"
                ),
                max_tokens=300,
            )
            if not summary_text:
                summary_text = (
                    f"Found {result['paper_count']} paper(s) connecting {drug.drug_name} "
                    f"to {disease_name}. See citations for details."
                )
        elif papers:
            summary_text = (
                f"Found {result['paper_count']} paper(s) in PubMed. "
                f"Most recent: \"{papers[0].title}\" ({papers[0].journal}, {papers[0].year})."
            )
        else:
            summary_text = f"No published research found connecting {drug.drug_name} to {disease_name}."

        summaries.append(EvidenceSummary(
            drug_name=drug.drug_name,
            paper_count=result["paper_count"],
            top_papers=papers,
            evidence_summary=summary_text,
        ))

    return summaries
