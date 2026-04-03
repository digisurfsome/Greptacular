# 10-Step Criteria Evaluation for NEEDS_EVALUATION Mechanisms

When a mechanism has multiple viable implementation approaches, score each approach 0-100 using these 10 criteria. Each criterion is worth 0-10 points. Sum all 10 for the total score.

---

## Criteria

### 1. Technical Complexity (0-10)
How hard is this approach to implement correctly?
- 0-3: Requires deep expertise, novel algorithms, or cutting-edge tech
- 4-6: Moderate complexity, well-documented but requires careful implementation
- 7-10: Straightforward, well-trodden path, ample examples and libraries

**Score HIGH for simpler approaches** (less complexity = better).

### 2. Scalability (0-10)
How well does this approach handle growth (10x users, 100x data)?
- 0-3: Will hit walls at moderate scale, requires rearchitecture
- 4-6: Scales with known effort (add caching, indexes, workers)
- 7-10: Scales naturally, horizontally, or has proven track record at scale

### 3. Maintainability (0-10)
How easy is this to maintain, debug, and modify over time?
- 0-3: Complex internals, poor observability, tightly coupled
- 4-6: Standard patterns but some hidden complexity
- 7-10: Clean separation, good logging, easy to understand and modify

### 4. Performance (0-10)
What are the latency, throughput, and resource characteristics?
- 0-3: Slow, resource-heavy, or creates bottlenecks
- 4-6: Acceptable performance with optimization
- 7-10: Fast, efficient, minimal resource usage

### 5. Security (0-10)
What are the security implications and attack surface?
- 0-3: Large attack surface, requires significant security hardening
- 4-6: Standard security concerns, handled by following best practices
- 7-10: Minimal attack surface, security built into the approach

### 6. User Experience (0-10)
How does this approach affect what the end user sees and feels?
- 0-3: Visible UX compromises (loading delays, limited features, workarounds)
- 4-6: Acceptable UX with minor tradeoffs
- 7-10: Seamless UX, no compromises visible to the user

### 7. Cost (0-10)
What are the infrastructure, service, and operational costs?
- 0-3: Expensive ongoing costs, paid APIs, dedicated infrastructure
- 4-6: Moderate costs, scales linearly with usage
- 7-10: Low cost, free tier sufficient, or included in existing stack

### 8. Time to Implement (0-10)
How long does this approach take from start to production-ready?
- 0-3: Weeks of development, significant integration work
- 4-6: Days of focused work, some integration required
- 7-10: Hours to days, drop-in solution or minimal wiring

### 9. Ecosystem Fit (0-10)
How well does this approach integrate with the chosen stack?
- 0-3: Foreign to the stack, requires adapters, bridges, or workarounds
- 4-6: Compatible but not native, some glue code needed
- 7-10: Native to the stack, first-party support, idiomatic usage

### 10. Future Flexibility (0-10)
How well does this approach accommodate future changes?
- 0-3: Locked in, hard to swap, creates vendor/architectural lock-in
- 4-6: Changeable with moderate refactoring
- 7-10: Easy to swap, extend, or replace without cascading changes

---

## Scoring Process

1. For each NEEDS_EVALUATION mechanism, list 2-3 competing approaches
2. Score each approach on all 10 criteria (0-10 per criterion)
3. Sum for total (0-100)
4. List 2-4 concrete pros and 2-4 concrete cons per approach
5. Apply Developer's Choice: if top score has >15 point margin, auto-select
6. Apply 15% rule: if top two scores are within 15 points, design both

## Score Interpretation

| Total Score | Meaning |
|-------------|---------|
| 80-100 | Strong approach — high confidence |
| 60-79 | Viable approach — acceptable with known tradeoffs |
| 40-59 | Weak approach — significant concerns |
| 0-39 | Poor approach — should not be selected |

## Example

**Mechanism:** Notification Engine
**Approaches:** (A) Supabase Edge Functions + Resend, (B) BullMQ Queue + Worker

| Criterion | Approach A | Approach B |
|-----------|-----------|-----------|
| Technical Complexity | 8 | 5 |
| Scalability | 6 | 9 |
| Maintainability | 8 | 6 |
| Performance | 7 | 8 |
| Security | 8 | 7 |
| User Experience | 8 | 8 |
| Cost | 9 | 5 |
| Time to Implement | 9 | 5 |
| Ecosystem Fit | 9 | 6 |
| Future Flexibility | 6 | 7 |
| **Total** | **78** | **66** |

Delta = 12 points (within 15) → **Design both. Record alternate_approach with score_delta: 12.**
