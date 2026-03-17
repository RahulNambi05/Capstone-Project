"""
Candidate retrieval module for finding matching resumes for a job description.
Uses parsed job descriptions to search the vector store and rank candidates.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document

from src.retrieval.job_parser import ParsedJobDescription
from src.embeddings.vector_store import semantic_search, get_vector_store, init_vector_store

logger = logging.getLogger(__name__)


class CandidateRetriever:
    """
    Retrieves and ranks candidate resumes matching a job description.
    """

    def __init__(self):
        """Initialize the CandidateRetriever."""
        logger.info("CandidateRetriever initialized")

    def retrieve_candidates(
        self,
        parsed_jd: ParsedJobDescription,
        top_k: int = 10,
        apply_experience_filter: bool = True,
        apply_role_filter: bool = True,
        deduplicate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve candidate resumes matching a job description.

        Strategy:
        1. Retrieve top_k*3 results using ONLY semantic similarity (no metadata filters)
        2. Deduplicate by resume_id, keeping highest-scoring chunk
        3. Return top_k final candidates ranked by semantic score

        Args:
            parsed_jd: ParsedJobDescription model with extracted job info
            top_k: Number of candidates to return (default: 10)
            apply_experience_filter: Ignored - no metadata filtering used
            apply_role_filter: Ignored - no metadata filtering used
            deduplicate: Keep only highest-scoring chunk per resume (default: True)

        Returns:
            List of candidate dicts with resume_id, resume_text, score, metadata, etc.

        Raises:
            ValueError: If parsed_jd is invalid or top_k is invalid
        """
        if not isinstance(parsed_jd, ParsedJobDescription):
            raise ValueError("parsed_jd must be a ParsedJobDescription instance")

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer")

        try:
            # Step 0: Ensure vector store is available (startup should init; keep a safe fallback)
            vector_store = get_vector_store()
            if vector_store is None:
                init_vector_store()
                vector_store = get_vector_store()
                if vector_store is None:
                    raise RuntimeError("Vector store failed to initialize")

            # Step 1: Build rich query string from job description
            query_string = self._build_query_string(parsed_jd)
            logger.info(f"Built search query: {query_string[:150]}...")

            # Step 2: Retrieve candidates using ONLY semantic similarity (no metadata filters)
            # Skip all metadata filtering - ChromaDB has 38063+ docs, most metadata is "other"
            # Request top_k*3 to account for deduplication
            search_top_k = top_k * 3 if deduplicate else top_k

            logger.info(
                f"Retrieving top {search_top_k} results using semantic search (NO metadata filters)"
            )
            search_results = semantic_search(
                query=query_string,
                top_k=search_top_k,
                filters=None  # IMPORTANT: No metadata filtering
            )

            logger.info(f"Semantic search returned {len(search_results)} results from {search_top_k} requested")

            if not search_results:
                logger.warning(
                    f"No candidates found via semantic search for: {parsed_jd.job_summary}"
                )
                return []

            # Log score distribution for debugging
            if search_results:
                scores = [score for _, score in search_results]
                logger.info(
                    f"Score distribution - Min: {min(scores):.4f}, Max: {max(scores):.4f}, "
                    f"Avg: {sum(scores)/len(scores):.4f}"
                )

            # Step 3: Process and deduplicate results
            candidates = self._process_results(
                search_results,
                parsed_jd,
                top_k,
                deduplicate
            )

            logger.info(
                f"Retrieved {len(candidates)} candidates after deduplication "
                f"from {len(search_results)} semantic search results"
            )
            return candidates

        except Exception as e:
            logger.error(f"Error retrieving candidates: {str(e)}", exc_info=True)
            raise

    def _build_query_string(self, parsed_jd: ParsedJobDescription) -> str:
        """
        Build a rich query string from job description components.

        Args:
            parsed_jd: ParsedJobDescription model

        Returns:
            Rich query string combining skills and summary
        """
        query_parts = []

        # Add job summary
        if parsed_jd.job_summary:
            query_parts.append(parsed_jd.job_summary)

        # Add required skills with emphasis
        if parsed_jd.required_skills:
            skills_str = " ".join(parsed_jd.required_skills[:10])  # Top 10 skills
            query_parts.append(f"Required skills: {skills_str}")

        # Add preferred skills
        if parsed_jd.preferred_skills:
            pref_skills_str = " ".join(parsed_jd.preferred_skills[:5])  # Top 5 preferred
            query_parts.append(f"Preferred: {pref_skills_str}")

        # Add experience level
        if parsed_jd.experience_level:
            query_parts.append(f"{parsed_jd.experience_level} level")

        # Add role category
        if parsed_jd.role_category:
            query_parts.append(parsed_jd.role_category)

        query_string = " ".join(query_parts)

        logger.debug(f"Built query string: {query_string[:100]}...")
        return query_string

    def _process_results(
        self,
        search_results: List[Tuple[Document, float]],
        parsed_jd: ParsedJobDescription,
        top_k: int,
        deduplicate: bool
    ) -> List[Dict[str, Any]]:
        """
        Process search results and deduplicate by resume_id.

        Deduplication keeps the highest-scoring chunk for each resume,
        then returns the top_k candidates by score.

        Args:
            search_results: List of (Document, score) tuples from semantic search
            parsed_jd: The job description being matched
            top_k: Number of final candidates to return
            deduplicate: Whether to deduplicate by resume_id (default: True)

        Returns:
            List of processed candidate dictionaries
        """
        logger.debug(f"Processing {len(search_results)} search results (deduplicate={deduplicate})")

        # Deduplicate by resume_id, keeping highest-scoring chunk per resume
        if deduplicate:
            resume_groups = {}

            for doc, score in search_results:
                resume_id = doc.metadata.get("resume_id", "unknown")

                # Keep only the highest-scoring chunk for each resume
                if resume_id not in resume_groups:
                    resume_groups[resume_id] = {
                        "doc": doc,
                        "score": score,
                        "chunk_count": 1
                    }
                else:
                    resume_groups[resume_id]["chunk_count"] += 1
                    # Update if this chunk has higher score
                    if score > resume_groups[resume_id]["score"]:
                        resume_groups[resume_id]["doc"] = doc
                        resume_groups[resume_id]["score"] = score

            # Convert to list and sort by score (descending)
            deduplicated_results = [
                (data["doc"], data["score"])
                for data in resume_groups.values()
            ]
            deduplicated_results.sort(key=lambda x: x[1], reverse=True)

            logger.info(
                f"Deduplicated {len(search_results)} chunks from {len(deduplicated_results)} unique resumes "
                f"(avg {len(search_results)/len(deduplicated_results):.1f} chunks per resume)"
            )

            # Take top_k
            final_results = deduplicated_results[:top_k]
            logger.debug(f"Selected top {len(final_results)}/{len(deduplicated_results)} candidates")
        else:
            final_results = search_results[:top_k]
            logger.debug(f"No deduplication - returning top {len(final_results)} results")

        # Build candidate dictionaries
        candidates = []

        for doc, score in final_results:
            metadata = doc.metadata or {}

            # Calculate matched skills
            matched_skills = self._calculate_matched_skills(
                doc.page_content,
                parsed_jd.required_skills + parsed_jd.preferred_skills
            )

            candidate = {
                "resume_id": metadata.get("resume_id", "unknown"),
                "resume_text": doc.page_content,
                "category": metadata.get("category", "Uncategorized"),
                "score": round(score, 4),
                "metadata": {
                    "experience_level": metadata.get("experience_level", "unknown"),
                    "role_category": metadata.get("role_category", "unknown"),
                    "experience_years": metadata.get("experience_years", 0),
                    "education": metadata.get("education", "unknown"),
                    "top_skills": metadata.get("top_skills", []),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "chunk_count": metadata.get("chunk_count", 1),
                },
                "matched_skills": matched_skills,
                "top_scores_in_chunks": score
            }

            candidates.append(candidate)

        logger.debug(f"Built {len(candidates)} candidate dicts with metadata and matched skills")
        return candidates

    def _calculate_matched_skills(
        self,
        resume_text: str,
        job_skills: List[str]
    ) -> List[str]:
        """
        Calculate which job skills are mentioned in the resume.

        Args:
            resume_text: The resume text content
            job_skills: List of skills from the job description

        Returns:
            List of matched skills
        """
        if not job_skills:
            return []

        matched = []
        resume_lower = resume_text.lower()

        for skill in job_skills:
            skill_lower = skill.lower()
            if skill_lower in resume_lower:
                matched.append(skill)

        return matched[:10]  # Return top 10 matched skills

    def retrieve_for_multiple_jobs(
        self,
        parsed_jobs: List[ParsedJobDescription],
        top_k_per_job: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve candidates for multiple job descriptions.

        Args:
            parsed_jobs: List of ParsedJobDescription instances
            top_k_per_job: Number of candidates per job (default: 10)

        Returns:
            Dictionary mapping job descriptions to candidate lists
        """
        results = {}
        failed_count = 0

        for idx, parsed_jd in enumerate(parsed_jobs):
            try:
                job_key = f"{parsed_jd.role_category}_{idx}"
                candidates = self.retrieve_candidates(parsed_jd, top_k=top_k_per_job)
                results[job_key] = {
                    "job_summary": parsed_jd.job_summary,
                    "required_skills": parsed_jd.required_skills,
                    "experience_level": parsed_jd.experience_level,
                    "role_category": parsed_jd.role_category,
                    "candidates": candidates,
                    "candidate_count": len(candidates)
                }
            except Exception as e:
                logger.error(f"Error processing job at index {idx}: {str(e)}")
                failed_count += 1
                continue

        logger.info(
            f"Retrieved candidates for {len(results)}/{len(parsed_jobs)} jobs. "
            f"Failed: {failed_count}"
        )

        return results


def retrieve_candidates(
    parsed_jd: ParsedJobDescription,
    top_k: int = 10,
    apply_filters: bool = True,
    deduplicate: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieve candidates for a job description using semantic search.

    Implements the retrieval strategy:
    1. Uses ONLY semantic similarity search (ignores apply_filters parameter)
    2. Retrieves top_k*3 results from ChromaDB
    3. Deduplicates by resume_id, keeping highest-scoring chunk
    4. Returns top_k final candidates

    Args:
        parsed_jd: ParsedJobDescription with job details
        top_k: Number of candidates to return (default: 10)
        apply_filters: IGNORED - no metadata filtering used
        deduplicate: Deduplicate by resume_id (default: True)

    Returns:
        List of candidate dictionaries with resume_id, score, metadata, etc.
    """
    logger.debug(
        f"retrieve_candidates() call - top_k={top_k}, deduplicate={deduplicate} "
        f"(apply_filters={apply_filters} ignored)"
    )

    retriever = CandidateRetriever()
    return retriever.retrieve_candidates(
        parsed_jd=parsed_jd,
        top_k=top_k,
        apply_experience_filter=False,  # Ignore - use semantic search only
        apply_role_filter=False,  # Ignore - use semantic search only
        deduplicate=deduplicate
    )
