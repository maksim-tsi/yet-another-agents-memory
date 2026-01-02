# Phase 5 Readiness Tracker

**Date:** 2026-01-02  
**Purpose:** Consolidated graded tracker for Phase 5 readiness across architecture, implementation depth, testing realism, performance, documentation integrity, and governance. Grading scale: Green (meets bar), Amber (minor gaps), Red (blocking gaps). Use project-specific evidence and improvements drawn from the Phase 5 checklist.

## Grading Legend
- **Green:** Evidence current and sufficient; no action required.  
- **Amber:** Partial or dated evidence; address specified improvement.  
- **Red:** Missing/conflicting evidence; must remediate before Phase 5.

## 1. Architecture & ADR Alignment
| Item | Grade | Evidence | Improvement Action |
| --- | --- | --- | --- |
| Tier responsibilities and flow (L1–L4) | TBD | [docs/ADR/003-four-layers-memory.md](../ADR/003-four-layers-memory.md); [AGENTS.MD](../../AGENTS.MD); [docs/reports/adr-003-architecture-review.md](../reports/adr-003-architecture-review.md) | Ensure diagrams/text reflect current engine code paths and dual-index commitments. |
| CIAR policy compliance | TBD | [docs/ADR/004-ciar-scoring-formula.md](../ADR/004-ciar-scoring-formula.md); [config/ciar_config.yaml](../../config/ciar_config.yaml); [src/memory/ciar_scorer.py](../../src/memory/ciar_scorer.py) | Verify decay/recency parameters match ADR defaults per domain; document rationale in config comments. |
| Lifecycle engines coverage (promotion → consolidation → distillation) | TBD | [src/memory/engines/promotion_engine.py](../../src/memory/engines/promotion_engine.py); [consolidation_engine.py](../../src/memory/engines/consolidation_engine.py); [distillation_engine.py](../../src/memory/engines/distillation_engine.py); [docs/reports/adr-003-architecture-review.md](../reports/adr-003-architecture-review.md) | Document retry/circuit-breaker thresholds; test degradation paths. |
| Dual-index guarantees (L3 Qdrant + Neo4j; L4 Typesense) | TBD | [src/memory/tiers/episodic_memory_tier.py](../../src/memory/tiers/episodic_memory_tier.py); [semantic_memory_tier.py](../../src/memory/tiers/semantic_memory_tier.py) | Specify divergence detection/repair runbooks; add idempotent write checks. |
| Operating vs persistent layer boundaries | TBD | [src/memory/tiers/active_context_tier.py](../../src/memory/tiers/active_context_tier.py); [working_memory_tier.py](../../src/memory/tiers/working_memory_tier.py) | Confirm hot-path TTL/windowing constraints (10–20 turns, 24h TTL) are enforced and logged. |

## 2. Implementation Depth
| Item | Grade | Evidence | Improvement Action |
| --- | --- | --- | --- |
| Tier behavior completeness | TBD | [src/memory/tiers/base_tier.py](../../src/memory/tiers/base_tier.py) + concrete tiers | Add edge-case handling (empty windows, backpressure) and per-method metrics. |
| Data contracts (Fact, Episode, KnowledgeDocument) | TBD | [src/memory/models.py](../../src/memory/models.py) | Validate provenance across L2→L4; align required/optional fields with engine assumptions. |
| LLM orchestration and fallbacks | TBD | [src/utils/llm_client.py](../../src/utils/llm_client.py); [docs/LLM_PROVIDER_TESTS.md](../LLM_PROVIDER_TESTS.md); [docs/LLM_PROVIDER_TEST_RESULTS.md](../LLM_PROVIDER_TEST_RESULTS.md) | Document routing by task; ensure GOOGLE_API_KEY usage is uniform. |
| Storage adapters and metrics | TBD | [src/storage/](../../src/storage); [docs/metrics_usage.md](../metrics_usage.md) | Confirm metrics on errors/timeouts; document reconnection/backoff and pool sizing. |

