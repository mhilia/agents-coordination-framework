# AI Agents Communication Stack — Architecture & Conception

> Document de conception évolutif — à affiner au fil des échanges.

---

## 1. Contexte & Objectifs

### Cas d'usage cible — Vessel Delay Alert (POC)

Quand un navire CMA CGM accumule un retard significatif (tempête, congestion portuaire, panne), le système :
1. **Détecte** l'anomalie en temps réel à partir des positions AIS
2. **Identifie** les bookings et clients impactés
3. **Notifie** automatiquement les clients avec une estimation de retard

### Objectifs techniques
- Orchestrer des agents IA spécialisés capables de collaborer de façon autonome
- Démontrer la complémentarité **Kafka (async)** pour l'ingestion temps réel et **A2A (sync)** pour la coordination inter-agents
- Traiter des flux de données en temps réel avec **Flink**
- Fournir aux agents un accès unifié aux outils via **MCP**

---

## 2. Stack Technologique

| Technologie | Rôle dans le système |
|---|---|
| **A2A** (Agent-to-Agent Protocol) | Communication synchrone entre agents — discovery, délégation de tâches, notifications push |
| **MCP** (Model Context Protocol) | Interface standardisée agents ↔ outils/données (BDD, APIs, Kafka, etc.) |
| **Kafka Confluent Cloud** | Bus d'événements asynchrone — ingestion de données, files de messages inter-agents |
| **Flink Confluent** | Traitement de flux en temps réel — enrichissement, agrégation, routage, CEP |
| **Claude API** | Moteur LLM des agents (Sonnet/Opus selon complexité de la tâche) |

### A2A — Principes clés
- Chaque agent expose un **Agent Card** (JSON, discovery via `/.well-known/agent.json`)
- Communication via **JSON-RPC over HTTP**
- Support natif du mode streaming (SSE) et des tâches longues
- Sécurité : authentification OAuth2 / API key entre agents

### MCP — Principes clés
- Chaque agent dispose d'un client MCP connecté à des **MCP Servers**
- Les servers exposent : **Tools** (actions), **Resources** (données), **Prompts** (templates)
- Transport : stdio (local) ou SSE/HTTP (remote)

---

## 3. Architecture Proposée — POC Vessel Delay Alert

```
  AISStream.io (WebSocket)
         │
         ▼
  ┌─────────────────┐
  │   AIS Producer  │  ais-producer/producer.py
  │   (Python)      │  filtre MMSI CMA CGM (~600 navires)
  └────────┬────────┘
           │ produce
           ▼
┌──────────────────────────────────────────────────────┐
│               Kafka Confluent Cloud                   │
│                                                       │
│  topic: ais-positions      ◄── positions brutes       │
│  topic: vessel-delays      ◄── retards détectés       │
│  topic: notifications-sent ◄── audit notifications    │
└──────────┬──────────────────────────────┬─────────────┘
           │                              │
           ▼                              │
┌──────────────────────┐                 │
│   Flink Confluent    │                 │
│                      │                 │
│  Fenêtre glissante   │                 │
│  2h sur ais-positions│                 │
│  vitesse moy < seuil │                 │
│  ET écart ETA > 4h   │                 │
│         │            │                 │
│         ▼            │                 │
│  → vessel-delays     │                 │
└──────────────────────┘                 │
                                         │
┌────────────────────────────────────────▼─────────────┐
│                   COUCHE AGENTS                       │
│                                                       │
│  ┌────────────────────────────────────────────────┐  │
│  │          Delay Monitor Agent                   │  │
│  │  - consomme vessel-delays (via Kafka MCP)      │  │
│  │  - modèle : Claude Haiku (détection simple)    │  │
│  └──────────────────────┬─────────────────────────┘  │
│                         │ A2A (sync)                  │
│                         ▼                             │
│  ┌────────────────────────────────────────────────┐  │
│  │          Booking Analyzer Agent                │  │
│  │  - reçoit le MMSI + retard estimé              │  │
│  │  - interroge la BDD bookings (via DB MCP)      │  │
│  │  - retourne la liste des clients impactés      │  │
│  │  - modèle : Claude Sonnet                      │  │
│  └──────────────────────┬─────────────────────────┘  │
│                         │ A2A (sync)                  │
│                         ▼                             │
│  ┌────────────────────────────────────────────────┐  │
│  │          Customer Notifier Agent               │  │
│  │  - reçoit liste clients + contexte retard      │  │
│  │  - rédige notification personnalisée (LLM)     │  │
│  │  - envoie via API notif (via API MCP)          │  │
│  │  - publie sur notifications-sent (Kafka MCP)   │  │
│  │  - modèle : Claude Sonnet                      │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘
           │ MCP
           ▼
┌──────────────────────────────────────────────────────┐
│                   COUCHE MCP SERVERS                  │
│                                                       │
│  ┌─────────────────┐  ┌───────────────┐  ┌─────────┐ │
│  │  Kafka MCP      │  │  Database MCP │  │ API MCP │ │
│  │  consume/produce│  │  bookings DB  │  │ notifs  │ │
│  └─────────────────┘  └───────────────┘  └─────────┘ │
└──────────────────────────────────────────────────────┘
```

