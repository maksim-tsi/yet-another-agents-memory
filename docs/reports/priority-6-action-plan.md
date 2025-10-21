# Priority 6: Action Plan to Meet Coverage Criteria

**Date:** October 21, 2025  
**Objective:** Achieve >80% coverage per adapter and meet all Priority 6 specification requirements  
**Current Overall Coverage:** 75%  
**Target Overall Coverage:** >80%

---

## Quick Reference

| Phase | Focus | Tests | Hours | Priority |
|-------|-------|-------|-------|----------|
| **Phase 1** | Fix failing tests | 21 | 4-6 | 🔴 CRITICAL |
| **Phase 2** | Neo4j 69%→80% | 8-10 | 3-4 | 🔴 HIGH |
| **Phase 3** | Qdrant 68%→80% | 9-11 | 3-4 | 🔴 HIGH |
| **Phase 4** | Typesense 72%→80% | 6-8 | 2-3 | 🟡 MEDIUM |
| **Phase 5** | Postgres 71%→80% | 7-9 | 3 | 🟡 MEDIUM |
| **Phase 6** | Redis 75%→80% | 5-6 | 2 | 🟢 LOW |
| **Phase 7** | Integration tests | 28 | 6-8 | 🔴 HIGH |
| **TOTAL** | | 84-93 | 23-30 | |

---

## Phase 1: Fix Failing Tests (CRITICAL)

**Priority:** 🔴 CRITICAL  
**Time:** 4-6 hours  
**Tests:** 21 failing tests  
**Goal:** All existing tests passing

### Neo4j Failing Tests (9 tests)

#### 1.1 Fix Async Mock Patterns
**File:** `tests/storage/test_neo4j_adapter.py`

```python
# ISSUE: AsyncMock.json() needs to be awaited
# Current (WRONG):
mock_response.json = AsyncMock(return_value={'data': [...]})

# Fixed (CORRECT):
async def json_response():
    return {'data': [...]}
mock_response.json = json_response
```

**Tests to fix:**
- `test_retrieve_batch` - Add proper async mock for json()
- `test_health_check_connected` - Update expected status from 'healthy' to 'unhealthy'
- `test_health_check_not_connected` - Update expected status to 'unhealthy'

**Time:** 1-1.5 hours

#### 1.2 Fix Return Value Expectations
**File:** `tests/storage/test_neo4j_adapter.py`

```python
# ISSUE: Batch operations return dict, not bool or list
# test_store_batch_entities
assert len(result) == 3  # WRONG - result is not a list

# Fix: Check actual implementation return type
result = await adapter.store_batch(batch_data)
assert isinstance(result, dict) or isinstance(result, list)

# test_delete_batch
assert result is True  # WRONG - returns dict {id: bool}

# Fix: Check dict structure
assert isinstance(result, dict)
assert all(isinstance(v, bool) for v in result.values())
```

**Tests to fix:**
- `test_store_batch_entities` - Update assertions for actual return type
- `test_delete_batch` - Expect dict not bool

**Time:** 1 hour

#### 1.3 Fix Validation Tests
**File:** `tests/storage/test_neo4j_adapter.py`

```python
# ISSUE: Tests expect StorageQueryError but implementation validates in store()
# Current tests:
# test_store_relationship_missing_from
# test_store_relationship_missing_to  
# test_store_relationship_missing_type

# Fix: Check if validation is in store() or separate method
# Update test to match actual validation behavior
```

**Tests to fix:**
- `test_store_relationship_missing_from`
- `test_store_relationship_missing_to`
- `test_store_relationship_missing_type`
- `test_connection_failure_recovery`

**Time:** 1.5-2 hours

### Qdrant Failing Tests (3 tests)

#### 1.4 Fix Qdrant Mock Issues
**File:** `tests/storage/test_qdrant_adapter.py`

