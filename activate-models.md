# Modèles Claude activés sur Vertex AI

> Généré le 2026-04-09  
> Source : API `v1beta1/publishers/anthropic/models` — Vertex AI Model Garden

---

## Synthèse

| Projet | ID Projet | us-east5 | us-central1 | europe-west1 | europe-west4 | asia-southeast1 |
|--------|-----------|:--------:|:-----------:|:------------:|:------------:|:---------------:|
| prj-agentic-factory-sbx | prj-240444336327 | 4 | 8 | 4 | 3 | 2 |
| prj-ai-innovation-sbx | prj-152202612488 | 4 | 8 | 4 | 3 | 2 |
| prj-imagefactory-prd | prj-645870428741 | — | — | — | — | — |
| prj-network-prd | prj-20892159146 | — | — | — | — | — |

> `—` : Vertex AI API non activée ou accès insuffisant pour ce projet.

---

## prj-agentic-factory-sbx (`prj-240444336327`)

### us-east5 (Ohio)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |
| claude-sonnet-4-5 | 20250929 |

### us-central1 (Iowa)

| Modèle | Version |
|--------|---------|
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |
| claude-opus-4-1 | 20250805 |
| claude-sonnet-4-5 | 20250929 |
| claude-haiku-4-5 | 20251001 |
| claude-opus-4-5 | 20251101 |
| claude-opus-4-6 | default |
| claude-sonnet-4-6 | default |

### europe-west1 (Belgique)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |
| claude-sonnet-4-5 | 20250929 |

### europe-west4 (Pays-Bas)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |

### asia-southeast1 (Singapour)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-sonnet-4-5 | 20250929 |

---

## prj-ai-innovation-sbx (`prj-152202612488`)

### us-east5 (Ohio)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |
| claude-sonnet-4-5 | 20250929 |

### us-central1 (Iowa)

| Modèle | Version |
|--------|---------|
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |
| claude-opus-4-1 | 20250805 |
| claude-sonnet-4-5 | 20250929 |
| claude-haiku-4-5 | 20251001 |
| claude-opus-4-5 | 20251101 |
| claude-opus-4-6 | default |
| claude-sonnet-4-6 | default |

### europe-west1 (Belgique)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |
| claude-sonnet-4-5 | 20250929 |

### europe-west4 (Pays-Bas)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-opus-4 | 20250514 |
| claude-sonnet-4 | 20250514 |

### asia-southeast1 (Singapour)

| Modèle | Version |
|--------|---------|
| claude-3-opus | 20240229 |
| claude-sonnet-4-5 | 20250929 |

---

## prj-imagefactory-prd (`prj-645870428741`)

Aucun modèle retourné — Vertex AI API probablement non activée sur ce projet ou droits insuffisants.

---

## prj-network-prd (`prj-20892159146`)

Aucun modèle retourné — Vertex AI API probablement non activée sur ce projet ou droits insuffisants.

---

## Notes

- L'API interrogée (`publishers/anthropic/models`) retourne les modèles **disponibles** dans Vertex AI Model Garden pour chaque région, filtrés par les droits du projet utilisé comme quota project.
- Les modèles avec version `default` pointent vers la dernière version stable du modèle.
- **us-central1** dispose du catalogue le plus complet (8 modèles dont les plus récents Claude 4.6).
- Pour utiliser un modèle : `{région}-aiplatform.googleapis.com/v1/projects/{project}/locations/{région}/publishers/anthropic/models/{modèle}@{version}:streamRawPredict`
