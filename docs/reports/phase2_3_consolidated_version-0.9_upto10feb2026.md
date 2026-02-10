# Phase 2-3 Consolidated (version-0.9, upto10feb2026)

Consolidated Phase 2 action plan and Phase 3 prerequisite completion notes.
Sections preserve original content and date markers.

Sources:
- phase-2-action-plan.md
- phase-3-prereq-complete.md

---
## Source: phase-2-action-plan.md

# Phase 2 Implementation Action Plan

**Created**: November 2, 2025  
**Target**: Complete ADR-003 Memory Tiers & Lifecycle Engines  
**Current Status**: Phase 1 Complete (30%) | Phase 2 Not Started (0%)  
**Estimated Duration**: 6-8 weeks

---

## Overview

This plan breaks down Phase 2 (Memory Intelligence) into concrete, actionable sprints with clear deliverables and acceptance criteria.

**Goal**: Transform storage adapters into an intelligent four-tier memory system with autonomous lifecycle engines.

---

## Phase 2A: Memory Tier Classes (Weeks 1-3)

### Week 1: L1 Active Context Tier

**Deliverable**: Working L1 tier with turn windowing

**Tasks**:
1. Create `src/memory/tiers/base_tier.py`
   - Abstract base class for all tiers
   - Common interface (store, retrieve, query)
   - Health check and metrics integration

2. Create `src/memory/tiers/active_context_tier.py`
   - Wrap Redis and PostgreSQL adapters
   - Implement turn windowing (keep 10-20 recent)
   - TTL management (24 hours)
   - Session-based isolation

3. Add tests: `tests/memory/test_active_context_tier.py`
   - Turn storage and retrieval
   - Window size enforcement
   - TTL expiration
   - Session isolation

**Acceptance Criteria**:
- [ ] Tier stores conversation turns
- [ ] Automatically limits to N recent turns
- [ ] TTL expires old sessions
- [ ] 80%+ test coverage
- [ ] Performance: <5ms average latency

---

### Week 2: L2 Working Memory Tier

**Deliverable**: Working L2 tier with fact storage

**Tasks**:
1. Update PostgreSQL schema
   ```sql
   -- migrations/002_working_memory_ciar.sql
   ALTER TABLE working_memory 
   ADD COLUMN ciar_score FLOAT DEFAULT 0.0,
   ADD COLUMN certainty FLOAT DEFAULT 0.0,
   ADD COLUMN impact FLOAT DEFAULT 0.0,
   ADD COLUMN age_decay FLOAT DEFAULT 1.0,
   ADD COLUMN recency_boost FLOAT DEFAULT 1.0,
   ADD COLUMN source_uri VARCHAR(500),
   ADD COLUMN last_accessed TIMESTAMP DEFAULT NOW(),
   ADD COLUMN access_count INTEGER DEFAULT 0;
   
   CREATE INDEX idx_ciar_score ON working_memory(ciar_score DESC);
   CREATE INDEX idx_session_ciar ON working_memory(session_id, ciar_score DESC);
   ```

2. Create `src/memory/tiers/working_memory_tier.py`
   - Wrap PostgreSQL adapter
   - Store facts with CIAR metadata
   - Query by session and CIAR threshold
   - Track access counts
   - Update recency on access

3. Add tests: `tests/memory/test_working_memory_tier.py`
   - Fact storage with CIAR data
   - Query by threshold
   - Recency tracking
   - Access count updates

**Acceptance Criteria**:
- [ ] Stores facts with CIAR metadata
- [ ] Queries by CIAR threshold
- [ ] Tracks access patterns
- [ ] Schema migration runs successfully
- [ ] 80%+ test coverage

---

### Week 3: L3 & L4 Tiers

**Deliverable**: L3 episodic and L4 semantic tiers

**L3: Episodic Memory Tier**