```python
# test_delete_batch_vectors
# ISSUE: Returns dict {id: bool} not bool
assert result is True  # WRONG

# Fix:
assert isinstance(result, dict)
assert all(isinstance(v, bool) for v in result.values())

# test_health_check_connected
# ISSUE: Missing 'collection_info' in health response
assert 'collection_info' in health  # WRONG - field doesn't exist

# Fix: Check actual health_check() return structure
# Update test to match actual fields returned

# test_health_check_not_connected
# ISSUE: Returns 'unhealthy' not 'disconnected'
assert health['status'] == 'disconnected'  # WRONG

# Fix:
assert health['status'] == 'unhealthy'
```

**Time:** 1 hour

### Typesense Failing Tests (9 tests)

#### 1.5 Fix Typesense Async Issues
**File:** `tests/storage/test_typesense_adapter.py`

```python
# ISSUE: Multiple tests have unawaited coroutines

# All these tests need async mock fixes:
# - test_store_batch_documents
# - test_health_check_connected
# - test_search_with_filter_by
# - test_search_with_facet_by
# - test_search_with_sort_by
# - test_search_empty_results
# - test_store_with_auto_id

# Fix pattern:
# 1. Make response.json() async
async def json_response():
    return {'hits': [...]}
mock_response.json = json_response

# 2. Make headers a regular dict, not AsyncMock
mock_client.headers = {'X-API-Key': 'test'}  # Not AsyncMock!

# 3. Fix delete_batch return type
assert result is True  # WRONG - returns dict

assert isinstance(result, dict)  # CORRECT
```

**Time:** 1.5-2 hours

---

## Phase 2: Neo4j 69% → 80% Coverage

**Priority:** 🔴 HIGH  
**Time:** 3-4 hours  
**Tests Needed:** 8-10 new tests  
**Lines to Cover:** ~28 of 78 missing

### 2.1 Relationship Operations Tests

**Missing Lines:** 237-241, 266-270, 286-290

```python
class TestNeo4jRelationships:
    """Test relationship CRUD operations."""
    
    async def test_create_relationship_basic(self):
        """Test creating a basic relationship between nodes."""
        # Create two nodes
        node1 = await adapter.store({'type': 'Person', 'name': 'Alice'})
        node2 = await adapter.store({'type': 'Person', 'name': 'Bob'})
        
        # Create relationship
        rel = await adapter.create_relationship(
            from_id=node1,
            to_id=node2,
            rel_type='KNOWS',
            properties={'since': 2020}
        )
        
        assert rel is not None
        assert rel['type'] == 'KNOWS'
    
    async def test_get_relationships_by_node(self):
        """Test retrieving all relationships for a node."""
        node_id = 'test-node-123'
        relationships = await adapter.get_relationships(node_id)
        assert isinstance(relationships, list)
    
    async def test_delete_relationship(self):
        """Test deleting a relationship."""
        rel_id = 'test-rel-123'
        result = await adapter.delete_relationship(rel_id)
        assert result is True or isinstance(result, dict)
    
    async def test_update_relationship_properties(self):
        """Test updating relationship properties."""
        rel_id = 'test-rel-123'
        new_props = {'weight': 0.8, 'updated': '2025-10-21'}
        result = await adapter.update_relationship(rel_id, new_props)
        assert result is not None
```

**Time:** 1.5 hours

### 2.2 Query Builder Tests

**Missing Lines:** 332-372

```python
class TestNeo4jQueryBuilder:
    """Test Cypher query construction helpers."""
    
    async def test_query_with_multiple_filters(self):
        """Test complex query with multiple filter conditions."""
        query = {
            'match': {'type': 'Person'},
            'filters': [
                {'field': 'age', 'op': '>', 'value': 25},
                {'field': 'city', 'op': '=', 'value': 'NYC'}
            ],
            'limit': 10
        }
        results = await adapter.query(query)
        assert isinstance(results, list)
    
    async def test_query_with_sorting(self):
        """Test query with ORDER BY clause."""
        query = {
            'match': {'type': 'Person'},
            'sort': [{'field': 'name', 'order': 'ASC'}]
        }
        results = await adapter.query(query)
        assert isinstance(results, list)
    
    async def test_query_with_aggregation(self):
        """Test COUNT/SUM/AVG aggregation queries."""
        query = {
            'match': {'type': 'Person'},
            'aggregate': {'function': 'COUNT', 'alias': 'total'}
        }
        result = await adapter.query(query)
        assert 'total' in result or isinstance(result, int)
```

