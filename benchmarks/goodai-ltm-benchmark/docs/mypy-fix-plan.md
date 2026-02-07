# Mypy Fix Plan

## Goal
Fix all reported mypy errors in the `mas-memory-layer/benchmarks/goodai-ltm-benchmark` project.

## Errors Overview
Found 85 errors in 25 files.

## Plan

### Phase 1: Runner
- [ ] `runner/master_log.py`: Fix missing type annotations
- [ ] `runner/scheduler.py`: Fix `Path` undefined and missing return type

### Phase 2: Utils
- [ ] `utils/ui.py`: Fix missing type annotations
- [ ] `utils/llm.py`: Fix `Any` return
- [ ] `utils/data.py`: Fix missing type annotations
- [ ] `utils/filling_task.py`: Fix `Any` return

### Phase 3: Dataset Interfaces
- [ ] `dataset_interfaces/interface.py`: Fix missing return types, redundant casts, missing argument types
- [ ] `dataset_interfaces/factory.py`: Fix redundant cast
- [ ] `dataset_interfaces/tests/test_match_evaluation.py`: Fix missing return types

### Phase 4: Model Interfaces
- [ ] `model_interfaces/ltm_agent_wrapper.py`: Fix missing return types
- [ ] `model_interfaces/llm_interface.py`: Fix missing return types
- [ ] `model_interfaces/gemini_interface.py`: Fix missing argument types
- [ ] `model_interfaces/charlie_interface.py`: Fix missing types
- [ ] `model_interfaces/base_ltm_agent.py`: Fix missing types
- [ ] `model_interfaces/length_bias_agent.py`: Fix missing return types
- [ ] `model_interfaces/memgpt_proxy.py`: Fix missing types
- [ ] `model_interfaces/huggingface_interface.py`: Fix missing return types

### Phase 5: Datasets
- [ ] `datasets/sally_ann.py`: Fix variable annotation
- [ ] `datasets/restaurant.py`: Fix missing argument types

### Phase 6: Reporting
- [ ] `reporting/results.py`: Fix missing return types
- [ ] `reporting/generate.py`: Fix missing types and redundant casts
- [ ] `reporting/detailed_report.py`: Fix missing return types
- [ ] `reporting/comparative_report.py`: Fix missing return types

### Phase 7: Root & Misc
- [ ] `evaluate.py`: Fix missing return types
- [ ] `webui/server.py`: Fix `Any` return
- [ ] `dev_scripts/figures.py`: Fix missing return types and variable annotations

## Verification
Run `poetry run mypy .` after each phase.