## 3. Testing Realism & Coverage
| Item | Grade | Evidence | Improvement Action |
| --- | --- | --- | --- |
| Unit vs integration breadth | TBD | [tests/memory/](../../tests/memory); [tests/storage/](../../tests/storage); [tests/utils/](../../tests/utils); [tests/integration/](../../tests/integration) | Map each lifecycle path to an integration test; add failure-injection (backend unavailable, partial writes). |
| Mocks vs real backends | TBD | Skip markers; [tests/integration/test_llmclient_real.py](../../tests/integration/test_llmclient_real.py); [tests/utils/test_gemini_structured_output.py](../../tests/utils/test_gemini_structured_output.py) | Prioritize real-backend runs for critical paths under feature flags; keep mocks for isolation only. |
| Coverage posture | TBD | [htmlcov/status.json](../../htmlcov/status.json); [docs/LLM_PROVIDER_TEST_RESULTS.md](../LLM_PROVIDER_TEST_RESULTS.md) | Increase coverage on lifecycle error branches, divergence repair, retry/circuit-breaker logic. |
| Acceptance and performance tests | TBD | [benchmarks/README.md](../../benchmarks/README.md); [benchmarks/configs/](../../benchmarks/configs) | Enforce <2s p95 lifecycle with real backends; automate reporting. |

## 4. Performance & Benchmarking
| Item | Grade | Evidence | Improvement Action |
| --- | --- | --- | --- |
| Latency/throughput SLAs | TBD | [docs/reports/adr-003-architecture-review.md](../reports/adr-003-architecture-review.md); [docs/metrics_usage.md](../metrics_usage.md) | Run lifecycle benchmarks on Redis/Postgres/Qdrant/Neo4j/Typesense; capture p95/p99 and queue depth. |
| Resource and configuration tuning | TBD | Pooling/batching in [src/storage/](../../src/storage); [config/](../../config) | Document recommended pool sizes, batch sizes, load-shedding/backpressure; add tests for defaults. |
| GoodAI LTM benchmark readiness | TBD | [docs/uc-01.md](../uc-01.md); [docs/research/](../research) | Prepare reproducible scripts and baselines (RAG vs full-context) with fixed seeds and logging. |

## 5. Documentation & Status Integrity
| Item | Grade | Evidence | Improvement Action |
| --- | --- | --- | --- |
| Status currency | TBD | [DEVLOG.md](../../DEVLOG.md); [docs/plan/](../plan); [docs/reports/adr-003-architecture-review.md](../reports/adr-003-architecture-review.md) | Reconcile outdated statements; record Phase 4 closure and pending gates. |
| Operational runbooks | TBD | [docs/environment-guide.md](../environment-guide.md); [docs/metrics_usage.md](../metrics_usage.md) | Add runbooks for lifecycle failures, divergence repair, LLM fallback behavior. |
| Config-to-ADR alignment | TBD | [config/ciar_config.yaml](../../config/ciar_config.yaml); [docs/ADR/004-ciar-scoring-formula.md](../ADR/004-ciar-scoring-formula.md) | Capture domain-specific CIAR overrides and rationale. |
| Risk register and lessons | TBD | [docs/lessons-learned.md](../lessons-learned.md) | Log Phase 4 incidents with mitigations and code links. |

## 6. Governance & Safety
| Item | Grade | Evidence | Improvement Action |
| --- | --- | --- | --- |
| Error handling and circuit breakers | TBD | [src/memory/engines/](../../src/memory/engines); [src/storage/](../../src/storage) | Confirm thresholds/retry budgets are implemented, documented, and tested. |
| Provenance and auditability | TBD | [src/memory/models.py](../../src/memory/models.py); engine writes | Add tests ensuring provenance survives L2→L4 promotions and reconciliations. |
| Data retention and TTLs | TBD | L1/L2 logic and configs | Validate TTL enforcement and retention policies match ADR and compliance notes; expose metrics on expirations. |

## Usage
- Update Grade per item (Green/Amber/Red). Keep concise notes in Improvement Action.  
- Link to specific code lines or test outputs when grading.  
- Re-run grading after each validation cycle or major change to engines, tiers, or adapters.
- **Recommended invocations:**
	- Fast path (lint + unit/mocked): `./scripts/grade_phase5_readiness.sh --mode fast`
	- Full path (adds integration, real LLM if env present, benchmarks opt-in): `./scripts/grade_phase5_readiness.sh --mode full --summary-out /tmp/phase5-readiness.json`
	- Skip real LLM/provider checks even with `GOOGLE_API_KEY` set: add `--skip-llm`
- **Summary artifact:** If `--summary-out` is provided, the Python emitter writes the JSON summary to that path; otherwise it prints to stdout. Coverage is pulled from `htmlcov/status.json` when present.