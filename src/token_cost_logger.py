import json
from pathlib import Path
from typing import Dict, Any

def log_token_and_cost(
    total_records: int = 2940,
    total_route_weeks: int = 728,
    llm_calls: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    embedding_queries_count: int = 28,
    output_path: str = "outputs/token_cost_log.json"
) -> Dict[str, Any]:
    """
    Computes and persists token usage and financial cost accounting.
    """
    approx_embedding_tokens = 10 * 80 + embedding_queries_count * 25  # ~10 notes + queries

    log_data = {
        "execution_profile": f"Full run across {total_records} shipments ({total_route_weeks} route-weeks)",
        "llm_accounting": {
            "model_name": "None (Deterministic Templates for Reason Field)",
            "llm_calls": llm_calls,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": 0.00,
            "cost_basis": "Zero API cost. Deterministic templates guarantee 100% byte-for-byte reproducibility."
        },
        "embedding_accounting": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "context_notes_embedded": 10,
            "queries_embedded": embedding_queries_count,
            "approx_embedding_input_tokens": approx_embedding_tokens,
            "embedding_calls": 2,
            "cost_usd": 0.00,
            "cost_basis": "Open-source model executed locally on CPU via SentenceTransformers & FAISS."
        },
        "total_financial_cost_usd": 0.00,
        "runtime_environment": {
            "libraries": [
                "pandas",
                "numpy",
                "sentence-transformers",
                "faiss-cpu",
                "pytest",
                "pyyaml"
            ],
            "paid_apis_used": False,
            "cloud_dependencies": False
        }
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

    return log_data
