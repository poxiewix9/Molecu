"""ChEMBL REST API wrapper — look up approved/clinical drugs by protein target."""

import httpx
import logging

log = logging.getLogger(__name__)

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"


async def _resolve_molecule_name(molecule_chembl_id: str) -> str | None:
    """Look up a molecule's preferred name by its ChEMBL ID."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/molecule/{molecule_chembl_id}.json")
            if resp.status_code != 200:
                return None
            data = resp.json()
            return data.get("pref_name") or None
    except Exception:
        return None


async def search_drugs_for_target(gene_name: str, limit: int = 10) -> list[dict]:
    """Find approved or clinical-phase drugs that act on a given gene/protein target."""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            target_resp = await client.get(f"{BASE_URL}/target/search.json", params={
                "q": gene_name,
                "limit": "3",
            })
            target_resp.raise_for_status()
            target_data = target_resp.json()

        targets = target_data.get("targets", [])
        if not targets:
            return []

        chembl_id = targets[0].get("target_chembl_id")
        if not chembl_id:
            return []

        async with httpx.AsyncClient(timeout=20) as client:
            mech_resp = await client.get(f"{BASE_URL}/mechanism.json", params={
                "target_chembl_id": chembl_id,
                "limit": str(limit),
            })
            mech_resp.raise_for_status()
            mech_data = mech_resp.json()

        mechanisms = mech_data.get("mechanisms", [])
        drugs = []
        seen = set()
        for mech in mechanisms:
            mol_name = mech.get("molecule_name") or ""
            chembl_mol_id = mech.get("molecule_chembl_id", "")

            if not mol_name or mol_name.startswith("CHEMBL"):
                if chembl_mol_id:
                    resolved = await _resolve_molecule_name(chembl_mol_id)
                    if resolved:
                        mol_name = resolved
                    else:
                        continue
                else:
                    continue

            if mol_name in seen:
                continue
            seen.add(mol_name)

            drugs.append({
                "drug_name": mol_name,
                "molecule_chembl_id": chembl_mol_id,
                "mechanism_of_action": mech.get("mechanism_of_action", ""),
                "action_type": mech.get("action_type", ""),
                "target_chembl_id": chembl_id,
                "source": "ChEMBL",
            })

        return drugs

    except Exception as e:
        log.warning("ChEMBL search failed for %s: %s", gene_name, e)
        return []


async def search_drugs_for_targets(gene_names: list[str], max_per_target: int = 5) -> list[dict]:
    """Search ChEMBL for drugs targeting multiple genes. De-duplicates by drug name."""
    all_drugs = []
    seen = set()

    for gene in gene_names[:5]:
        results = await search_drugs_for_target(gene, limit=max_per_target)
        for drug in results:
            name = drug["drug_name"].lower()
            if name not in seen:
                seen.add(name)
                drug["matched_target"] = gene
                all_drugs.append(drug)

    return all_drugs