1. Update Neo4j schema for bi-temporal model
   ```cypher
   // migrations/003_bitemporal_graph.cypher
   CREATE CONSTRAINT fact_valid_from IF NOT EXISTS
   FOR ()-[r:RELATES_TO]-()
   REQUIRE r.factValidFrom IS NOT NULL;
   
   CREATE INDEX entity_temporal IF NOT EXISTS
   FOR (n:Entity)
   ON (n.factValidFrom, n.factValidTo);
   ```

2. Create `src/memory/tiers/episodic_memory_tier.py`
   - Coordinate Qdrant + Neo4j adapters
   - Dual-index episodes (vector + graph)
   - Store bi-temporal properties
   - Link Qdrant payloads to Neo4j nodes

3. Add tests: `tests/memory/test_episodic_memory_tier.py`

**L4: Semantic Memory Tier**

1. Update Typesense schema
   ```typescript
   // Knowledge document schema
   {
     "name": "knowledge_base",
     "fields": [
       {"name": "knowledge_id", "type": "string"},
       {"name": "content", "type": "string"},
       {"name": "confidence_score", "type": "float"},
       {"name": "source_episodes", "type": "string[]"},
       {"name": "provenance_links", "type": "string[]"}
     ]
   }
   ```

2. Create `src/memory/tiers/semantic_memory_tier.py`
   - Wrap Typesense adapter
   - Store knowledge documents
   - Track provenance to L3 episodes

3. Add tests: `tests/memory/test_semantic_memory_tier.py`

**Acceptance Criteria**:
- [ ] L3 dual-indexes episodes
- [ ] Bi-temporal properties working
- [ ] L4 stores knowledge with provenance
- [ ] Tests passing
- [ ] 80%+ coverage

---

## Phase 2B: CIAR Scoring & Promotion (Weeks 4-5)

### Week 4: CIAR Scoring System

**Deliverable**: Working CIAR calculator

**Tasks**:
1. Create `src/memory/ciar_scorer.py`
   ```python
   class CIARScorer:
       def calculate(self, fact: Dict) -> float:
           """Calculate CIAR score"""
           certainty = self._calculate_certainty(fact)
           impact = self._calculate_impact(fact)
           age_decay = self._calculate_age_decay(fact)
           recency_boost = self._calculate_recency(fact)
           return (certainty * impact) * age_decay * recency_boost
       
       def _calculate_certainty(self, fact: Dict) -> float:
           """Extract from LLM metadata or use heuristics"""
           
       def _calculate_impact(self, fact: Dict) -> float:
           """Classify: preferences (high) vs mentions (low)"""
           
       def _calculate_age_decay(self, fact: Dict) -> float:
           """Exponential decay: exp(-lambda * age_days)"""
           
       def _calculate_recency_boost(self, fact: Dict) -> float:
           """Boost based on access count"""
   ```

2. Add configuration
   ```python
   # config/ciar_config.yaml
   ciar:
     threshold: 0.6
     age_decay_lambda: 0.1
     recency_boost_factor: 0.05
     certainty_default: 0.7
     impact_weights:
       preference: 0.9
       constraint: 0.8
       entity: 0.6
       mention: 0.3
   ```

3. Add tests: `tests/memory/test_ciar_scorer.py`
   - Score calculation
   - Component calculations
   - Threshold checks
   - Edge cases

**Acceptance Criteria**:
- [ ] Calculates all CIAR components
- [ ] Formula: `(C × I) × AD × RB`
- [ ] Configurable parameters
- [ ] 100% test coverage
- [ ] Documented with examples

---

### Week 5: Fact Extraction & Promotion

**Deliverable**: L1→L2 promotion working

