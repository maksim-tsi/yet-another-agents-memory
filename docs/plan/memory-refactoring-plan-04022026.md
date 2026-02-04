Plan: Generic BaseTier Refactoring (Phase 2E) — Updated
This refactoring converts the abstract BaseTier class to use Python Generics (BaseTier[T]), aligning return types with Pydantic domain models. The two research reports provide comprehensive guidance and resolve all open architectural questions.

TL;DR
Refactor BaseTier to BaseTier[T] where T is bound to BaseModel. Create missing TurnData model for L1. The research confirms: (1) 3/4 tiers already return Pydantic objects, (2) performance overhead is negligible (<0.1ms), (3) store() should also accept T not just dict. Estimated ~250-330 lines affected across ~10 files.

Answers to Previously Raised Considerations
Consideration	Research Answer	Source
L1 retrieve() returns list[dict]	Create TurnData model. L1 should follow same pattern. Report proposes TurnData(BaseModel) with session_id, turn_id, role, content, timestamp, metadata	refactoring_memory_tiers_2_type_safe.md
Covariance handling for mypy	Not explicitly addressed, but report recommends Pydantic V2's mypy plugin. Use invariant T first; Pydantic handles covariance internally.	Section 2.1
Should store() accept T instead of dict?	Yes — proposed signature is store(self, data: T) -> str. This makes API fully symmetric and aligns with "Reasoning-First" schema pattern.	Section 3.1 Proposed Generic Definition
Steps
Create TurnData Pydantic model in models.py

Add TurnData(BaseModel) with fields: turn_id, session_id, role: Literal["user", "assistant", "system"], content, timestamp, metadata
This fills the L1 model gap identified in Section 5.1
Refactor base_tier.py to Generic

Add T = TypeVar("T", bound=BaseModel) and make BaseTier(ABC, Generic[T])
Update store(data: T) -> str (accept model, not dict)
Update retrieve(identifier: str) -> T | None
Update query(filters, limit, **kwargs) -> list[T]
Update tiers bottom-up (L4 → L3 → L2 → L1) per Section 5.2 rollout strategy

src/memory/tiers/l4_semantic_memory.py: BaseTier[KnowledgeDocument] (lowest volume, start here)
src/memory/tiers/l3_episodic_memory.py: BaseTier[Episode] (dual-index merge logic needs attention)
src/memory/tiers/l2_working_memory.py: BaseTier[Fact] (already returns Fact)
src/memory/tiers/l1_active_context.py: BaseTier[TurnData] (highest performance risk, do last)
Update PromotionEngine in promotion_engine.py

Change dict access (turn['content']) to attribute access (turn.content)
Other engines (Consolidation, Distillation) already use model attributes
Refactor src/memory/unified_tools.py (if exists) or tool implementations

Use model attributes instead of manual dict key extraction
Simplifies code by removing parsing layer
Update tests incrementally after each tier

L1 tests need most changes (dict → TurnData attributes)
L2-L4 tests already use model attributes
Benchmark L1 after refactor to ensure latency stays <5ms

If needed, use model_construct() for trusted data to bypass validation
Further Considerations (Resolved)
L1 retrieve() returns list[dict] → Resolved: Create TurnData model per Section 5.1

Covariance for mypy → Resolved: Use invariant T with Pydantic V2 mypy plugin; test incrementally

Should store() accept T? → Resolved: Yes, per Section 3.1 proposed signature

Risk Mitigation (from Table 2)
Component	Risk	Mitigation
L1 ActiveContext	Medium (Performance)	Benchmark after; use model_construct() if needed
L3 Episodic	High (Qdrant/Neo4j merge)	Careful review of dual-index merge logic
Tests (574)	Low (Tedious)	Automate with search-replace for common patterns
