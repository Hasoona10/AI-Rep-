# Cost Optimization Plan for AI Receptionist

## Current Cost Analysis

### Main Cost Drivers
1. **LLM API Calls (GPT-4o-mini)**: ~$0.0002 per call
   - RAG response generation: `rag.generate_response()`
   - Intent classification (fallback): `classify_intent_llm()`
   - Reservation parsing: `reservation_logic.parse_reservation_request()`

2. **Embedding API Calls**: ~$0.0001 per 1K tokens
   - RAG retrieval: `rag._embed_text()` (for vector search)

### Current Optimizations (Already Implemented)
✅ **Three-tier response system** (60-80% cost reduction)
✅ **ML intent classification** (96.66% accuracy, avoids LLM)
✅ **Template responses** for common questions
✅ **Unrelated question detection** (skips RAG)

## Recommended Additional Optimizations

### 1. Response Caching (High Impact: ~30-50% additional savings)
**Cost Savings**: $0.0001 - $0.0002 per cached response

**Implementation**:
- Cache LLM responses for identical questions
- Use simple hash of question text as cache key
- TTL: 24 hours (menu/hours don't change often)

**Expected Impact**: 
- 30-50% of LLM calls can be cached
- For 1000 interactions: Save $0.06 - $0.10

### 2. Optimize Reservation Parsing (Medium Impact: ~5-10% savings)
**Current**: Uses LLM for every reservation request
**Optimization**: Use pattern matching + templates first

**Implementation**:
- Parse date/time using regex patterns
- Use templates for common reservation phrases
- Only use LLM for complex/ambiguous requests

**Expected Impact**: 
- 70-80% of reservations can be parsed without LLM
- For 100 reservations/month: Save $0.014 - $0.016

### 3. Reduce RAG Retrieval Overhead (Medium Impact: ~10-15% savings)
**Current**: Always retrieves 3 documents, even for simple questions
**Optimization**: Skip retrieval for questions already handled by templates

**Implementation**:
- Check if question matches template patterns BEFORE RAG retrieval
- Only retrieve when truly needed

**Expected Impact**: 
- Reduce embedding API calls by 10-15%
- For 1000 interactions: Save $0.01 - $0.015

### 4. Expand Template Coverage (High Impact: ~20-30% additional savings)
**Current**: 77 unique templates from order intents
**Optimization**: Integrate all 926 follow-up mappings

**Implementation**:
- Load `order_followup_mappings.json` into `call_flow.py`
- Use fuzzy matching for similar questions
- Add templates for common follow-up questions

**Expected Impact**: 
- Reduce LLM calls by additional 20-30%
- For 1000 interactions: Save $0.04 - $0.06

### 5. Optimize LLM Parameters (Low Impact: ~5-10% savings)
**Current**: `max_tokens=220`, `temperature=0.6`
**Optimization**: Reduce tokens, lower temperature

**Implementation**:
- Reduce `max_tokens` to 150 (shorter responses)
- Lower `temperature` to 0.3 (more deterministic, cheaper)
- Use `gpt-4o-mini` (already using cheapest model)

**Expected Impact**: 
- 5-10% cost reduction per LLM call
- For 1000 LLM calls: Save $0.01 - $0.02

### 6. Conversation History Optimization (Low Impact: ~5% savings)
**Current**: Uses last 4 messages in conversation history
**Optimization**: Use only last 2 messages for most cases

**Implementation**:
- Reduce history to 2 messages for simple questions
- Only use full history for complex multi-turn conversations

**Expected Impact**: 
- 5% reduction in token usage
- For 1000 interactions: Save $0.01

### 7. Skip RAG for Order-Related Questions (High Impact: ~15-20% savings)
**Current**: Some order questions still trigger RAG
**Optimization**: Handle all order questions with templates

**Implementation**:
- Expand order parsing templates
- Use the 926 follow-up mappings for order questions
- Only use RAG for non-order complex questions

**Expected Impact**: 
- 15-20% reduction in RAG calls
- For 1000 interactions: Save $0.03 - $0.04

## Implementation Priority

### Phase 1: Quick Wins (Implement First)
1. ✅ **Response Caching** - Easy to implement, high impact
2. ✅ **Expand Template Coverage** - Use the 926 mappings
3. ✅ **Skip RAG for Orders** - Already have order parsing

**Expected Savings**: 40-60% additional cost reduction

### Phase 2: Medium Effort
4. ✅ **Optimize Reservation Parsing** - Pattern matching
5. ✅ **Reduce RAG Retrieval** - Skip when templates match

**Expected Savings**: 15-25% additional cost reduction

### Phase 3: Fine-tuning
6. ✅ **Optimize LLM Parameters** - Reduce tokens
7. ✅ **Conversation History** - Shorter history

**Expected Savings**: 10-15% additional cost reduction

## Total Expected Cost Reduction

### Current State
- **Cost per 1000 interactions**: ~$0.04 - $0.08 (after initial optimizations)
- **LLM usage**: 20-40% of questions

### After All Optimizations
- **Cost per 1000 interactions**: ~$0.01 - $0.02
- **LLM usage**: 5-10% of questions
- **Total savings**: 75-85% cost reduction vs. original

## Cost Tracking (Recommended)

Add cost tracking to monitor:
- Number of LLM calls per day
- Cost per interaction
- Cache hit rate
- Template usage rate

This helps identify further optimization opportunities.