**Tasks**:
1. Create `src/memory/fact_extractor.py`
   ```python
   class FactExtractor:
       def __init__(self, llm_client, circuit_breaker):
           self.llm = llm_client
           self.circuit_breaker = circuit_breaker
       
       async def extract_facts(self, turns: List[Dict]) -> List[Dict]:
           """Extract facts from conversation turns"""
           try:
               if self.circuit_breaker.is_open():
                   return await self._rule_based_extraction(turns)
               
               facts = await self._llm_extraction(turns)
               self.circuit_breaker.record_success()
               return facts
           
           except Exception as e:
               self.circuit_breaker.record_failure()
               return await self._rule_based_extraction(turns)
       
       async def _llm_extraction(self, turns: List[Dict]) -> List[Dict]:
           """Use LLM to extract structured facts"""
       
       async def _rule_based_extraction(self, turns: List[Dict]) -> List[Dict]:
           """Fallback: simple regex/NER extraction"""
   ```

2. Create `src/memory/engines/circuit_breaker.py`
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_count = 0
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.state = "closed"  # closed, open, half_open
           self.last_failure_time = None
       
       def is_open(self) -> bool:
           """Check if circuit is open (failures exceeded)"""
       
       def record_success(self):
           """Reset failure count on success"""
       
       def record_failure(self):
           """Increment failures, open circuit if threshold hit"""
   ```

3. Create `src/memory/engines/promotion_engine.py`
   ```python
   class PromotionEngine:
       def __init__(self, l1_tier, l2_tier, extractor, scorer):
           self.l1 = l1_tier
           self.l2 = l2_tier
           self.extractor = extractor
           self.scorer = scorer
       
       async def run(self):
           """Background task: promote L1→L2"""
           while True:
               await self._process_sessions()
               await asyncio.sleep(60)  # Run every minute
       
       async def _process_sessions(self):
           """Process all active sessions"""
           sessions = await self.l1.get_active_sessions()
           
           for session_id in sessions:
               turns = await self.l1.get_recent_turns(session_id, limit=5)
               facts = await self.extractor.extract_facts(turns)
               
               for fact in facts:
                   ciar_score = self.scorer.calculate(fact)
                   
                   if ciar_score > 0.6:  # Threshold
                       await self.l2.store_fact({
                           **fact,
                           'ciar_score': ciar_score,
                           'session_id': session_id
                       })
   ```

4. Add tests:
   - `tests/memory/test_fact_extractor.py`
   - `tests/memory/test_circuit_breaker.py`
   - `tests/memory/test_promotion_engine.py`

**Acceptance Criteria**:
- [ ] Extracts facts from turns
- [ ] Calculates CIAR scores
- [ ] Promotes if score > threshold
- [ ] Circuit breaker works
- [ ] Runs asynchronously
- [ ] 80%+ coverage

---

## Phase 2C: Consolidation Engine (Weeks 6-8)

### Week 6: Episode Clustering

**Deliverable**: Time-windowed fact clustering

**Tasks**:
1. Create `src/memory/episode_consolidator.py`
   ```python
   class EpisodeConsolidator:
       def __init__(self, l2_tier, l3_tier, llm_client):
           self.l2 = l2_tier
           self.l3 = l3_tier
           self.llm = llm_client
       
       async def cluster_facts(
           self, 
           session_id: str,
           time_window_hours: int = 24
       ) -> List[List[Dict]]:
           """Cluster facts by time and semantic similarity"""
           facts = await self.l2.get_facts_in_window(
               session_id, 
               hours=time_window_hours
           )
           
           # Time-based clustering
           clusters = self._cluster_by_time(facts, gap_minutes=60)
           
           # Optional: Further cluster by topic
           clusters = self._refine_by_topic(clusters)
           
           return clusters
       
       def _cluster_by_time(self, facts, gap_minutes):
           """Group facts with <N minute gaps"""
       
       def _refine_by_topic(self, clusters):
           """Optional: split large clusters by topic"""
   ```

2. Add tests: `tests/memory/test_episode_consolidator.py`

**Acceptance Criteria**:
- [ ] Clusters facts by time windows
- [ ] Handles gap-based splitting
- [ ] Configurable parameters
- [ ] Tests passing

---

### Week 7: Episode Summarization & Dual Indexing

**Deliverable**: LLM-based episode summaries + dual storage

**Tasks**:
1. Add summarization to `EpisodeConsolidator`
   ```python
   async def summarize_cluster(self, cluster: List[Dict]) -> str:
       """Generate narrative summary of fact cluster"""
       prompt = f"""
       Summarize the following facts into a coherent narrative:
       
       Facts:
       {self._format_facts(cluster)}
       
       Generate a concise summary that captures the key information.
       """
       
       summary = await self.llm.generate(prompt)
       return summary
   ```

2. Add dual indexing
   ```python
   async def store_episode(
       self, 
       cluster: List[Dict],
       summary: str,
       session_id: str
   ) -> Dict:
       """Store episode in both Qdrant and Neo4j"""
       episode_id = f"ep_{uuid.uuid4().hex}"
       
       # 1. Create Neo4j event node
       neo4j_node_id = await self.l3.neo4j.create_event_node({
           'episode_id': episode_id,
           'summary': summary,
           'factValidFrom': cluster[0]['timestamp'],
           'factValidTo': cluster[-1]['timestamp'],
           'sourceType': 'consolidation'
       })
       
       # 2. Store in Qdrant with Neo4j link
       await self.l3.qdrant.store({
           'content': summary,
           'metadata': {
               'episode_id': episode_id,
               'neo4j_node_id': neo4j_node_id,
               'source_facts': [f['id'] for f in cluster],
               'session_id': session_id
           }
       })
       
       return {'episode_id': episode_id, 'neo4j_node_id': neo4j_node_id}
   ```

3. Add tests

**Acceptance Criteria**:
- [ ] Generates episode summaries
- [ ] Stores in both Qdrant and Neo4j
- [ ] Links maintained
- [ ] Bi-temporal properties set
- [ ] Tests passing

---

### Week 8: Consolidation Engine

**Deliverable**: Asynchronous L2→L3 consolidation

**Tasks**:
1. Create `src/memory/engines/consolidation_engine.py`
   ```python
   class ConsolidationEngine:
       def __init__(self, consolidator, config):
           self.consolidator = consolidator
           self.config = config
       
       async def run(self):
           """Background task: consolidate L2→L3"""
           while True:
               await self._consolidate_sessions()
               await asyncio.sleep(3600)  # Hourly
       
       async def _consolidate_sessions(self):
           """Process all sessions needing consolidation"""
           sessions = await self._get_sessions_needing_consolidation()
           
           for session_id in sessions:
               try:
                   clusters = await self.consolidator.cluster_facts(session_id)
                   
                   for cluster in clusters:
                       summary = await self.consolidator.summarize_cluster(cluster)
                       await self.consolidator.store_episode(
                           cluster, summary, session_id
                       )
               
               except Exception as e:
                   logger.error(f"Consolidation failed for {session_id}: {e}")
   ```

2. Add health monitoring
3. Add tests

**Acceptance Criteria**:
- [ ] Runs asynchronously
- [ ] Non-blocking
- [ ] Error handling
- [ ] Metrics collection
- [ ] Tests passing

---

## Phase 2D: Distillation Engine (Weeks 9-10)

### Week 9: Pattern Mining

**Deliverable**: Multi-episode pattern detection

**Tasks**:
1. Create `src/memory/pattern_miner.py`
   ```python
   class PatternMiner:
       async def find_patterns(
           self, 
           episodes: List[Dict],
           min_occurrences: int = 3
       ) -> List[Dict]:
           """Detect recurring patterns across episodes"""
           
           # 1. Extract entities/themes from episodes
           themes = await self._extract_themes(episodes)
           
           # 2. Find recurring themes
           patterns = self._find_recurring(themes, min_occurrences)
           
           # 3. Score pattern significance
           scored = self._score_patterns(patterns)
           
           return scored
   ```

2. Add tests

---

### Week 10: Knowledge Synthesis & Distillation Engine

**Deliverable**: L3→L4 knowledge distillation

**Tasks**:
1. Create `src/memory/knowledge_distiller.py`
   ```python
   class KnowledgeDistiller:
       async def synthesize_knowledge(
           self, 
           pattern: Dict,
           source_episodes: List[str]
       ) -> Dict:
           """Generate generalized knowledge from pattern"""
           prompt = f"""
           Based on these recurring patterns:
           {pattern}
           
           Generate a generalized knowledge statement with confidence.
           """
           
           knowledge = await self.llm.generate(prompt)
           
           return {
               'content': knowledge,
               'confidence': self._calculate_confidence(pattern),
               'source_episodes': source_episodes,
               'provenance_links': source_episodes
           }
   ```

2. Create `src/memory/engines/distillation_engine.py`
   ```python
   class DistillationEngine:
       async def run(self):
           """Background task: distill L3→L4"""
           while True:
               await self._distill_knowledge()
               await asyncio.sleep(86400)  # Daily
   ```

3. Add tests

**Acceptance Criteria**:
- [ ] Mines patterns from episodes
- [ ] Synthesizes knowledge
- [ ] Stores in L4 with provenance
- [ ] Runs asynchronously
- [ ] Tests passing

---

## Phase 2E: Memory Orchestrator (Week 11)

**Deliverable**: Unified system coordination

**Tasks**:
1. Refactor `memory_system.py` → `memory_orchestrator.py`
2. Integrate all tiers
3. Add engine lifecycle management
4. Add multi-tier query coordination
5. Add health aggregation
6. Add tests

**Acceptance Criteria**:
- [ ] Single unified interface
- [ ] Manages all 4 tiers
- [ ] Coordinates 3 engines
- [ ] Health checks
- [ ] Metrics aggregation
- [ ] Tests passing

---

## Success Metrics

### Technical Metrics
- [ ] All tier classes implemented
- [ ] All engines implemented
- [ ] CIAR scoring working
- [ ] L1→L2→L3→L4 flow complete
- [ ] 80%+ test coverage
- [ ] <100ms query latency (L1)
- [ ] Async engines non-blocking

### Functionality Metrics
- [ ] Stores conversation turns (L1)
- [ ] Promotes significant facts (L2)
- [ ] Consolidates episodes (L3)
- [ ] Distills knowledge (L4)
- [ ] Circuit breakers working
- [ ] Bi-temporal model working

### Documentation
- [ ] All classes documented
- [ ] Architecture diagrams updated
- [ ] README reflects reality
- [ ] Migration guides complete

---

## Risk Management

### High-Risk Items
1. **LLM Integration** - External dependency
   - Mitigation: Circuit breaker + fallback
2. **Async Coordination** - Complex concurrency
   - Mitigation: Use proven patterns (asyncio tasks)
3. **Bi-Temporal Model** - Novel implementation
   - Mitigation: Start simple, iterate

### Blocked Items
- Need LLM API access for fact extraction
- Need production database instances for testing

---

## Next Steps

**Week 1 Starts**: Implement L1 Active Context Tier  
**File**: `src/memory/tiers/active_context_tier.py`  
**Tests**: `tests/memory/test_active_context_tier.py`

**First Commit Message**:
```
feat(memory): implement L1 Active Context Tier

