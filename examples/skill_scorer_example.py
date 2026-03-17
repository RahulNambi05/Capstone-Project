"""
Example usage of the skill scorer module.
Demonstrates semantic skill matching and overlap scoring.
"""
import logging
from src.agents.skill_scorer import compute_skill_overlap_score, SkillScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Sample candidate skill sets
BACKEND_CANDIDATE = [
    "Python", "Django", "PostgreSQL", "Docker", "AWS", "REST APIs",
    "Git", "Linux", "Redis", "Microservices", "FastAPI"
]

FRONTEND_CANDIDATE = [
    "JavaScript", "React", "TypeScript", "CSS", "HTML", "Redux",
    "Jest", "Webpack", "Node.js", "Git", "Responsive Design"
]

DATA_SCIENCE_CANDIDATE = [
    "Python", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
    "SQL", "AWS", "Jupyter", "Matplotlib", "Statistics", "R"
]

DEVOPS_CANDIDATE = [
    "Kubernetes", "Docker", "Jenkins", "Terraform", "AWS", "Linux",
    "Ansible", "Python", "GitLab", "Prometheus", "Git", "Bash"
]

# Job requirements
BACKEND_JOB_REQUIRED = [
    "Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "REST APIs", "AWS"
]

BACKEND_JOB_PREFERRED = [
    "GraphQL", "Redis", "Kafka", "RabbitMQ", "FastAPI", "Microservices"
]

FRONTEND_JOB_REQUIRED = [
    "JavaScript", "React", "TypeScript", "CSS", "Git", "Testing"
]

FRONTEND_JOB_PREFERRED = [
    "Next.js", "Redux", "GraphQL", "Responsive Design", "HTML5"
]

DATA_SCIENCE_JOB_REQUIRED = [
    "Python", "Machine Learning", "TensorFlow", "SQL", "Statistics"
]

DATA_SCIENCE_JOB_PREFERRED = [
    "Deep Learning", "NLP", "Computer Vision", "PyTorch", "Spark", "AWS"
]


def example_single_scoring():
    """Example 1: Score a single candidate against a job."""
    print("\n" + "=" * 70)
    print("Example 1: Single Candidate Skill Scoring")
    print("=" * 70)

    print("\nScoring Backend Candidate against Backend Job...\n")

    try:
        result = compute_skill_overlap_score(
            candidate_skills=BACKEND_CANDIDATE,
            required_skills=BACKEND_JOB_REQUIRED,
            preferred_skills=BACKEND_JOB_PREFERRED
        )

        print(f"Overall Score: {result.overall_score}/100")
        print(f"  Required Skills Match: {result.required_match_pct}%")
        print(f"  Preferred Skills Match: {result.preferred_match_pct}%\n")

        print(f"Matched Skills ({len(result.matched_skills)}):")
        for skill in result.matched_skills:
            print(f"  ✓ {skill}")

        print(f"\nMissing Required Skills ({len(result.missing_required_skills)}):")
        for skill in result.missing_required_skills:
            print(f"  ✗ {skill}")

        print(f"\nMissing Preferred Skills ({len(result.missing_preferred_skills)}):")
        for skill in result.missing_preferred_skills:
            print(f"  ◇ {skill}")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


def example_multiple_candidates():
    """Example 2: Score multiple candidates for same job."""
    print("\n" + "=" * 70)
    print("Example 2: Multiple Candidates Scoring")
    print("=" * 70)

    candidates = [
        {"name": "Backend Dev", "skills": BACKEND_CANDIDATE},
        {"name": "Frontend Dev", "skills": FRONTEND_CANDIDATE},
        {"name": "Full-Stack Dev", "skills": BACKEND_CANDIDATE + FRONTEND_CANDIDATE},
    ]

    print(f"\nScoring {len(candidates)} candidates for Backend position...\n")

    try:
        scorer = SkillScorer()

        scored = scorer.score_batch(
            candidates=candidates,
            required_skills=BACKEND_JOB_REQUIRED,
            preferred_skills=BACKEND_JOB_PREFERRED
        )

        # Sort by score
        scored.sort(key=lambda x: x["skill_score"]["overall_score"], reverse=True)

        print(f"{'Rank':<6} {'Candidate':<20} {'Score':<8} {'Required':<12} {'Preferred':<12}")
        print(f"{'-' * 60}")

        for i, candidate in enumerate(scored, 1):
            score = candidate["skill_score"]
            print(
                f"{i:<6} {candidate['name']:<20} "
                f"{score['overall_score']:<8.2f} "
                f"{score['required_match_pct']:<12.1f}% "
                f"{score['preferred_match_pct']:<12.1f}%"
            )

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