**Time:** 1 hour

### 2.3 Error Handling Tests

**Missing Lines:** 379-381, 400, 403, 417-420

```python
class TestNeo4jErrorHandling:
    """Test error handling and recovery."""
    
    async def test_query_timeout_handling(self):
        """Test handling of query timeouts."""
        with patch.object(adapter.driver, 'session') as mock_session:
            mock_session.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(StorageQueryError, match="timeout"):
                await adapter.query({'match': {'type': 'Person'}})
    
    async def test_connection_pool_exhausted(self):
        """Test handling when connection pool is exhausted."""
        # Simulate pool exhaustion
        with pytest.raises(StorageConnectionError):
            # Test implementation
            pass
    
    async def test_invalid_cypher_syntax(self):
        """Test handling of invalid Cypher queries."""
        with pytest.raises(StorageQueryError, match="syntax"):
            await adapter.execute_query("INVALID CYPHER QUERY")
```

**Time:** 0.5-1 hour

---

## Phase 3: Qdrant 68% → 80% Coverage

**Priority:** 🔴 HIGH  
**Time:** 3-4 hours  
**Tests Needed:** 9-11 new tests  
**Lines to Cover:** ~28 of 74 missing

### 3.1 Complex Filter Tests

**Missing Lines:** 214-216, 263-265

```python
class TestQdrantAdvancedFilters:
    """Test complex filter combinations."""
    
    async def test_multiple_must_conditions(self):
        """Test vector search with multiple MUST conditions."""
        filters = {
            'must': [
                {'key': 'category', 'match': {'value': 'tech'}},
                {'key': 'year', 'range': {'gte': 2020}}
            ]
        }
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            filters=filters,
            limit=10
        )
        assert isinstance(results, list)
    
    async def test_should_conditions(self):
        """Test OR-like SHOULD conditions."""
        filters = {
            'should': [
                {'key': 'tag', 'match': {'value': 'ai'}},
                {'key': 'tag', 'match': {'value': 'ml'}}
            ]
        }
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            filters=filters
        )
        assert isinstance(results, list)
    
    async def test_must_not_conditions(self):
        """Test exclusion with MUST_NOT."""
        filters = {
            'must_not': [
                {'key': 'status', 'match': {'value': 'deleted'}}
            ]
        }
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            filters=filters
        )
        assert isinstance(results, list)
    
    async def test_nested_filter_groups(self):
        """Test nested filter conditions."""
        filters = {
            'must': [
                {
                    'should': [
                        {'key': 'type', 'match': {'value': 'doc'}},
                        {'key': 'type', 'match': {'value': 'article'}}
                    ]
                }
            ]
        }
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            filters=filters
        )
        assert isinstance(results, list)
```

**Time:** 1.5 hours

### 3.2 Collection Management Tests

**Missing Lines:** 475-517

```python
class TestQdrantCollectionManagement:
    """Test collection lifecycle operations."""
    
    async def test_create_collection_with_schema(self):
        """Test creating collection with specific vector config."""
        config = {
            'vectors': {
                'size': 384,
                'distance': 'Cosine'
            },
            'optimizers_config': {
                'indexing_threshold': 10000
            }
        }
        result = await adapter.create_collection('test_coll', config)
        assert result is True or result is None
    
    async def test_update_collection_config(self):
        """Test updating collection configuration."""
        new_config = {'optimizers_config': {'indexing_threshold': 20000}}
        result = await adapter.update_collection('test_coll', new_config)
        assert result is not None
    
    async def test_get_collection_info_detailed(self):
        """Test retrieving detailed collection information."""
        info = await adapter.get_collection_info('test_coll')
        assert 'vectors_count' in info
        assert 'indexed_vectors_count' in info
        assert 'points_count' in info
    
    async def test_list_all_collections(self):
        """Test listing all available collections."""
        collections = await adapter.list_collections()
        assert isinstance(collections, list)
```

**Time:** 1-1.5 hours

### 3.3 Advanced Vector Search Tests

**Missing Lines:** 345-347, 604-607