- Add base tier abstraction
- Implement active context tier with turn windowing
- Add TTL management and session isolation
- Tests: 80%+ coverage

Part of Phase 2A (ADR-003 implementation)
```

---

**Ready to begin? Start with Week 1!**

---

## Source: phase-3-prereq-complete.md

# Phase 3 Pre-Requisite Implementation Complete

**Date**: December 28, 2025  
**Status**: ✅ COMPLETE  
**Duration**: 1 day

## Executive Summary

Successfully refactored the PromotionEngine to align with ADR-003's batch processing specification, resolving the critical mismatch between the architecture document and implementation. This prerequisite work enables Phase 3 (Agent Integration Layer) to proceed with the correct memory promotion strategy.

## Problem Statement

**Critical Mismatch Identified**: ADR-003 (Revised Nov 2, 2025) specifies **batch compression with topic segmentation** for L1→L2 promotion, but the existing implementation performed **per-turn fact extraction** with individual LLM calls per turn.

## Solution

### Architecture Transformation

**Before**:
```
L1 turns → [FactExtractor: 1 LLM call per turn] → Facts → CIAR filter → L2
```

**After**:
```
L1 batch (10-20 turns) → [TopicSegmenter: 1 LLM call] → Topic Segments 
  → CIAR filter on segments → [FactExtractor per segment] → Facts with segment context → L2
