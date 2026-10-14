import json
import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.token_cost_logger import log_token_and_cost

def main():
    print("=" * 60)
    print(">>> RUNNING TOKEN & COST ACCOUNTING (PHASE 9)")
    print("=" * 60)
    log_data = log_token_and_cost()
    print("Token & Cost log written to outputs/token_cost_log.json:")
    print(json.dumps(log_data, indent=2))

if __name__ == "__main__":
    main()