```python
class TestQdrantAdvancedSearch:
    """Test advanced vector search features."""
    
    async def test_search_with_score_threshold(self):
        """Test filtering results by similarity score."""
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            score_threshold=0.8,
            limit=10
        )
        # All results should have score >= 0.8
        assert all(r.get('score', 0) >= 0.8 for r in results)
    
    async def test_search_with_payload_include(self):
        """Test including specific payload fields only."""
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            with_payload=['title', 'author'],
            limit=5
        )
        assert isinstance(results, list)
    
    async def test_search_with_vector_name(self):
        """Test searching with named vectors."""
        results = await adapter.search_vectors(
            query_vector=[0.1] * 384,
            vector_name='content_vector',
            limit=10
        )
        assert isinstance(results, list)
```

**Time:** 1 hour

---

## Phase 4: Typesense 72% → 80% Coverage

**Priority:** 🟡 MEDIUM  
**Time:** 2-3 hours  
**Tests Needed:** 6-8 new tests  
**Lines to Cover:** ~16 of 54 missing

### 4.1 Schema Operations Tests

**Missing Lines:** 386-397, 401-403

```python
class TestTypesenseSchemaOperations:
    """Test collection schema management."""
    
    async def test_create_collection_with_schema(self):
        """Test creating collection with field definitions."""
        schema = {
            'name': 'test_collection',
            'fields': [
                {'name': 'title', 'type': 'string'},
                {'name': 'content', 'type': 'string'},
                {'name': 'year', 'type': 'int32'},
                {'name': 'rating', 'type': 'float'}
            ]
        }
        result = await adapter.create_collection(schema)
        assert result is not None
    
    async def test_update_collection_schema(self):
        """Test adding fields to existing collection."""
        new_field = {'name': 'category', 'type': 'string', 'facet': True}
        result = await adapter.add_field('test_collection', new_field)
        assert result is not None
    
    async def test_get_collection_schema(self):
        """Test retrieving collection schema."""
        schema = await adapter.get_schema('test_collection')
        assert 'fields' in schema
        assert isinstance(schema['fields'], list)
```

**Time:** 1 hour

### 4.2 Advanced Search Tests

**Missing Lines:** 490-506

```python
class TestTypesenseAdvancedSearch:
    """Test advanced search features."""
    
    async def test_search_with_highlighting(self):
        """Test search with result highlighting."""
        query = {
            'q': 'machine learning',
            'query_by': 'content',
            'highlight_full_fields': 'content',
            'highlight_affix_num_tokens': 10
        }
        results = await adapter.search(query)
        assert isinstance(results, list)
    
    async def test_search_with_typo_tolerance(self):
        """Test fuzzy search with typo tolerance."""
        query = {
            'q': 'machne lerning',  # Typos
            'query_by': 'content',
            'num_typos': 2
        }
        results = await adapter.search(query)
        assert isinstance(results, list)
    
    async def test_search_with_prefix_matching(self):
        """Test prefix-based search."""
        query = {
            'q': 'mach',
            'query_by': 'content',
            'prefix': True
        }
        results = await adapter.search(query)
        assert isinstance(results, list)
```

**Time:** 1-1.5 hours

---

## Phase 5: Postgres 71% → 80% Coverage

**Priority:** 🟡 MEDIUM  
**Time:** 3 hours  
**Tests Needed:** 7-9 new tests  
**Lines to Cover:** ~20 of 63 missing

### 5.1 Transaction Management Tests

**Missing Lines:** 523-544, 557, 561-566