```

### Key Benefits

1. **10-20× LLM Call Reduction**: Single batch call vs. per-turn calls
2. **Noise Compression**: Filters greetings, acknowledgments, filler before fact extraction
3. **Contextual Coherence**: Facts extracted from coherent topic segments, not isolated turns
4. **CIAR Pre-Filter**: Low-scoring segments don't trigger fact extraction (saves API costs)
5. **Provenance Tracking**: Facts linked to source segments via `topic_segment_id`

## Implementation Details

### 1. Phase 3 Dependencies Installed ✅

Added to `requirements.txt`:
- `langgraph>=0.1.0` - Multi-agent state graphs and orchestration
- `langchain-core>=0.2.0` - Agent tools, message structures, callbacks
- `fastapi>=0.100.0` - Agent wrapper API (/run_turn endpoint)
- `uvicorn>=0.23.0` - ASGI server for FastAPI

### 2. TopicSegmenter Component ✅

**File**: `src/memory/engines/topic_segmenter.py` (287 lines)

**Features**:
- Batch threshold enforcement (10-20 turns, configurable)
- Single LLM call per batch (Gemini 2.5 Flash per ADR-006)
- Noise compression and topic segmentation
- `TopicSegment` Pydantic model with validation
- Graceful LLM failure fallback (single segment with low certainty)

**TopicSegment Model**:
```python
class TopicSegment(BaseModel):
    segment_id: str
    topic: str                    # Brief label (3-200 chars)
    summary: str                  # Concise narrative (10-2000 chars)
    key_points: List[str]         # 3-10 significant points
    turn_indices: List[int]       # Source turn indices
    certainty: float              # LLM confidence (0.0-1.0)
    impact: float                 # Importance estimate (0.0-1.0)
    participant_count: int
    message_count: int
    temporal_context: Dict        # Dates, times, deadlines