def example_cross_role_scoring():
    """Example 3: Score candidates across different roles."""
    print("\n" + "=" * 70)
    print("Example 3: Cross-Role Candidate Scoring")
    print("=" * 70)

    candidates = [
        ("Backend Dev", BACKEND_CANDIDATE),
        ("Frontend Dev", FRONTEND_CANDIDATE),
        ("Data Scientist", DATA_SCIENCE_CANDIDATE),
        ("DevOps Engineer", DEVOPS_CANDIDATE),
    ]

    jobs = [
        ("Backend", BACKEND_JOB_REQUIRED, BACKEND_JOB_PREFERRED),
        ("Frontend", FRONTEND_JOB_REQUIRED, FRONTEND_JOB_PREFERRED),
        ("Data Science", DATA_SCIENCE_JOB_REQUIRED, DATA_SCIENCE_JOB_PREFERRED),
    ]

    print("\nCross-role compatibility matrix:\n")

    # Create header
    print(f"{'Candidate':<20}", end="")
    for job_name, _, _ in jobs:
        print(f"{job_name:<12}", end="")
    print()
    print(f"{'-' * 70}")

    # Score each candidate for each job
    for candidate_name, candidate_skills in candidates:
        print(f"{candidate_name:<20}", end="")

        for job_name, req_skills, pref_skills in jobs:
            try:
                result = compute_skill_overlap_score(
                    candidate_skills=candidate_skills,
                    required_skills=req_skills,
                    preferred_skills=pref_skills
                )
                print(f"{result.overall_score:<12.1f}", end="")
            except Exception as e:
                print(f"{'ERROR':<12}", end="")

        print()

    print("\nNote: Higher scores indicate better role fit.")


def example_semantic_matching():
    """Example 4: Demonstrate semantic matching capabilities."""
    print("\n" + "=" * 70)
    print("Example 4: Semantic Skill Matching")
    print("=" * 70)

    print("\nDemonstrating semantic similarity in skill matching...\n")

    # Candidate with slightly different skill names
    candidate_skills = [
        "Python Programming",
        "Relational Databases",
        "Container Technology",
        "Cloud Computing",
        "API Development"
    ]

    # Job requirements with different wording
    required_skills = [
        "Python",
        "PostgreSQL",
        "Docker",
        "AWS",
        "REST APIs"
    ]

    print(f"Candidate Skills: {candidate_skills}")
    print(f"Job Requirements: {required_skills}\n")

    try:
        result = compute_skill_overlap_score(
            candidate_skills=candidate_skills,
            required_skills=required_skills,
            preferred_skills=[]
        )

        print(f"Match Score: {result.overall_score}%\n")

        print("Detailed Matches:")
        for skill, details in result.match_details["required"].items():
            similarity = details["similarity"]
            matched = details["candidate_skill"]
            is_match = details["is_match"]

            status = "✓" if is_match else "✗"
            print(f"  {status} '{skill}' → '{matched}' (similarity: {similarity:.4f})")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


def example_threshold_analysis():
    """Example 5: Analyze impact of similarity threshold."""
    print("\n" + "=" * 70)
    print("Example 5: Similarity Threshold Analysis")
    print("=" * 70)

    candidate_skills = [
        "Python development",
        "Web frameworks",
        "Relational databases",
        "Container orchestration"
    ]

    job_skills = [
        "Python",
        "Django",
        "PostgreSQL",
        "Kubernetes"
    ]

    thresholds = [0.5, 0.6, 0.7, 0.75, 0.8, 0.9]

    print(f"\nCandidate Skills: {candidate_skills}")
    print(f"Job Skills: {job_skills}\n")

    print(f"{'Threshold':<12} {'Score':<10} {'Matched':<10} {'Missing':<10}")
    print(f"{'-' * 45}")

    for threshold in thresholds:
        try:
            scorer = SkillScorer(similarity_threshold=threshold)
            result = scorer.compute_skill_overlap_score(
                candidate_skills=candidate_skills,
                required_skills=job_skills,
                preferred_skills=[]
            )

            matched_count = result.matched_required_count
            missing_count = result.total_required_count - matched_count

            print(
                f"{threshold:<12.2f} {result.overall_score:<10.1f} "
                f"{matched_count:<10} {missing_count:<10}"
            )

        except Exception as e:
            logger.error(f"Error with threshold {threshold}: {e}")


