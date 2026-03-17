"""
Example usage of the ranking agent module.
Demonstrates scoring and ranking candidates against job descriptions.
"""
import logging
from src.agents.ranking_agent import (
    rank_candidates,
    get_ranking_statistics,
    sort_candidates_by_criteria,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Sample data
SAMPLE_CANDIDATES = [
    {
        "resume_id": "resume_001",
        "score": 0.92,  # Semantic similarity from vector store (0-1)
        "metadata": {
            "top_skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS"],
            "experience_level": "senior",
            "role_category": "backend",
            "education": "bachelors",
        },
    },
    {
        "resume_id": "resume_042",
        "score": 0.89,
        "metadata": {
            "top_skills": ["Python", "FastAPI", "PostgreSQL", "Kubernetes", "AWS"],
            "experience_level": "senior",
            "role_category": "backend",
            "education": "masters",
        },
    },
    {
        "resume_id": "resume_087",
        "score": 0.76,
        "metadata": {
            "top_skills": ["Python", "PostgreSQL", "Docker", "AWS"],
            "experience_level": "mid",
            "role_category": "backend",
            "education": "bachelors",
        },
    },
    {
        "resume_id": "resume_105",
        "score": 0.68,
        "metadata": {
            "top_skills": ["JavaScript", "React", "Node.js", "MongoDB"],
            "experience_level": "senior",
            "role_category": "frontend",
            "education": "bachelors",
        },
    },
]

SAMPLE_PARSED_JD = {
    "required_skills": [
        "Python",
        "Django",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "Kubernetes",
        "REST APIs",
        "Microservices",
        "AWS",
    ],
    "preferred_skills": [
        "GraphQL",
        "Kafka",
        "RabbitMQ",
        "Kubernetes certification",
    ],
}


