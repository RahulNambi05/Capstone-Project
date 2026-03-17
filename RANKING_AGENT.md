# Ranking Agent Module - Documentation

## Overview

The **ranking_agent.py** module provides intelligent candidate ranking by combining semantic similarity scoring with skill overlap scoring. It assigns candidates a final score that reflects both their semantic relevance to the job and their technical skill match.

## Architecture

### Scoring Formula
```
final_score = (semantic_score × semantic_weight) + (skill_score × skill_weight)

Default Weights:
  - semantic_weight = 0.4 (40%) - Semantic similarity from vector store
  - skill_weight = 0.6 (60%) - Skill overlap from semantic matching

Range: 0-100 (float)
```

### Score Components

**Semantic Score (0-100)**
- Derived from vector store retrieval cosine similarity (0-1)
- Normalized to 0-100 scale
- Measures relevance of entire resume to job description
- Weight: 40% (default)

**Skill Score (0-100)**
- Computed by semantic skill matching (sentence-transformers)
- Measures overlap of candidate skills vs job requirements
- Weighted: 70% required skills + 30% preferred skills
- Cosine similarity threshold: 0.75
- Weight: 60% (default)

## Core Functions

### 1. `rank_candidates(candidates, parsed_jd, semantic_weight=0.4, skill_weight=0.6)`

Main ranking function that scores and ranks all candidates.

**Parameters:**
- `candidates` (List[Dict]): From vector store retrieval, each with:
  - `resume_id`: Unique identifier
  - `score`: Semantic similarity (0-1)
  - `metadata`: Experience level, role category, education, top skills

- `parsed_jd` (Dict): Job description with:
  - `required_skills`: List of required technical skills
  - `preferred_skills`: List of preferred/nice-to-have skills

- `semantic_weight` (float): Weight for semantic score (default: 0.4)
- `skill_weight` (float): Weight for skill score (default: 0.6)

**Returns:** List of ranked candidates with fields:
- `rank`: Position (1-based)
- `resume_id`: Unique identifier
- `final_score`: Combined score (0-100)
- `semantic_score`: Semantic similarity (0-100)
- `skill_score`: Skill overlap (0-100)
- `matched_skills`: Skills that match job
- `missing_skills`: Required skills missing
- `explanation`: Human-readable summary
- `metadata`: Candidate information

**Error Handling:**
- Validates weight sum = 1.0, normalizes if needed
- Catches and logs errors per candidate, continues ranking
- Returns empty list if no candidates provided
- Continues on individual candidate errors

### 2. `get_ranking_statistics(candidates)`

Calculate statistics about ranked candidate pool.

**Returns:**
- `total_candidates`: Number of candidates ranked
- `avg_final_score`: Average final score
- `avg_semantic_score`: Average semantic score
- `avg_skill_score`: Average skill score
- `top_score`: Highest final score
- `bottom_score`: Lowest final score
- `median_score`: Median of final scores

### 3. `sort_candidates_by_criteria(candidates, sort_by='final_score', ascending=False)`

Re-sort already-ranked candidates by different criteria.

**Parameters:**
- `candidates`: List of ranked candidates
- `sort_by`: Field to sort by (final_score, semantic_score, skill_score)
- `ascending`: Sort direction (default: False = descending)

**Returns:** Re-ranked list with updated rank positions

## Usage Examples

### Basic Usage

```python
from src.agents.ranking_agent import rank_candidates

# Rank candidates
ranked_candidates = rank_candidates(
    candidates=candidates_from_vector_store,
    parsed_jd=parsed_job_description
)

# Display results
for candidate in ranked_candidates:
    print(f"{candidate['rank']}. {candidate['resume_id']}")
    print(f"   Score: {candidate['final_score']:.1f}/100")
    print(f"   {candidate['explanation']}")
```

### Custom Weights (Skill-Focused)

```python
# Emphasize skill match over semantic similarity (70% skill, 30% semantic)
ranked = rank_candidates(
    candidates=candidates,
    parsed_jd=parsed_jd,
    semantic_weight=0.3,  # 30%
    skill_weight=0.7      # 70%
)
```

### Get Statistics

```python
from src.agents.ranking_agent import get_ranking_statistics

stats = get_ranking_statistics(ranked_candidates)
print(f"Average Score: {stats['avg_final_score']:.1f}/100")
print(f"Top Score: {stats['top_score']:.1f}/100")
```

### Sort by Different Criteria

