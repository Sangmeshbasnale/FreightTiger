import numpy as np
from typing import List, Dict, Any, Tuple
from src.notes_registry import NotesRegistry

class NoteRetriever:
    def __init__(self, registry: NotesRegistry, model_name: str = "all-MiniLM-L6-v2"):
        self.registry = registry
        self.notes = registry.get_all_notes()
        self.model_name = model_name
        self.model = None
        self.note_embeddings = None
        self._init_embeddings()

    def _init_embeddings(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            texts = [
                f"Note {n['note_id']} on {n['date']} for {n['applies_to']}: {n['note']}"
                for n in self.notes
            ]
            self.note_embeddings = self.model.encode(texts, normalize_embeddings=True)
        except Exception as e:
            # Fallback if sentence-transformers is still installing or unavailable
            print(f"Warning: SentenceTransformer not initialized ({e}). Using lexical scoring.")
            self.model = None

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves top_k notes matching the semantic query.
        Returns list of (note_dict, similarity_score).
        """
        if self.model is not None and self.note_embeddings is not None:
            q_emb = self.model.encode([query], normalize_embeddings=True)[0]
            scores = np.dot(self.note_embeddings, q_emb)
            top_indices = np.argsort(scores)[::-1][:top_k]
            return [(self.notes[i], float(scores[i])) for i in top_indices]
        else:
            # Lexical fallback based on token overlap
            q_words = set(query.lower().split())
            results = []
            for n in self.notes:
                n_text = f"{n['note_id']} {n['applies_to']} {n['note']}".lower()
                score = sum(1.0 for w in q_words if w in n_text) / (len(q_words) + 1e-5)
                results.append((n, score))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