```

### 3. PromotionEngine Refactor ✅

**File**: `src/memory/engines/promotion_engine.py` (162 lines)

**New Flow**:
1. Check L1 turn count against batch threshold (skip if < 10)
2. Retrieve batch from ActiveContextTier
3. Use TopicSegmenter for batch compression and segmentation
4. Score each segment: `CIAR = (certainty × impact) × 1.0 × 1.0` (fresh segments)
5. Filter segments below promotion threshold (default: 0.6)
6. Extract facts from significant segments only
7. Store facts with segment metadata in WorkingMemoryTier

**Constructor Changes**:
```python
def __init__(
    self,
    l1_tier: ActiveContextTier,
    l2_tier: WorkingMemoryTier,
    topic_segmenter: TopicSegmenter,  # NEW
    fact_extractor: FactExtractor,
    ciar_scorer: CIARScorer,
    config: Optional[Dict[str, Any]] = None
):
    # batch_min_turns, batch_max_turns from config
```

### 4. Data Model Updates ✅

**File**: `src/memory/models.py`

Enhanced `Fact` model:
```python
class Fact(BaseModel):
    # ... existing fields ...
    
    # NEW: Topic Segmentation (ADR-003: batch processing context)
    topic_segment_id: Optional[str] = None  # Links to source TopicSegment
    topic_label: Optional[str] = None       # Brief topic from segment
