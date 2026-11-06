# Lab 5 — Data Model Worksheet & Schema Design Review

- **Author:** Hà Trần Bội Anh (`@htbaax`)
- **Role:** Member 6 (TV6) — Data Privacy & Schema Review Lead
- **Assignment:** Lab 05 Homework H3 Bonus (+1 point)
- **Repository:** `Computational-Thinking-Project/assistant_core_lab`
- **Issue Reference:** Closes #42

---

## 1. Critique the bad schema (`sql/bad_schema.sql`)

Analysis of the initial anti-pattern schema in `sql/bad_schema.sql`:

```sql
CREATE TABLE chats (
    id INTEGER,
    student_name TEXT,          -- real names stored with every message
    student_phone TEXT,
    message TEXT,               -- full raw message, kept forever
    answer TEXT,
    intent TEXT,                -- free text: 'fee', 'Fee', 'FEE', 'tuition'...
    time TEXT,                  -- '5/10/2026 9:03 PM' as text
    feedback TEXT,              -- '1,-1,1' comma-separated list of ratings
    latency TEXT                -- '120ms'
);
```

| # | Problem | Why it hurts | Fix |
|---|---|---|---|
| **1** | **Direct storage of PII** (`student_name`, `student_phone`) | Storing identifiable personal information directly violates the Data Minimization principle (e.g., Vietnam Personal Data Protection Decree 13/2023/ND-CP). If the database is compromised, student identities and contact details are leaked. No assistant feature requires knowing a student's real name or phone number. | Completely remove `student_name` and `student_phone`. To track conversation continuity anonymously, store only a salted cryptographic hash (`session_id`) in a dedicated `chat_session` table. |
| **2** | **Full raw message retention** (`message`) | Raw user queries frequently contain sensitive or confidential data (e.g., student IDs, personal circumstances, credentials, phone numbers). Retaining raw text permanently maximizes data breach impact and wastes disk storage. | Do not persist full query text. Only extract and store structured telemetry required for analytics and service improvements: `intent`, `topic` (handbook rule ID), `resolved` boolean, and `degraded` flag. |
| **3** | **Unnormalized categorical free text** (`intent`) | Storing case-insensitive synonyms (`'fee'`, `'Fee'`, `'FEE'`, `'tuition'`) prevents accurate grouping and reporting. Queries like `GROUP BY intent` or `WHERE intent = 'fee'` will treat these variations as separate categories, producing fragmented and misleading analytics. | Constrain `intent` to a normalized, lowercase enumerated set (`"fee"`, `"office"`, `"rule"`, `"greeting"`, `"unknown"`). Enforce this constraint at the API layer (Pydantic / SQLModel enum) and with database `CHECK` constraints. |
| **4** | **Unstructured locale-dependent timestamp string** (`time`) | Storing timestamps as human-formatted text (`'5/10/2026 9:03 PM'`) breaks chronological sorting (`ORDER BY time` evaluates lexicographically, so `'10/...'` precedes `'5/...'`). It also prevents range filtering (`BETWEEN`, `>`, `<`) and native datetime aggregations (`strftime`, `DATE()`). | Store timestamps using standard UTC ISO-8601 strings or native `TIMESTAMP` / `DATETIME` format (e.g., `created_at: datetime = Field(default_factory=utcnow)` in SQLModel), enabling precise indexing and chronological queries. |
| **5** | **First Normal Form (1NF) violation** (`feedback = '1,-1,1'`) | Storing multiple values as a comma-separated list in a single cell violates 1NF (atomic values). SQL aggregation functions (`AVG`, `SUM`, `COUNT`) cannot operate on delimited strings without complex, error-prone string manipulation. Furthermore, feedback timestamps and individual user comments cannot be tracked. | Normalize the relationship: decompose feedback into a dedicated `feedback` table linked via foreign key to `interaction(request_id)`. Store each rating atomically (`rating: int` with values `-1, 0, 1`), along with an optional `comment` and timestamp. |
| **6** | **Non-numeric metric string with unit** (`latency = '120ms'`) | Storing numbers with text units (`'120ms'`) prevents mathematical and statistical operations. Calling `AVG(latency)` or `SUM(latency)` yields `0` or raises runtime errors, preventing performance monitoring and SLA compliance tracking. | Store latency as a pure floating-point or integer number in milliseconds (`latency_ms: float = 0.0`), allowing direct `AVG(latency_ms)` and `ROUND(..., 1)` calculations. |
| **7** | **Missing Primary Key and uniqueness constraints** (`id INTEGER`) | The column `id` is declared without `PRIMARY KEY` or `NOT NULL`. This permits duplicate IDs, NULL keys, and duplicate rows. Table lookups require an inefficient full table scan ($O(N)$), and other tables cannot safely establish foreign key relationships with this table. | Declare `id: int | None = Field(default=None, primary_key=True)` (in SQLite: `INTEGER PRIMARY KEY AUTOINCREMENT`) and provide indexed unique business keys (e.g., `request_id: str = Field(unique=True, index=True)`). |