### Pourquoi hybride — la séparation est intentionnelle

| Pattern | Où | Pourquoi |
|---|---|---|
| **Kafka (async)** | AIS → Flink → Delay Monitor | Volume élevé, découplage, l'agent n'a pas à polluer son contexte avec chaque position AIS |
| **A2A (sync)** | Delay Monitor → Booking Analyzer → Notifier | La notification DOIT référencer des données de booking exactes : cohérence critique, flux séquentiel |

---

## 4. Composants Détaillés

### 4.1 Source de données AIS

**Fichier :** `ais-producer/producer.py`

| Paramètre | Valeur |
|---|---|
| Source | AISStream.io (WebSocket temps réel) |
| Filtre | MMSI CMA CGM (~600 navires) |
| Output | Kafka topic `ais-positions` |
| Clé Kafka | MMSI (partitionnement par navire) |
| Format | JSON |

```json
{
  "mmsi": "215301000",
  "vessel_name": "CMA CGM MARCO POLO",
  "lat": 43.2965,
  "lon": 5.3811,
  "speed_knots": 14.2,
  "course": 187.0,
  "heading": 185,
  "nav_status": "Under way using engine",
  "timestamp": "2026-04-09T10:32:00Z",
  "destination": "FRMRS"
}
```

### 4.2 Agents

| Agent | Trigger | MCP Tools | Modèle Claude | A2A |
|---|---|---|---|---|
| **Delay Monitor** | Consomme `vessel-delays` (Kafka) | `kafka_consume` | Haiku | Appelant |
| **Booking Analyzer** | Appelé via A2A | `db_query` (bookings) | Sonnet | Appelé / Appelant |
| **Customer Notifier** | Appelé via A2A | `db_query` (CRM), `send_notification`, `kafka_produce` | Sonnet | Appelé |

#### Agent Cards A2A (résumé)

```json
// Booking Analyzer — /.well-known/agent.json
{
  "name": "Booking Analyzer",
  "description": "Finds all bookings and customers impacted by a vessel delay",
  "url": "http://booking-analyzer:8001",
  "skills": [{
    "id": "analyze_delay_impact",
    "name": "Analyze Delay Impact",
    "inputModes": ["application/json"],
    "outputModes": ["application/json"]
  }]
}
```

### 4.3 Topics Kafka

| Topic | Producteur | Consommateur | Description |
|---|---|---|---|
| `ais-positions` | AIS Producer (Python) | Flink | Positions brutes CMA CGM |
| `vessel-delays` | Flink | Delay Monitor Agent | Navires en retard détectés |
| `notifications-sent` | Customer Notifier Agent | Monitoring / audit | Log des notifications envoyées |

### 4.4 Job Flink (SQL)

```sql
-- Détection de retard : fenêtre glissante 2h
-- Déclenche si vitesse moyenne < 3 kn ET écart ETA > 4h

INSERT INTO vessel_delays
SELECT
    mmsi,
    vessel_name,
    AVG(speed_knots)          AS avg_speed,
    LAST_VALUE(lat)           AS last_lat,
    LAST_VALUE(lon)           AS last_lon,
    LAST_VALUE(destination)   AS destination,
    LAST_VALUE(timestamp)     AS last_seen,
    CURRENT_TIMESTAMP         AS detected_at
FROM ais_positions
GROUP BY
    mmsi,
    vessel_name,
    HOP(event_time, INTERVAL '10' MINUTE, INTERVAL '2' HOUR)
HAVING AVG(speed_knots) < 3.0;
```

