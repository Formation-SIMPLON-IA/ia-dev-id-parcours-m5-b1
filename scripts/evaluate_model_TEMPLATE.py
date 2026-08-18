"""Évaluation continue + tracking MLflow (SQUELETTE M5-B2 À COMPLÉTER).

À chaque release : recalcule les métriques cibles sur un jeu de référence
figé, **trace le run dans MLflow**, compare aux seuils, et **sort un code
retour non-zéro** si dégradation (→ bloque la release en CI).

Renommez ce fichier en `scripts/evaluate_model.py` une fois complété.
Mini-cours : `07_MLflow_tracking_essentiel.md` + `08_Evaluation_continue_seuils`.

Usage cible::

    python scripts/evaluate_model.py --release-tag v2.0.0
    python scripts/evaluate_model.py --release-tag bad --degrade   # test du rouge
    mlflow ui    # comparer les runs
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import mlflow
import pandas as pd

ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "services" / "model" / "models"
REFERENCE_SET = ROOT / "data" / "reference_set.csv"

# TODO 1 — définir vos seuils (stratégie absolu / relatif / hybride).
#   Documentez-les ET justifiez-les dans evaluation_thresholds.md.
THRESHOLDS: dict[str, dict[str, float]] = {
    # "f1_macro": {"absolute_min": ..., "max_drop_vs_baseline": ...},
}


def compute_metrics(model, df: pd.DataFrame, meta: dict) -> dict[str, float]:
    """Calcule les métriques cibles sur le jeu de référence."""
    # TODO 2 — construire X (feature_columns_*) et y (target + target_mapping),
    #   prédire, et calculer f1_macro / f1_default / roc_auc / recall_default.
    raise NotImplementedError


def check_thresholds(metrics: dict[str, float], baseline: dict) -> list[str]:
    """Retourne la liste des violations de seuil (vide = release OK)."""
    # TODO 3 — comparer chaque métrique à son plancher absolu ET à la baisse
    #   max tolérée vs baseline. Retourner les messages de violation.
    raise NotImplementedError


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-tag", default="dev")
    parser.add_argument("--degrade", action="store_true")
    args = parser.parse_args()

    model = joblib.load(MODELS_DIR / "pyrenex_risk_v2.joblib")
    meta = json.loads((MODELS_DIR / "pyrenex_risk_v2.json").read_text(encoding="utf-8"))
    df = pd.read_csv(REFERENCE_SET)

    if args.degrade:
        # TODO 4 — simuler un bug de preprocessing réaliste (ex. désaligner
        #   X et y) pour PROUVER que le rouge bloque bien la release.
        pass

    metrics = compute_metrics(model, df, meta)
    baseline = meta.get("metrics_holdout", {})
    violations = check_thresholds(metrics, baseline)

    # --- Bloc MLflow PRÉ-CÂBLÉ — complétez params + metrics ------------------
    mlflow.set_experiment("pyrenex-eval-continue")
    with mlflow.start_run(run_name=args.release_tag):
        mlflow.log_params(
            {
                "model_version": meta["model_version"],
                "release_tag": args.release_tag,
                # TODO 5 — ajouter reference_set, n_reference…
            }
        )
        mlflow.log_metrics(metrics)              # ← les 4 métriques tracées
        mlflow.set_tag("release_blocked", str(bool(violations)))
    # ------------------------------------------------------------------------

    print(json.dumps({"metrics": metrics, "violations": violations}, indent=2))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