---

## 2. Store or not? (Privacy-aware storage matrix)

In compliance with Privacy by Design, GDPR, and Vietnam's Personal Data Protection regulations (Decree 13/2023/ND-CP), data storage must follow the **Data Minimization** rule: store only what is strictly necessary to deliver and improve features.

| Data | Store? | Form (raw / hashed / aggregated / none) | Proposed Retention Policy* | Reason & Behavioral Nuance |
|---|---|---|---|---|
| **raw user message** | **No** | `none` | 0 (ephemeral / RAM only) | User questions can inadvertently contain sensitive personal details (PII), academic transcripts, or credentials. Once answered by `AssistantService`, the raw text is discarded. Operational needs only require categorized intent and handbook topic. |
| **session id** | **Yes** | `hashed in DB` (SHA-256 + salt); `raw in JSON logs` | 30–90 days (proposed)* | Needed to correlate multi-turn dialogs within a single session and measure active session counts. Hashed with a secret server salt before persisting to SQLite (`chat_session.id`). **Nuance:** The raw session ID remains in the in-memory request scope and can be emitted in application JSON logs when logger context formatting is enabled. |
| **intent, latency, topic** | **Yes** | `raw` (structured telemetry) | 1 year (proposed)* | Essential operational metrics for monitoring system responsiveness, identifying knowledge gaps (unresolved topics), and tracking usage patterns over time without exposing user identities. |
| **feedback rating** | **Yes** | `raw` (integer: `-1, 0, 1`) | 1 year (proposed)* | Critical quality metric to measure answer accuracy, student satisfaction, and model degradation over releases. |
| **feedback comment** | **Yes** | `raw text` (stored verbatim, max 500 chars) | 90 days (proposed)* | Qualitative feedback explaining why an answer was unhelpful. Kept optional with a 500-character cap. **Nuance:** Comments are stored verbatim as submitted without automated PII redaction; users could potentially enter personal details in this free-form field (residual PII risk exists). |
| **student name / phone** | **No** | `none` | 0 (never collected) | Direct identifying PII that provides zero functional value to the virtual assistant. Completely omitted from API schemas and database tables. |

> **\*Note on Retention Policy vs. Current Implementation:** The retention periods specified above represent the **proposed data governance lifecycle policy**. In the current v0.5 release, automated TTL deletion or periodic cleanup cron jobs are not yet implemented in the codebase; data persists in SQLite until manual database truncation or migration.

---

## 3. Product questions → fields

Mapping operational product questions to required database entities, columns, and executable SQL query sketches:

| Product question | Fields needed | Table(s) | Query sketch |
|---|---|---|---|
| **Most failed intent?** | `intent`, `resolved` | `interaction` | ```sql SELECT intent, COUNT(*) AS failure_count FROM interaction WHERE resolved = 0 GROUP BY intent ORDER BY failure_count DESC LIMIT 1; ``` |
| **Average response time by intent?** | `intent`, `latency_ms` | `interaction` | ```sql SELECT intent, ROUND(AVG(latency_ms), 1) AS avg_latency_ms, COUNT(*) AS total_requests FROM interaction GROUP BY intent ORDER BY avg_latency_ms DESC; ``` |
| **Top unresolved topics?** | `topic`, `resolved` | `interaction` | ```sql SELECT topic, COUNT(*) AS unresolved_count FROM interaction WHERE resolved = 0 AND topic IS NOT NULL GROUP BY topic ORDER BY unresolved_count DESC LIMIT 5; ``` |
| **Topics with most negative feedback?** | `topic`, `rating` | `interaction` JOIN `feedback` | ```sql SELECT i.topic, COUNT(*) AS thumbs_down_count FROM feedback f JOIN interaction i ON f.request_id = i.request_id WHERE f.rating = -1 AND i.topic IS NOT NULL GROUP BY i.topic ORDER BY thumbs_down_count DESC LIMIT 5; ``` |