> Note : la comparaison ETA vs ETA attendue nécessite un JOIN avec une table de référence des voyages planifiés (à ajouter en v2).

### 4.5 MCP Servers

| Server | Transport | Tools exposés |
|---|---|---|
| `kafka-mcp-server` | HTTP/SSE | `kafka_consume(topic, group_id)`, `kafka_produce(topic, message)` |
| `database-mcp-server` | HTTP/SSE | `db_query(sql)`, `db_get_bookings_by_vessel(mmsi)` |
| `api-mcp-server` | HTTP/SSE | `send_notification(customer_id, channel, message)` |

---

## 5. Flux de Données — POC End-to-End

```
1. AISStream.io       → positions AIS en continu (WebSocket)
2. AIS Producer       → publie sur ais-positions (Kafka)
3. Flink              → fenêtre 2h, détecte vitesse < 3kn
4. Flink              → publie sur vessel-delays (Kafka)
                              │
                              ▼ (async — Kafka)
5. Delay Monitor Agent  consomme vessel-delays via Kafka MCP
   → analyse le contexte du retard avec Claude Haiku
   → appelle Booking Analyzer via A2A
                              │
                              ▼ (sync — A2A)
6. Booking Analyzer Agent reçoit {mmsi, delay_hours}
   → interroge la BDD bookings via DB MCP
   → retourne [{customer_id, booking_ref, cargo_type, ...}]
   → répond à Delay Monitor via A2A
                              │
                              ▼ (sync — A2A)
7. Delay Monitor Agent  appelle Customer Notifier via A2A
   avec {vessel_name, delay_hours, impacted_customers[]}

8. Customer Notifier Agent
   → enrichit avec données CRM via DB MCP
   → rédige notification personnalisée par client (Claude Sonnet)
   → envoie via API MCP (email / SMS / portail client)
   → publie confirmation sur notifications-sent (Kafka MCP)
```

---

## 6. Infrastructure & Déploiement

```
<!-- À définir -->
```

| Composant | Option envisagée |
|---|---|
| Agents runtime | Docker / Cloud Run / GKE |
| MCP Servers | Même runtime que les agents ou microservices dédiés |
| Kafka | Confluent Cloud (managed) |
| Flink | Confluent Cloud for Flink (managed) |
| Registry A2A | Service discovery dédié ou fichiers statiques |
| Observabilité | OpenTelemetry → Grafana / Confluent Metrics |

---

## 7. Sécurité

- **A2A** : OAuth2 entre agents, mTLS optionnel
- **Kafka** : SASL/OAUTHBEARER, ACLs par topic et par agent (service account dédié)
- **MCP** : API Key ou OAuth2 selon le server
- **Secrets** : Google Secret Manager / Vault

---

## 8. Questions Ouvertes & Décisions

| # | Question | Statut |
|---|---|---|
| Q1 | Quel est le cas d'usage métier principal ? | **À définir** |
| Q2 | Nombre et types d'agents spécialisés ? | **À définir** |
| Q3 | Volume et fréquence des événements Kafka estimés ? | **À définir** |
| Q4 | Flink : SQL ou DataStream API ? | **À définir** |
| Q5 | Runtime agents : conteneurs stateless ou agents persistants ? | **À définir** |
| Q6 | Gestion de l'état des agents (stateful vs stateless) ? | **À définir** |
| Q7 | Stratégie de retry / DLQ pour les tâches d'agents ? | **À définir** |
| Q8 | API Gateway devant les agents A2A (auth centralisée) ? | **À définir** |

---

## 9. Prochaines Étapes

### Fait
- [x] Définir le cas d'usage POC (Vessel Delay Alert)
- [x] Valider l'architecture hybride Kafka + A2A
- [x] AIS Producer (ais-producer/producer.py)

### À faire
- [ ] Créer le topic Kafka `ais-positions` sur Confluent Cloud
- [ ] Écrire et déployer le job Flink SQL (vessel-delays)
- [ ] Implémenter les 3 MCP Servers (Kafka, DB, API)
- [ ] Implémenter les 3 agents (Delay Monitor, Booking Analyzer, Customer Notifier)
- [ ] Définir les Agent Cards A2A complètes
- [ ] Choisir le runtime agents (Cloud Run recommandé pour la POC)
- [ ] Tests end-to-end avec données AIS réelles

---

*Document vivant — dernière mise à jour : 2026-04-09*
