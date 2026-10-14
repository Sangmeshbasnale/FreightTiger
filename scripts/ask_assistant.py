import sys
from pathlib import Path

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.qa_assistant import PlainEnglishQAAssistant

def main():
    try:
        assistant = PlainEnglishQAAssistant("outputs/submission.csv")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nUser Query: {query}")
        print("\nAssistant Answer:")
        print(assistant.answer_query(query))
    else:
        print("=" * 60)
        print("FreightTiger Plain-English Q&A Assistant (Stretch Goal)")
        print("Type 'exit' or 'quit' to stop.")
        print("=" * 60)
        while True:
            try:
                user_q = input("\nAsk a question (e.g., 'Why did costs spike on Ahmedabad-Mumbai in January 2025?'): ")
                if user_q.strip().lower() in ["exit", "quit", "q"]:
                    break
                if not user_q.strip():
                    continue
                print("\nAssistant Answer:")
                print(assistant.answer_query(user_q))
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    main()
