# **ADR-002: Adopting SOTA Neuro-Symbolic and Temporal Patterns for the Hybrid Memory System**

**Title:** Enhancement of the Hybrid Memory Architecture with State-of-the-Art Neuro-Symbolic and Temporal Modeling Patterns
**Status:** Accepted
**Date:** September 14, 2025

## **1. Context**

Following the initial design and prototyping of our four-tier hybrid memory architecture, a comprehensive review of state-of-the-art (SOTA) research in neuro-symbolic AI, graph databases, and agent memory systems was conducted. This review included a detailed analysis of the Zep Temporal Knowledge Graph architecture by Rasmussen et al. and a broader survey of 140+ recent papers on related topics.

The findings from this research have validated our core architectural direction but have also highlighted specific opportunities to enhance our system's capabilities, align it more closely with SOTA practices, and increase its practical value for complex domains like Supply Chain Management. This ADR documents the decisions to adopt these enhancements.

## **2. Decision**

We will enhance the `MAS Memory Layer` with the following four key architectural patterns:

1.  **Adopt "Think-on-Graph" Reasoning:** The internal logic of our agents will be updated to use an iterative, step-by-step graph traversal pattern when reasoning over the Persistent Knowledge Layer, rather than a single, monolithic query.
2.  **Simulate Hypergraphs in the Property Graph:** We will model higher-order, multi-entity events (e.g., shipments, transactions) by introducing a central "event" or "hyperedge" node in our Neo4j schema, to which all participating entities are linked.
3.  **Implement a Full Bi-Temporal Data Model:** We will evolve our Neo4j data model to be bi-temporal, explicitly separating a fact's validity in the real world (`factValidFrom`, `factValidTo`) from the system's observation of that fact (`sourceObservationTimestamp`).
4.  **Defer Direct RDF Ingestion:** We will not build a dedicated RDF ingestion and triple store pipeline at this stage. Instead, we will focus on the more pragmatic and performant property graph model, with the option to add RDF-to-Property-Graph converters in the future.

## **3. Rationale**

These decisions are grounded in empirical evidence from the SOTA literature and are designed to maximize our system's performance, auditability, and real-world modeling accuracy.

*   **"Think-on-Graph" reasoning** is a proven pattern (e.g., ToG, PoG) for reducing LLM hallucination by 30-50%. By constraining agent reasoning to verified paths in the knowledge graph, we create more reliable and auditable decision traces, a critical requirement for enterprise decision support.
*   **Hypergraph simulation** is necessary because real-world SCM events are rarely simple pairwise relationships. Modeling a shipment as a higher-order event involving a supplier, vessel, product, and port is a more accurate representation of reality. This pattern allows us to capture this complexity within our existing, high-performance Neo4j stack without adding a dedicated (and less mature) hypergraph database.
*   **A bi-temporal data model** is the core innovation of SOTA memory systems like Zep. It is the only robust way to handle dynamic, evolving knowledge and answer critical business questions like "What was our inventory level *before* the disruption?" or "Show me the full route this container took." Our previous, simpler temporal model was insufficient for these tasks. This enhancement is critical for the system's practical utility.
*   **Deferring RDF support** is a pragmatic engineering decision. The research indicates a clear industry trend towards property graphs (like Neo4j) for LLM integration due to their more navigable schemas and LLM-friendly query languages (Cypher). By focusing on the property graph model first, we align with best practices and avoid unnecessary complexity.

## **4. Consequences**

*   **Positive:**
    *   **Increased Novelty & Impact:** The system is now more closely aligned with frontier research, incorporating advanced concepts like temporal reasoning and hypergraph modeling.
    *   **Improved Performance & Reliability:** The "Think-on-Graph" pattern will reduce costly LLM errors. The bi-temporal model will improve the accuracy of time-sensitive queries.
    *   **Enhanced Real-World Modeling:** The system will be able to represent complex, multi-party SCM events and reason about their evolution over time, dramatically increasing its value.
    *   **Clearer Development Path:** This ADR provides a precise set of implementation requirements for the development team.

*   **Negative / Trade-offs:**
    *   **Increased Implementation Complexity:** The agent's reasoning logic and the data consolidation procedures will be more complex. Specifically, the `ConsolidationAgent` will now need to handle temporal invalidation, and a new `KnowledgeAuditorAgent` is required to maintain the freshness of dynamic data.
    *   **Richer Data Schema:** The Neo4j schema becomes more complex, requiring careful management of temporal and provenance properties on all factual relationships.
    *   **No Native RDF Support (Initially):** The system will not be able to directly ingest and query RDF/SPARQL sources out-of-the-box, which is an accepted short-term limitation.

## **5. High-Level Implementation Plan**

1.  **Data Model Update (DBMS):**
    *   Modify the Neo4j schema to include the new node label (e.g., `:SCM_Event`).
    *   Add the full suite of temporal and provenance properties (`validity_type`, `factValidFrom`, `factValidTo`, `sourceURI`, `sourceObservationTimestamp`, etc.) to all factual relationship types.

2.  **Agent Logic Update (Code):**
    *   Refactor the `PlannerAgent` to implement an iterative "Think-on-Graph" reasoning loop.
    *   Update all data-extraction agents (`TextbookExtractor`, `StandardsAnalyst`, `LiveKnowledgeCollector`) to correctly populate the new, richer metadata properties.
    *   Enhance the `ConsolidationAgent` with the "find-and-invalidate" logic for handling superseded facts.
    *   Create the new, background `KnowledgeAuditorAgent` for proactive re-validation of dynamic data.

This ADR formalizes our commitment to building a state-of-the-art system. While it increases the engineering effort, the resulting improvements in capability, reliability, and academic contribution are substantial and necessary.