---

## 4. Entity-Relationship (ER) Diagram

The normalized schema implemented in `assistant_api/db.py` separates concerns into three distinct entities:

```mermaid
erDiagram
    CHAT_SESSION ||--o{ INTERACTION : initiates
    INTERACTION ||--o{ FEEDBACK : receives

    CHAT_SESSION {
        string id PK "Salted SHA-256 hash"
        string channel "e.g. web"
        datetime created_at "UTC timestamp"
    }

    INTERACTION {
        int id PK "Autoincrement primary key"
        string request_id "Unique 12-char hex request ID"
        string session_id FK "References chat_session.id"
        string intent "Categorized intent"
        string topic "Handbook rule ID"
        boolean resolved "Answered or error"
        boolean degraded "Fallback answer used"
        float latency_ms "Latency in ms"
        datetime created_at "UTC timestamp"
    }

    FEEDBACK {
        int id PK "Autoincrement primary key"
        string request_id FK "References interaction.request_id"
        int rating "Rating minus 1 to 1"
        string comment "Optional user comment"
        datetime created_at "UTC timestamp"
    }
```

### Relational Schema Properties:
1. **1-to-N Cardinality (`CHAT_SESSION` → `INTERACTION`):** A single hashed session can generate multiple interactions over time.
2. **1-to-N Cardinality (`INTERACTION` → `FEEDBACK`):** An interaction generates zero, one, or multiple feedback entries (supporting audit trails or re-ratings).
3. **Foreign Key Integrity:** `interaction.session_id` references `chat_session.id`; `feedback.request_id` references `interaction.request_id`.
4. **Anonymity & Pseudonymity Assessment (Current Implementation vs. Nuances):**
   - **Database Pseudonymity:** No database tables store raw user query messages, student IDs, student names, IP addresses, or phone numbers. Session tokens are pseudonymized via salted SHA-256 hashing before storing in `chat_session.id`.
   - **Logging Exposure Nuance:** While the SQLite database stores only the salted session hash, the original raw `session_id` exists in the in-process request context and can be emitted in application-level JSON logs when logging handlers with context formatting are enabled.
   - **Residual PII Risk in Free-Form Feedback:** The `feedback.comment` column stores user comments verbatim up to 500 characters. Because there is currently no automated PII scrubber/redaction filter applied, users could inadvertently include personal information when submitting feedback.


---

## 5. Privacy & Data Integrity Audit Report (PR #38 Codebase Review)

As part of the TV6 audit responsibilities, the persistence implementation submitted in PR #38 (`feature/assistant-persistence` by `@AI-WFox`) was reviewed against data security requirements:

- [x] **Zero Raw User Message Storage:** Inspected `src/assistant_api/main.py` (`POST /v1/chat`). Confirmed that `req.message` is consumed solely by `service.handle(...)` in RAM and is **never** passed to `repo.record_interaction(...)` or written to `assistant.db`.
- [x] **Salted Session Anonymization:** Inspected `hash_session()` in `src/assistant_api/db.py`. Confirmed session IDs are salted using `Settings.session_salt` and hashed with SHA-256 (`hashlib.sha256((salt + raw).encode()).hexdigest()[:16]`).
- [x] **Orphan Record Prevention:** Inspected `Repository.add_feedback()`. Confirmed an existence check query (`select(Interaction).where(Interaction.request_id == request_id)`) executes prior to inserting feedback. Invalid request IDs return `None` and result in HTTP 404 (`unknown_request_id`), preventing dangling feedback.
- [x] **Admin Authorization Protection:** Inspected `GET /v1/feedback` and `GET /v1/stats/intents`. Confirmed both administrative endpoints require valid `X-API-Key` authentication via `require_admin`.
