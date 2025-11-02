# LLM Integration Documentation

This directory contains documentation for Large Language Model (LLM) integrations in the Multi-Layered Memory System project.

## ✅ Provider Status

**Google Gemini: SELECTED**

Google Gemini free tier selected as LLM provider following AgentRouter abandonment. Offers generous rate limits (10-15 RPM, 250k-1M TPM) with 1M token context windows across 3 model variants optimized for quality, volume, and speed.

**Implementation Status:** Ready for Phase 2 integration (Week 4-11)

## Architecture Decision Records

See related ADRs for LLM provider strategy:
- **[ADR-006: Free-Tier LLM Provider Strategy](../ADR/006-free-tier-llm-strategy.md)** ✅ **CURRENT** - Google Gemini multi-model strategy
- **[ADR-005: Multi-Tier LLM Provider Strategy](../ADR/005-multi-tier-llm-provider-strategy.md)** - ~~Superseded~~ (AgentRouter not accessible)

## Quick Start

### 1. Get Gemini API Key
```bash
# Register at Google AI Studio
# Get free API key from: https://aistudio.google.com/apikey
```

### 2. Configure Environment
```bash
# Add to .env file
echo "GOOGLE_API_KEY=your-api-key-here" >> .env
```

### 3. Install Dependencies
```bash
pip install google-generativeai
```

### 4. Start Implementation
See **Week 4-5** in the [Implementation Plan](../plan/implementation-plan-02112025.md) for CIAR Scorer and Fact Extraction integration

## Model Selection Quick Reference

| Task | Model | Cost/1M tokens | When to Use |
|------|-------|---------------|-------------|
| CIAR Scoring | GPT-5 Mini | $0.33 | High frequency, simple classification |
| Fact Extraction | DeepSeek-V3 | $0.38 | Primary workload, balanced quality/cost |
| Episode Summary | GLM-4.6 | $0.31 | Narrative generation |
| Knowledge Synthesis | GPT-5 | $3.44 | Complex reasoning, low frequency |

## Cost Targets

- **Daily Budget:** $3.00 (≈ $90/month pace)
- **Monthly Budget:** $60-80 (with buffer)
- **Per Operation:**
  - Fact extraction: <$0.002 per fact
  - Episode summary: <$0.01 per episode
  - Knowledge synthesis: <$0.05 per document

## Support

**Technical Issues:**
- Review troubleshooting section in [Setup Guide](agentrouter-setup-guide.md#10-troubleshooting)
- Check [ADR-005](../ADR/005-multi-tier-llm-provider-strategy.md) for architectural decisions

**AgentRouter Issues:**
- Dashboard: https://agentrouter.org/dashboard
- Support: support@agentrouter.org

---

**Last Updated:** November 2, 2025  
**Maintained By:** Development Team