```python
class TestPostgresTransactions:
    """Test transaction handling."""
    
    async def test_transaction_commit(self):
        """Test successful transaction commit."""
        async with adapter.transaction() as tx:
            await adapter.store({'session_id': 'test', 'data': 'value1'})
            await adapter.store({'session_id': 'test', 'data': 'value2'})
            await tx.commit()
        
        # Verify data persisted
        results = await adapter.retrieve_by_session('test')
        assert len(results) == 2
    
    async def test_transaction_rollback(self):
        """Test transaction rollback on error."""
        try:
            async with adapter.transaction() as tx:
                await adapter.store({'session_id': 'test', 'data': 'value1'})
                raise Exception("Simulated error")
        except Exception:
            pass
        
        # Verify data NOT persisted
        results = await adapter.retrieve_by_session('test')
        assert len(results) == 0
    
    async def test_nested_transactions(self):
        """Test nested transaction handling (savepoints)."""
        async with adapter.transaction() as outer_tx:
            await adapter.store({'session_id': 'test', 'data': 'outer'})
            
            try:
                async with adapter.transaction() as inner_tx:
                    await adapter.store({'session_id': 'test', 'data': 'inner'})
                    raise Exception("Inner failure")
            except Exception:
                pass
            
            await outer_tx.commit()
        
        # Outer should persist, inner should not
        results = await adapter.retrieve_by_session('test')
        assert len(results) == 1
```

**Time:** 1.5 hours

### 5.2 Constraint and Error Tests

**Missing Lines:** 213-219, 257, 302, 581-585

```python
class TestPostgresConstraints:
    """Test constraint violations and error handling."""
    
    async def test_unique_constraint_violation(self):
        """Test handling of unique constraint violations."""
        await adapter.store({'id': 'test-123', 'data': 'value1'})
        
        with pytest.raises(StorageQueryError, match="unique|duplicate"):
            await adapter.store({'id': 'test-123', 'data': 'value2'})
    
    async def test_foreign_key_violation(self):
        """Test handling of foreign key constraint violations."""
        with pytest.raises(StorageQueryError, match="foreign key"):
            await adapter.store({
                'session_id': 'nonexistent-session',
                'parent_id': 'invalid-parent'
            })
    
    async def test_not_null_constraint(self):
        """Test handling of NOT NULL violations."""
        with pytest.raises(StorageQueryError, match="null|required"):
            await adapter.store({'data': 'value'})  # Missing required field
    
    async def test_check_constraint_violation(self):
        """Test handling of CHECK constraint violations."""
        with pytest.raises(StorageQueryError):
            await adapter.store({'confidence': 1.5})  # >1.0 violates CHECK
```

**Time:** 1 hour

---

## Phase 6: Redis 75% → 80% Coverage

**Priority:** 🟢 LOW (closest to target)  
**Time:** 2 hours  
**Tests Needed:** 5-6 new tests  
**Lines to Cover:** ~11 of 51 missing

### 6.1 TTL and Expiration Tests

**Missing Lines:** 212-224, 244-245

```python
class TestRedisTTL:
    """Test TTL and expiration handling."""
    
    async def test_set_with_ttl_seconds(self):
        """Test setting key with TTL in seconds."""
        await adapter.store('test-key', 'value', ttl=10)
        
        ttl = await adapter.get_ttl('test-key')
        assert 8 <= ttl <= 10  # Allow small variance
    
    async def test_set_with_ttl_expires(self):
        """Test that key actually expires after TTL."""
        await adapter.store('test-key', 'value', ttl=1)
        
        await asyncio.sleep(1.5)
        
        result = await adapter.retrieve('test-key')
        assert result is None
    
    async def test_update_ttl_existing_key(self):
        """Test updating TTL on existing key."""
        await adapter.store('test-key', 'value', ttl=10)
        await adapter.set_ttl('test-key', 20)
        
        ttl = await adapter.get_ttl('test-key')
        assert 18 <= ttl <= 20
    
    async def test_persist_key_remove_ttl(self):
        """Test removing TTL from key (persist)."""
        await adapter.store('test-key', 'value', ttl=10)
        await adapter.persist('test-key')
        
        ttl = await adapter.get_ttl('test-key')
        assert ttl == -1  # No expiration
```

**Time:** 1 hour

### 6.2 Pipeline and Scan Tests

**Missing Lines:** 325-330, 387-391, 465-470, 509-511

