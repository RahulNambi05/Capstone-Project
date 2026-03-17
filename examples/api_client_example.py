"""
Example usage of the Resume Matching System API.
Demonstrates all endpoints using the requests library.
"""
import requests
import json
from typing import Dict, Any

# API base URL
API_URL = "http://localhost:8000"

# Sample job description
SAMPLE_JOB = """
Senior Backend Engineer - Python

We are looking for an experienced Senior Backend Engineer to join our platform team.

Requirements:
- 7+ years of professional software development experience
- Expert-level proficiency in Python
- Strong experience with Django or FastAPI web frameworks
- Expertise in PostgreSQL and relational databases
- Experience with Docker and Kubernetes
- Strong understanding of REST APIs and microservices architecture
- AWS cloud platform experience

Preferred:
- GraphQL experience
- Event-driven architectures (Kafka, RabbitMQ)
- Kubernetes certification
"""


def print_response(response: requests.Response) -> None:
    """Pretty print a response."""
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)


def example_health_check() -> None:
    """Example 1: Health check."""
    print("\n" + "=" * 70)
    print("Example 1: Health Check")
    print("=" * 70)

    try:
        response = requests.get(f"{API_URL}/health")
        print(f"\nStatus Code: {response.status_code}")
        print("Response:")
        print_response(response)

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure server is running:")
        print(f"  python -m src.api.main")


def example_api_root() -> None:
    """Example 2: API root endpoints."""
    print("\n" + "=" * 70)
    print("Example 2: API Root Endpoints")
    print("=" * 70)

    try:
        response = requests.get(f"{API_URL}/")
        print(f"\nStatus Code: {response.status_code}")
        print("Root Endpoint:")
        print_response(response)

        response = requests.get(f"{API_URL}/api/v1")
        print("\nAPI v1 Endpoint:")
        print_response(response)

    except requests.exceptions.ConnectionError as e:
        print(f"Error: {e}")


def example_ingestion() -> None:
    """Example 3: Trigger resume ingestion."""
    print("\n" + "=" * 70)
    print("Example 3: Resume Ingestion")
    print("=" * 70)

    payload = {
        "csv_path": "data/resumes/resume_dataset.csv"
    }

    print(f"\nRequest Payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(f"{API_URL}/api/v1/ingest", json=payload)
        print(f"\nStatus Code: {response.status_code}")
        print("Response:")
        print_response(response)

    except requests.exceptions.ConnectionError as e:
        print(f"Error: {e}")
        print("\nNote: Make sure:")
        print("  1. API server is running: python -m src.api.main")
        print("  2. CSV file exists at: data/resumes/resume_dataset.csv")


def example_job_matching() -> None:
    """Example 4: Match job with candidates."""
    print("\n" + "=" * 70)
    print("Example 4: Job Candidate Matching")
    print("=" * 70)

    payload = {
        "job_description": SAMPLE_JOB,
        "top_k": 5,
        "filters": {
            "experience_level": "senior",
            "role_category": "backend"
        }
    }

    print(f"\nRequest:")
    print(f"  Job: Senior Backend Engineer")
    print(f"  Top K: 5")
    print(f"  Filters: experience_level=senior, role_category=backend")

    try:
        response = requests.post(f"{API_URL}/api/v1/match", json=payload)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nQuery Summary: {data.get('query_summary')}")
            print(f"Total Found: {data.get('total_found')}")
            print(f"Execution Time: {data.get('execution_time'):.2f}s")

            print(f"\nTopCandidates:")
            for candidate in data.get('candidates', [])[:3]:
                print(f"\n  {candidate['rank']}. {candidate['resume_id']}")
                print(f"     Overall Score: {candidate['overall_score']:.1f}/100")
                print(f"     Semantic: {candidate['semantic_score']:.2f} | Skill: {candidate['skill_score']:.1f}")
                print(f"     Level: {candidate['experience_level']} | Role: {candidate['role_category']}")
                print(f"     Explanation: {candidate['explanation']}")
        else:
            print("Response:")
            print_response(response)

    except requests.exceptions.ConnectionError as e:
        print(f"Error: {e}")
        print("\nNote: Make sure vector store is populated by running ingestion first.")


def example_statistics() -> None:
    """Example 5: Get vector store statistics."""
    print("\n" + "=" * 70)
    print("Example 5: Vector Store Statistics")
    print("=" * 70)

    try:
        response = requests.get(f"{API_URL}/api/v1/stats")
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nStatistics:")
            print(f"  Total Resumes: {data.get('total_resumes')}")
            print(f"  Total Chunks: {data.get('total_chunks')}")

            if data.get('categories'):
                print(f"\n  Categories:")
                for cat in data['categories'][:5]:
                    print(f"    {cat['name']}: {cat['count']} ({cat['percentage']:.1f}%)")

            if data.get('experience_levels'):
                print(f"\n  Experience Levels:")
                for level in data['experience_levels']:
                    print(f"    {level['name']}: {level['count']} ({level['percentage']:.1f}%)")

            if data.get('role_categories'):
                print(f"\n  Role Categories:")
                for role in data['role_categories'][:5]:
                    print(f"    {role['name']}: {role['count']} ({role['percentage']:.1f}%)")
        else:
            print("Response:")
            print_response(response)

    except requests.exceptions.ConnectionError as e:
        print(f"Error: {e}")


def example_error_handling() -> None:
    """Example 6: Error handling."""
    print("\n" + "=" * 70)
    print("Example 6: Error Handling")
    print("=" * 70)

    # Test invalid JD
    print("\nTest 1: Invalid job description (too short)")
    payload = {
        "job_description": "Need developer.",
        "top_k": 5
    }

    try:
        response = requests.post(f"{API_URL}/api/v1/match", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.json().get('detail')}")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")

    # Test non-existent CSV
    print("\n\nTest 2: Non-existent CSV file")
    payload = {
        "csv_path": "data/non_existent.csv"
    }

    try:
        response = requests.post(f"{API_URL}/api/v1/ingest", json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.json().get('detail')}")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")


def example_curl_commands() -> None:
    """Example 7: cURL commands for testing."""
    print("\n" + "=" * 70)
    print("Example 7: cURL Commands for Testing")
    print("=" * 70)

    print("\n1. Health Check:")
    print("   curl http://localhost:8000/health")

    print("\n2. Ingest Resumes:")
    print('   curl -X POST http://localhost:8000/api/v1/ingest \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"csv_path": "data/resumes/resume_dataset.csv"}\'')

    print("\n3. Match Job:")
    print('   curl -X POST http://localhost:8000/api/v1/match \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{')
    print('       "job_description": "Senior Python backend engineer...",')
    print('       "top_k": 10,')
    print('       "filters": {"experience_level": "senior"}')
    print('     }\'')

    print("\n4. Get Statistics:")
    print("   curl http://localhost:8000/api/v1/stats")

    print("\n5. View API Documentation:")
    print("   Browser: http://localhost:8000/docs")
    print("   or:      http://localhost:8000/redoc")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Resume Matching System API - Client Examples")
    print("=" * 70)

    print("\nBefore running examples, start the API server:")
    print("  python -m uvicorn src.api.main:app --reload")
    print("\nOr:")
    print("  python -m src.api.main")

    try:
        # Run examples
        example_health_check()
        example_api_root()
        example_statistics()
        example_job_matching()
        example_ingestion()
        example_error_handling()
        example_curl_commands()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
