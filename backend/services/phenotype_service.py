# backend/services/phenotype_service.py
from schemas import IntakeSchema

def classify_phenotype(data: IntakeSchema) -> str:
    """
    Classifies a patient into Rotterdam-aligned PMOS phenotypes based on symptom presentation:
    - Phenotype A (Classic): Hyperandrogenism + Ovulatory Dysfunction + Polycystic Ovaries (USG)
    - Phenotype B (Ovulatory-Hyperandrogenic): Hyperandrogenism + Ovulatory Dysfunction without USG cysts
    - Phenotype C (Metabolic-Adrenal): Hyperandrogenism + USG cysts, or metabolic/stress indicators
    - Phenotype D (Normo-Androgenic): Ovulatory Dysfunction + USG cysts without overt androgen symptoms
    """
    has_hyperandrogenism = bool(data.symp_hair or data.symp_thinning or data.symp_acne)
    has_ovulatory_dysfunction = bool(data.symp_periods)
    has_pcom_ultrasound = str(data.usg_result).lower() in ["cysts", "polycystic", "pco"]

    if has_hyperandrogenism and has_ovulatory_dysfunction and has_pcom_ultrasound:
        return "Phenotype A: Classic PMOS"
    elif has_hyperandrogenism and has_ovulatory_dysfunction and not has_pcom_ultrasound:
        return "Phenotype B: Ovulatory-Hyperandrogenic PMOS"
    elif has_hyperandrogenism and not has_ovulatory_dysfunction and has_pcom_ultrasound:
        return "Phenotype C: Metabolic-Adrenal PMOS"
    elif not has_hyperandrogenism and has_ovulatory_dysfunction and has_pcom_ultrasound:
        return "Phenotype D: Normo-Androgenic PMOS"
    elif data.symp_weight or data.symp_stress:
        return "Phenotype C: Metabolic-Adrenal PMOS"

    return "Phenotype B: Ovulatory-Hyperandrogenic PMOS"
