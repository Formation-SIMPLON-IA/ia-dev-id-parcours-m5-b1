# Évaluation continue & seuils bloquants — Mini-cours

> Brief associé : M5-B2
> Durée de lecture : ~30 min
> Pré-requis : CI GitHub Actions (mini-cours 03), métriques de classif (M1)

## Pourquoi cette techno ?

Votre CI teste le **code**. Mais un dev peut casser le **modèle** sans casser
le code : un preprocessing modifié par erreur, et le F1 passe de 0.71 à 0.55 —
ça part en prod sans alerte. L'**évaluation continue** comble ce trou : à
chaque release, on recalcule les métriques modèle sur un **jeu de référence
figé**, et on **bloque la release** si une métrique passe sous un seuil.

C'est le geste C9 (amélioration continue) côté garde-fou. Pas de détection de
drift ici (c'est M6) : on reste sur des **seuils statiques** sur des métriques
globales, branchés dans la CI via un **code retour non-zéro**.

## Concepts clés

- **Jeu de référence (`reference_set.csv`)** : un sous-échantillon **figé** du
  holdout, versionné. Figé = comparable d'une release à l'autre. On le regénère
  seulement si la population change (et on le documente).
- **Baseline** : la performance annoncée au client (métriques holdout M1). Les
  seuils se définissent **par rapport** à elle.
- **Stratégies de seuil** : **absolu** (« F1 ≥ 0.55 quoi qu'il arrive »),
  **relatif** (« pas plus de 3 pts sous la baseline »), **hybride** (les deux).
  L'hybride est le plus robuste.
- **Code retour** : le script sort `0` si OK, **`1` si violation**. GitHub
  Actions interprète `exit 1` comme un échec → release bloquée. Un `print` ne
  bloque rien.
- **Idempotence** : `random_state` fixé partout → 2 exécutions donnent le même
  résultat (sinon les seuils sont du bruit).

## Exemple minimal qui tourne

```python
import sys
from sklearn.metrics import f1_score

THRESHOLDS = {"f1_macro": {"absolute_min": 0.55, "max_drop_vs_baseline": 0.03}}

def check(metrics, baseline):
    violations = []
    for name, rule in THRESHOLDS.items():
        v = metrics[name]
        if v < rule["absolute_min"]:
            violations.append(f"{name}={v} < {rule['absolute_min']}")
        if baseline.get(name) and baseline[name] - v > rule["max_drop_vs_baseline"]:
            violations.append(f"{name} a chuté > {rule['max_drop_vs_baseline']}")
    return violations

violations = check({"f1_macro": 0.50}, {"f1_macro": 0.61})
print(violations)
sys.exit(1 if violations else 0)   # ← bloque la CI
```

## Exercice guidé

Prouvez que le garde-fou marche :
1. Lancez votre `evaluate_model.py --release-tag ok` → doit sortir **exit 0**.
2. Ajoutez un mode `--degrade` qui **désaligne X et y** (ou casse une feature)
   → relancez → doit lister des violations et sortir **exit 1**.
3. Branchez l'étape `evaluate-model` dans `ci.yml` (`needs: test`) et poussez
   une dégradation : le workflow doit passer **rouge**.

## Pièges fréquents

| Piège | Conséquence |
|---|---|
| Seuil « magique » non justifié (« 0.65 ça me va ») | Indéfendable devant le client / le jury |
| `print` au lieu de `sys.exit(1)` | La release dégradée part quand même |
| Reference_set non figé (regénéré à chaque run) | Métriques non comparables, seuils inutiles |
| `random_state` oublié | Résultats non idempotents, faux positifs/négatifs |
| Jamais tester le chemin rouge | On découvre en prod que le garde-fou ne bloque pas |

| Symptôme | Cause probable |
|---|---|
| La CI reste verte malgré une dégradation | Script ne renvoie pas `exit 1`, ou étape pas branchée |
| Résultats différents à chaque run | `random_state` non fixé / reference_set instable |
| Seuil contesté en revue | Pas de justification chiffrée vs baseline |

## Pour aller plus loin

- scikit-learn metrics : https://scikit-learn.org/stable/modules/model_evaluation.html
- GitHub Actions — job status & exit codes : https://docs.github.com/actions/writing-workflows
- Continuous evaluation (concept) : https://ml-ops.org/content/mlops-principles

## Vérification (checklist apprenant)

- [ ] Mon `reference_set.csv` est figé et versionné.
- [ ] Chaque seuil est **justifié** par rapport à la baseline.
- [ ] Le script sort **exit 1** sur dégradation (testé au moins une fois).
- [ ] L'étape `evaluate-model` bloque réellement la release en CI.
- [ ] Mes résultats sont idempotents (`random_state` fixé).