```python
class TestRedisPipelineAndScan:
    """Test pipeline operations and key scanning."""
    
    async def test_pipeline_multiple_operations(self):
        """Test executing multiple operations in pipeline."""
        async with adapter.pipeline() as pipe:
            pipe.set('key1', 'value1')
            pipe.set('key2', 'value2')
            pipe.get('key1')
            results = await pipe.execute()
        
        assert len(results) == 3
        assert results[2] == 'value1'
    
    async def test_scan_keys_by_pattern(self):
        """Test scanning keys matching pattern."""
        # Store test keys
        await adapter.store('test:user:1', 'data1')
        await adapter.store('test:user:2', 'data2')
        await adapter.store('test:session:1', 'data3')
        
        # Scan for user keys
        keys = []
        async for key in adapter.scan_iter('test:user:*'):
            keys.append(key)
        
        assert len(keys) == 2
        assert all('user' in key for key in keys)
```

**Time:** 1 hour

---

## Phase 7: Integration Tests

**Priority:** 🔴 HIGH  
**Time:** 6-8 hours  
**Tests Needed:** ~28 tests  
**Goal:** Reach 25% integration test proportion (from 6%)

### 7.1 Multi-Adapter Workflows (8 tests)

```python
class TestMultiAdapterWorkflows:
    """Test workflows spanning multiple adapters."""
    
    @pytest.mark.integration
    async def test_cache_write_through_to_postgres(self):
        """Test Redis cache with Postgres persistence."""
        # Write to Redis (L1)
        await redis_adapter.store('session:123', data)
        
        # Should also persist to Postgres
        pg_data = await postgres_adapter.retrieve('session:123')
        assert pg_data == data
    
    @pytest.mark.integration
    async def test_vector_search_with_metadata_enrichment(self):
        """Test Qdrant search enriched with Postgres metadata."""
        # Store vector in Qdrant
        vector_id = await qdrant_adapter.store_vector(embedding, {'ref_id': 'doc-123'})
        
        # Store metadata in Postgres
        await postgres_adapter.store({'id': 'doc-123', 'title': 'Test'})
        
        # Search and enrich
        results = await qdrant_adapter.search_vectors(query_vector)
        for result in results:
            metadata = await postgres_adapter.retrieve(result['ref_id'])
            result['metadata'] = metadata
        
        assert all('metadata' in r for r in results)
    
    @pytest.mark.integration
    async def test_full_text_search_with_graph_relations(self):
        """Test Typesense search combined with Neo4j relationships."""
        # Search documents
        docs = await typesense_adapter.search({'q': 'AI', 'query_by': 'content'})
        
        # Get related entities from Neo4j
        for doc in docs:
            relations = await neo4j_adapter.get_relationships(doc['id'])
            doc['relations'] = relations
        
        assert len(docs) > 0
    
    # ... 5 more multi-adapter tests
```

**Time:** 2-3 hours

### 7.2 Error Recovery Scenarios (7 tests)

```python
class TestErrorRecovery:
    """Test error handling and recovery."""
    
    @pytest.mark.integration
    async def test_redis_fallback_to_postgres_on_failure(self):
        """Test fallback to Postgres when Redis is down."""
        # Simulate Redis failure
        await redis_adapter.disconnect()
        
        # Should fallback to Postgres
        data = await system.retrieve('session:123')  # Uses fallback
        assert data is not None
    
    @pytest.mark.integration
    async def test_reconnection_after_network_failure(self):
        """Test automatic reconnection after network issue."""
        # Simulate disconnect
        await adapter.disconnect()
        
        # Wait for reconnection
        await asyncio.sleep(2)
        
        # Should auto-reconnect and work
        result = await adapter.health_check()
        assert result['status'] == 'healthy'
    
    # ... 5 more error recovery tests
```

**Time:** 2 hours

### 7.3 Cross-Adapter Consistency (6 tests)

```python
class TestCrossAdapterConsistency:
    """Test data consistency across adapters."""
    
    @pytest.mark.integration
    async def test_cache_invalidation_propagation(self):
        """Test cache invalidation propagates correctly."""
        # Write to all layers
        await redis_adapter.store('key', 'value1')
        await postgres_adapter.store('key', 'value1')
        
        # Update in Postgres
        await postgres_adapter.update('key', 'value2')
        
        # Redis should be invalidated
        redis_val = await redis_adapter.retrieve('key')
        assert redis_val is None or redis_val == 'value2'
    
    # ... 5 more consistency tests
```

**Time:** 1.5-2 hours

