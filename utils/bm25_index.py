import re
import os
from pathlib import Path
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self, campaign_path: Path):
        self.campaign_path = campaign_path
        self.files = []
        self.corpus = []
        self.bm25 = None
        self._refresh_index()

    def _tokenize(self, text):
        return re.findall(r'\w+', text.lower())

    def _refresh_index(self):
        self.files = []
        self.corpus = []
        
        # Index NPCs and Locations
        for folder in ["npcs", "locations"]:
            path = self.campaign_path / folder
            if path.exists():
                for f in path.glob("*.md"):
                    content = f.read_text(encoding="utf-8")
                    self.files.append(f)
                    self.corpus.append(self._tokenize(content))
        
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)

    def get_top_matches(self, query: str, n=2):
        if not self.bm25:
            return []
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get indices of top scores
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        
        # Filter out very low scores (optional)
        results = [self.files[i] for i in top_indices if scores[i] > 0.1]
        return results

# Global cache for indices to avoid re-reading files on every query
_indices = {}

def get_campaign_index(campaign_name: str) -> BM25Index:
    if campaign_name not in _indices:
        from campaign_loader import CAMPAIGN_DIR
        path = CAMPAIGN_DIR / campaign_name
        _indices[campaign_name] = BM25Index(path)
    return _indices[campaign_name]