```python
from src.agents.ranking_agent import sort_candidates_by_criteria

# Sort by skill score instead
by_skill = sort_candidates_by_criteria(
    ranked_candidates,
    sort_by='skill_score'
)

# Sort by semantic in ascending order
by_semantic_asc = sort_candidates_by_criteria(
    ranked_candidates,
    sort_by='semantic_score',
    ascending=True
)
```

## Score Interpretation

| Score Range | Interpretation | Meaning |
|------------|----------------|---------|
| 90-100 | Excellent fit | Strong semantic match + high skill coverage (80%+) |
| 80-89 | Very good fit | Good semantic match + strong skill coverage |
| 70-79 | Good fit | Moderate semantic + good skill match |
| 60-69 | Acceptable fit | Weak semantic or moderate skills |
| <60 | Weak fit | Poor semantic or limited skills |

## Explanation Format

Each candidate receives a human-readable explanation:

```
"Strong semantic match (92.3/100, 40% weight). Strong skill coverage
(88% required, 75% preferred, 60% weight). Matched: Python, Django,
PostgreSQL +4 more. Missing: Kubernetes. Overall: Excellent fit (89.0/100)"
```

Components:
1. Semantic match assessment
2. Skill coverage details
3. Top matched skills
4. Missing critical skills (if any)
5. Overall assessment

## Integration with Main API

The ranking agent is used in `src/api/main.py` in the `/api/v1/match` endpoint:

```python
# In match endpoint
from src.agents.ranking_agent import rank_candidates

# Step 1: Retrieve candidates from vector store
candidates = retrieve_candidates(parsed_job, top_k=100)

# Step 2: Rank candidates
ranked_candidates = rank_candidates(candidates, parsed_job_dict)

# Step 3: Return top K results
top_results = ranked_candidates[:request.top_k]
```

## Error Handling

The module includes comprehensive error handling:

1. **Invalid Weights**: Automatically normalizes weights if they don't sum to 1.0
2. **Missing Fields**: Handles candidates with missing metadata gracefully
3. **Empty Input**: Returns empty list if no candidates provided
4. **Per-Candidate Errors**: Continues ranking if individual candidate fails
5. **Logging**: All errors logged with full context

## RankingResult Class

Internal class representing a single ranked candidate:

**Fields:**
- `resume_id`: Unique identifier
- `semantic_score`: Semantic similarity (0-100)
- `skill_score`: Skill overlap (0-100)
- `final_score`: Weighted combination (0-100)
- `matched_skills`: List of matched skills
- `missing_skills`: List of missing required skills
- `explanation`: Human-readable explanation
- `metadata`: Candidate metadata
- `rank`: Position in rankings

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Rank 100 candidates | ~2-3s | Includes skill scoring for each |
| Calculate statistics | <100ms | Summary stats computation |
| Sort by criteria | <50ms | Re-ranking operation |
| Build explanation | <10ms | Per candidate |

## Advanced Features

### 1. Weighted Scoring
Adjust semantic/skill weight ratio based on job type:
- Technical roles: 60% skill + 40% semantic
- Leadership roles: 40% skill + 60% semantic
- Balanced approach: 50% + 50%

### 2. Tier-Based Rankings
Use score thresholds to create tiers:
```python
if score >= 85:
    tier = "Elite"
elif score >= 75:
    tier = "Strong"
elif score >= 65:
    tier = "Good"
```

### 3. Missing Skills Analysis
Track skill gaps for each candidate:
```python
for candidate in ranked_candidates:
    if candidate['missing_skills']:
        training_needed = candidate['missing_skills']
```

## Testing

Run the example script to test all features:

```bash
python examples/ranking_agent_example.py
```

Examples included:
1. Basic ranking
2. Custom weights
3. Statistics
4. Sort by criteria
5. Score interpretation
6. Missing requirements analysis
7. Metadata access
8. Error handling

## Integration Points

The ranking agent integrates with:

1. **Skill Scorer** (`src/agents/skill_scorer.py`)
   - Uses `compute_skill_overlap_score()` for skill matching

2. **Vector Store** (`src/embeddings/vector_store.py`)
   - Receives candidates with `score` field (semantic similarity)

3. **Job Parser** (`src/retrieval/job_parser.py`)
   - Receives parsed job with `required_skills`, `preferred_skills`

4. **API Main** (`src/api/main.py`)
   - Used in `/api/v1/match` endpoint for final ranking

## Files

- **src/agents/ranking_agent.py** (403 lines)
  - Core ranking implementation
  - RankingResult class
  - Utility functions

- **examples/ranking_agent_example.py** (295 lines)
  - 8 comprehensive examples
  - Usage patterns
  - Error handling demonstrations

---

**Version:** 1.0.0
**Last Updated:** March 2024
**Status:** Production Ready ✅