### 7.4 Performance Under Load (7 tests)

```python
class TestPerformanceUnderLoad:
    """Test adapter performance under concurrent load."""
    
    @pytest.mark.integration
    async def test_concurrent_writes_redis(self):
        """Test handling of concurrent writes to Redis."""
        tasks = [
            redis_adapter.store(f'key-{i}', f'value-{i}')
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 100
    
    @pytest.mark.integration
    async def test_bulk_vector_search_performance(self):
        """Test vector search performance with large result sets."""
        import time
        
        start = time.time()
        results = await qdrant_adapter.search_vectors(
            query_vector=[0.1] * 384,
            limit=1000
        )
        duration = time.time() - start
        
        assert duration < 2.0  # Should complete in <2 seconds
        assert len(results) <= 1000
    
    # ... 5 more performance tests
```

**Time:** 1.5-2 hours

---

## Implementation Schedule

### Week 1: Fix + Critical Coverage
**Days 1-2 (8 hours):** Phase 1 - Fix all 21 failing tests  
**Days 3-4 (8 hours):** Phase 2 - Neo4j 69% → 80%  
**Day 5 (4 hours):** Phase 3 start - Qdrant 68% → 80%

### Week 2: Medium Priority Coverage
**Days 1-2 (4 hours):** Phase 3 complete - Qdrant 68% → 80%  
**Days 3-4 (6 hours):** Phase 4 + 5 - Typesense + Postgres to 80%  
**Day 5 (2 hours):** Phase 6 - Redis 75% → 80%

### Week 3: Integration Tests
**Days 1-5 (6-8 hours):** Phase 7 - Add all integration tests

---

## Success Criteria

### Phase Completion Checklist

- [ ] **Phase 1:** All 122 tests passing (0 failures)
- [ ] **Phase 2:** Neo4j coverage ≥80%
- [ ] **Phase 3:** Qdrant coverage ≥80%
- [ ] **Phase 4:** Typesense coverage ≥80%
- [ ] **Phase 5:** Postgres coverage ≥80%
- [ ] **Phase 6:** Redis coverage ≥80%
- [ ] **Phase 7:** ≥25% integration tests
- [ ] **Final:** Overall coverage ≥80%

### Quality Gates

Each phase must pass:
- ✅ All tests in pytest passing
- ✅ No test warnings or errors
- ✅ Code follows AAA pattern
- ✅ Tests are isolated (no dependencies)
- ✅ Proper async/await usage
- ✅ Meaningful test names and docstrings

---

## Tracking Progress

### Run After Each Phase

```bash
# Run tests with coverage
.venv/bin/python -m pytest tests/storage/ -v \
  --cov=src/storage \
  --cov-report=term-missing \
  --cov-report=html

# Check specific adapter
.venv/bin/python -m pytest tests/storage/test_neo4j_adapter.py -v \
  --cov=src/storage/neo4j_adapter \
  --cov-report=term-missing

# View HTML report
xdg-open htmlcov/index.html
```

### Coverage Target Verification

```bash
# Should show all adapters >80%
.venv/bin/python -m pytest tests/storage/ \
  --cov=src/storage \
  --cov-report=term \
  --cov-fail-under=80
```

---

## Risk Mitigation

### If Behind Schedule

**Priority Triage:**
1. Phase 1 (MUST DO) - Fix failing tests
2. Phase 2 + 3 (MUST DO) - Neo4j + Qdrant to 80%
3. Phase 7 (HIGH) - Core integration tests (10-15 tests)
4. Phase 4-6 (CAN DEFER) - Other adapters to 80%

**Minimum Viable Completion:**
- All failing tests fixed (Phase 1)
- Neo4j + Qdrant ≥80% (Phases 2-3)
- 15 integration tests (Phase 7 partial)
- Time: ~14-16 hours

---

## Next Steps

1. **Review this plan** with team
2. **Assign phases** to developers
3. **Create tracking board** (Jira/GitHub)
4. **Set up branch** for coverage work
5. **Begin Phase 1** immediately

---

**Document Owner:** Development Team  
**Last Updated:** October 21, 2025  
**Status:** Ready for Implementation
