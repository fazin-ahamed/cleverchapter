import json
import os
from pathlib import Path


class Library:
    def __init__(self, path=None):
        self.path = Path(path or Path.home() / ".cleverchapter" / "library.json")
        self.data = {"books": [], "reels": [], "saved": []}
        
        if self.path.exists():
            with self.path.open(encoding="utf-8") as file:
                self.data.update(json.load(file))

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=2)
        
        os.replace(temporary, self.path)