def example_basic_ranking():
    """Example 1: Basic candidate ranking."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Candidate Ranking")
    print("=" * 70)

    print(f"\nInput: {len(SAMPLE_CANDIDATES)} candidates")
    print(f"Required Skills: {', '.join(SAMPLE_PARSED_JD['required_skills'][:5])}...")
    print(f"Preferred Skills: {', '.join(SAMPLE_PARSED_JD['preferred_skills'])}\n")

    # Rank candidates
    ranked = rank_candidates(SAMPLE_CANDIDATES, SAMPLE_PARSED_JD)

    print(f"Ranked: {len(ranked)} candidates\n")

    # Display top 3
    for candidate in ranked[:3]:
        print(f"\n{candidate['rank']}. {candidate['resume_id']}")
        print(f"   Final Score: {candidate['final_score']:.1f}/100")
        print(f"   Semantic: {candidate['semantic_score']:.1f} | Skill: {candidate['skill_score']:.1f}")
        print(f"   Matched Skills: {', '.join(candidate['matched_skills'][:3])}")
        print(f"   Explanation: {candidate['explanation']}")


def example_custom_weights():
    """Example 2: Ranking with custom weights."""
    print("\n" + "=" * 70)
    print("Example 2: Custom Weights (Skill-focused: 70/30)")
    print("=" * 70)

    print(f"\nInput: {len(SAMPLE_CANDIDATES)} candidates")
    print(f"Weights: 70% skill + 30% semantic\n")

    # Rank with skill emphasis (70% skill, 30% semantic)
    ranked = rank_candidates(
        SAMPLE_CANDIDATES,
        SAMPLE_PARSED_JD,
        semantic_weight=0.3,
        skill_weight=0.7,
    )

    print(f"Ranked: {len(ranked)} candidates\n")

    for candidate in ranked[:3]:
        print(f"\n{candidate['rank']}. {candidate['resume_id']}")
        print(f"   Final Score: {candidate['final_score']:.1f}/100")
        print(f"   Skills: {candidate['skill_score']:.1f}% | Semantic: {candidate['semantic_score']:.1f}")


def example_ranking_statistics():
    """Example 3: Ranking statistics."""
    print("\n" + "=" * 70)
    print("Example 3: Ranking Statistics")
    print("=" * 70)

    ranked = rank_candidates(SAMPLE_CANDIDATES, SAMPLE_PARSED_JD)
    stats = get_ranking_statistics(ranked)

    print(f"\nStatistics:")
    print(f"  Total Candidates: {stats['total_candidates']}")
    print(f"  Average Final Score: {stats['avg_final_score']:.1f}/100")
    print(f"  Average Semantic Score: {stats['avg_semantic_score']:.1f}/100")
    print(f"  Average Skill Score: {stats['avg_skill_score']:.1f}%")
    print(f"  Top Score: {stats['top_score']:.1f}/100")
    print(f"  Bottom Score: {stats['bottom_score']:.1f}/100")
    print(f"  Median Score: {stats['median_score']:.1f}/100")


def example_sort_by_criteria():
    """Example 4: Sorting by different criteria."""
    print("\n" + "=" * 70)
    print("Example 4: Sorting by Different Criteria")
    print("=" * 70)

    ranked = rank_candidates(SAMPLE_CANDIDATES, SAMPLE_PARSED_JD)

    print("\nDefault Sort (by final_score, descending):")
    for candidate in ranked[:3]:
        print(f"  {candidate['rank']}. {candidate['resume_id']}: {candidate['final_score']:.1f}")

    print("\nSort by skill_score:")
    sorted_by_skill = sort_candidates_by_criteria(ranked, sort_by="skill_score")
    for candidate in sorted_by_skill[:3]:
        print(f"  {candidate['rank']}. {candidate['resume_id']}: {candidate['skill_score']:.1f}%")

    print("\nSort by semantic_score:")
    sorted_by_semantic = sort_candidates_by_criteria(ranked, sort_by="semantic_score")
    for candidate in sorted_by_semantic[:3]:
        print(f"  {candidate['rank']}. {candidate['resume_id']}: {candidate['semantic_score']:.1f}")


def example_score_interpretation():
    """Example 5: Understanding the scores."""
    print("\n" + "=" * 70)
    print("Example 5: Score Interpretation Guide")
    print("=" * 70)

    ranked = rank_candidates(SAMPLE_CANDIDATES, SAMPLE_PARSED_JD)

    print("\nScore Ranges:")
    print("  90-100: Excellent fit - candidate has most required skills")
    print("  80-89:  Very good fit - strong semantic match and skill coverage")
    print("  70-79:  Good fit - many required skills but some missing")
    print("  60-69:  Acceptable fit - some relevant skills")
    print("  <60:    Weak fit - significant gaps\n")

    print("Candidate Assessments:")
    for candidate in ranked:
        score = candidate["final_score"]
        if score >= 85:
            assessment = "Excellent fit"
        elif score >= 75:
            assessment = "Very good fit"
        elif score >= 65:
            assessment = "Good fit"
        elif score >= 50:
            assessment = "Acceptable fit"
        else:
            assessment = "Weak fit"

        print(f"\n  {candidate['rank']}. {candidate['resume_id']}: {score:.1f} - {assessment}")
        print(f"     {candidate['explanation']}")


def example_missing_requirements():
    """Example 6: Analyzing missing requirements."""
    print("\n" + "=" * 70)
    print("Example 6: Missing Requirements Analysis")
    print("=" * 70)

    ranked = rank_candidates(SAMPLE_CANDIDATES, SAMPLE_PARSED_JD)

    print(f"\nRequired skills needed: {len(SAMPLE_PARSED_JD['required_skills'])}")
    print(f"Required: {', '.join(SAMPLE_PARSED_JD['required_skills'][:5])}...\n")

    for candidate in ranked[:3]:
        print(f"\n{candidate['rank']}. {candidate['resume_id']}")
        print(f"   Matched: {len(candidate['matched_skills'])} skills")
        if candidate["missing_skills"]:
            print(f"   Missing: {', '.join(candidate['missing_skills'][:3])}")
            if len(candidate["missing_skills"]) > 3:
                print(f"           +{len(candidate['missing_skills']) - 3} more")
        else:
            print(f"   Missing: None (perfect match!)")


def example_metadata_access():
    """Example 7: Accessing candidate metadata."""
    print("\n" + "=" * 70)
    print("Example 7: Candidate Metadata")
    print("=" * 70)

    ranked = rank_candidates(SAMPLE_CANDIDATES, SAMPLE_PARSED_JD)

    print(f"\nTop candidate metadata:\n")
    top_candidate = ranked[0]
    print(f"Resume ID: {top_candidate['resume_id']}")
    print(f"Experience Level: {top_candidate['metadata'].get('experience_level', 'N/A')}")
    print(f"Role Category: {top_candidate['metadata'].get('role_category', 'N/A')}")
    print(f"Education: {top_candidate['metadata'].get('education', 'N/A')}")
    print(f"Top Skills: {', '.join(top_candidate['metadata'].get('top_skills', [])[:5])}")


def example_error_handling():
    """Example 8: Error handling."""
    print("\n" + "=" * 70)
    print("Example 8: Error Handling")
    print("=" * 70)

    # Test with empty candidates
    print("\nTest 1: Empty candidates list")
    result = rank_candidates([], SAMPLE_PARSED_JD)
    print(f"  Result: {len(result)} candidates (expected: 0)")

    # Test with None parsed_jd
    print("\nTest 2: None parsed_jd")
    result = rank_candidates(SAMPLE_CANDIDATES, {})
    print(f"  Result: {len(result)} candidates ranked")

    # Test with missing fields
    print("\nTest 3: Candidate with missing fields")
    incomplete_candidate = {"resume_id": "incomplete_001"}
    result = rank_candidates([incomplete_candidate], SAMPLE_PARSED_JD)
    if result:
        print(f"  Handled gracefully: {result[0]['resume_id']} ranked")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Ranking Agent Examples")
    print("=" * 70)

    try:
        # Run examples
        example_basic_ranking()
        example_custom_weights()
        example_ranking_statistics()
        example_sort_by_criteria()
        example_score_interpretation()
        example_missing_requirements()
        example_metadata_access()
        example_error_handling()

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\nError: {e}")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")