```

### 5. Comprehensive Test Suite ✅

#### TopicSegmenter Tests
**File**: `tests/memory/engines/test_topic_segmenter.py` (378 lines, 14 tests)

- Model validation (topic/summary length constraints)
- Batch threshold enforcement (skips if < min_turns)
- Multi-segment extraction (3 segments from 10 turns)
- LLM failure fallback (creates single segment with low certainty)
- Invalid JSON handling
- Turn truncation (exceeds max_turns)
- Conversation formatting
- Fallback segment creation

**Result**: ✅ 14/14 tests passing (0.16s)

#### PromotionEngine Tests
**File**: `tests/memory/engines/test_promotion_engine.py` (353 lines, 9 tests)

- Batch threshold validation
- Successful batch processing (2 segments → 2 facts promoted)
- Low-scoring segment filtering (CIAR < threshold)
- No segments handling
- Health check includes batch configuration
- Segment-level CIAR scoring
- Segment formatting for extraction

**Result**: ✅ 9/9 tests passing (1.43s)

#### Integration Verification
**Command**: `pytest tests/memory/engines/ -v`  
**Result**: ✅ 37/37 tests passing (1.39s)

## Metrics

| Metric | Value |
|--------|-------|
| Files Created | 2 |
| Files Modified | 3 |
| Lines Added | ~800 |
| Tests Added | 23 |
| Test Coverage | 100% (new components) |
| Test Pass Rate | 23/23 (100%) |
| LLM Call Reduction | 10-20× |
| Batch Threshold | 10-20 turns (configurable) |

## Research Validation

- ✅ **RT-01** (ADR-007): InjectedState pattern ready for Phase 3 integration
- ✅ **RT-06** (ADR-006): Gemini 2.5 Flash for batch segmentation (10 RPM, 250K TPM)
- ✅ **RT-03**: Batch processing reduces Redis Streams overhead
- ✅ **ADR-003**: Aligned with revised architecture specification

## Next Steps: Phase 3 Implementation

With ADR-003 alignment complete, Phase 3 can now proceed:

### Week 1: Foundation
- Namespace Manager with Hash Tag pattern (`{session:id}:resource`)
- Lua atomicity scripts (`atomic_promotion.lua`)
- Redis Streams consumer groups

### Week 2: UnifiedMemorySystem + Unified Tools
- Enhance `memory_system.py` to integrate all tiers + engines
- Build high-level agent tools using ADR-007's InjectedState pattern

### Week 3: CIAR + Granular Tools
- Expose CIAR scoring to agents (RT-05: 18-48% improvement validated)
- Implement tier-specific granular tools

### Week 4: Agent Framework
- `BaseAgent` abstract class
- `MemoryAgent` (UC-01: full hybrid, all 4 tiers)
- `RAGAgent` (UC-02: vector-only baseline)
- `FullContextAgent` (UC-03: no retrieval baseline)

### Week 5-6: LangGraph + API
- Supervisor + sub-graph topology (ADR-007)
- FastAPI `/run_turn` endpoint
- Integration tests (≥80% coverage, 50-agent concurrency)

## Documentation Updates

- ✅ DEVLOG.md: Added entry for 2025-12-28
- ✅ requirements.txt: Added Phase 3 dependencies
- ✅ All new components include comprehensive docstrings

## Success Criteria

| Criterion | Status |
|-----------|--------|
| TopicSegmenter implemented | ✅ Complete |
| PromotionEngine refactored | ✅ Complete |
| Data models updated | ✅ Complete |
| Test coverage ≥80% | ✅ 100% (new code) |
| All tests passing | ✅ 37/37 |
| ADR-003 compliance | ✅ Verified |
| Phase 3 dependencies installed | ✅ Complete |

## Conclusion

The Phase 3 pre-requisite is **COMPLETE**. The PromotionEngine now implements ADR-003's batch compression strategy with topic segmentation, resolving the critical architectural mismatch. All tests pass, dependencies are installed, and the codebase is ready for Phase 3 Agent Integration Layer implementation.

**Phase 3 is cleared to start.**