def example_detailed_report():
    """Example 6: Generate detailed matching report."""
    print("\n" + "=" * 70)
    print("Example 6: Detailed Matching Report")
    print("=" * 70)

    print(f"\nGenerating report for Backend Candidate vs Backend Job...\n")

    try:
        result = compute_skill_overlap_score(
            candidate_skills=BACKEND_CANDIDATE,
            required_skills=BACKEND_JOB_REQUIRED,
            preferred_skills=BACKEND_JOB_PREFERRED
        )

        print("=== SKILL MATCH REPORT ===\n")

        print("OVERALL ASSESSMENT")
        print(f"  Overall Score: {result.overall_score}/100")
        print(f"  Assessment: ", end="")

        if result.overall_score >= 80:
            print("EXCELLENT MATCH")
        elif result.overall_score >= 60:
            print("GOOD MATCH")
        elif result.overall_score >= 40:
            print("ADEQUATE MATCH")
        else:
            print("POOR MATCH")

        print(f"\nREQUIREMENT COVERAGE")
        print(f"  Required Skills: {result.matched_required_count}/{result.total_required_count} "
              f"({result.required_match_pct}%)")
        print(f"  Preferred Skills: {result.matched_preferred_count}/{result.total_preferred_count} "
              f"({result.preferred_match_pct}%)")

        print(f"\nSTRENGTHS (Matched)")
        for skill in sorted(result.matched_skills)[:10]:
            print(f"  ✓ {skill}")

        if result.missing_required_skills:
            print(f"\nGAPS (Missing Required)")
            for skill in result.missing_required_skills:
                print(f"  ✗ {skill}")

        if result.missing_preferred_skills:
            print(f"\nNICE-TO-HAVE (Missing Preferred)")
            for skill in result.missing_preferred_skills[:5]:
                print(f"  ◇ {skill}")

        print(f"\n=== END REPORT ===")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


def example_weighted_scoring():
    """Example 7: Different weight combinations."""
    print("\n" + "=" * 70)
    print("Example 7: Weight Configuration Impact")
    print("=" * 70)

    print(f"\nImpact of different weight configurations...\n")

    weights = [
        (0.7, 0.3, "Standard (70% required, 30% preferred)"),
        (0.8, 0.2, "Strict (80% required, 20% preferred)"),
        (0.5, 0.5, "Balanced (50% required, 50% preferred)"),
        (0.9, 0.1, "Very Strict (90% required, 10% preferred)"),
    ]

    try:
        scorer = SkillScorer()

        print(f"{'Configuration':<40} {'Score':<10}")
        print(f"{'-' * 55}")

        for req_weight, pref_weight, description in weights:
            result = scorer.compute_skill_overlap_score(
                candidate_skills=BACKEND_CANDIDATE,
                required_skills=BACKEND_JOB_REQUIRED,
                preferred_skills=BACKEND_JOB_PREFERRED,
                required_weight=req_weight,
                preferred_weight=pref_weight
            )

            print(f"{description:<40} {result.overall_score:<10.1f}")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Skill Scorer Examples")
    print("=" * 70)
    print("\nNote: This example uses sentence-transformers for semantic matching.")
    print("First run will download the embedding model (~80MB).\n")

    try:
        # Run examples
        example_single_scoring()
        example_multiple_candidates()
        example_semantic_matching()
        example_cross_role_scoring()
        example_detailed_report()
        example_weighted_scoring()
        example_threshold_analysis()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        print("\nMake sure sentence-transformers is installed:")
        print("  pip install sentence-transformers")
