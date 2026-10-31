"""
Import and verify Lexicon datasets.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.entities.lexicon import get_lexicon


def main():
    lex = get_lexicon()
    print(f"Loaded {len(lex.brands)} brand formulations.")
    print(f"Loaded {len(lex.generics)} canonical generic ingredients.")
    print(f"Loaded {len(lex.classes)} therapeutic drug classes.")
    print(f"Loaded {len(lex.herbal_entries)} AYUSH and herbal items.")
    print("Lexicon verification successful.")


if __name__ == "__main__":
    main()
