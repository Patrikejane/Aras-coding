import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Method:
    name:        str
    language:    str
    method_type: str
    code:        str
    source_file: str


class CodeReader:
    EXT_TO_LANG   = {".cs": "C#", ".js": "JavaScript"}
    FOLDER_TO_TYPE= {"cs": "Server", "js": "Client"}

    def __init__(self, extracted_path: str):
        self.path = Path(extracted_path)

    def read_all(self) -> list:
        if not self.path.exists():
            raise FileNotFoundError(f"Extracted folder not found: {self.path}")
        methods = []
        for root, _, files in os.walk(self.path):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext not in self.EXT_TO_LANG: continue
                m = self._read(Path(root) / f, ext)
                if m: methods.append(m)
        return methods

    def _read(self, fp: Path, ext: str):
        try:
            code = fp.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  [CodeReader] Cannot read {fp}: {e}")
            return None
        language    = self.EXT_TO_LANG[ext]
        folder      = fp.parent.name.lower()
        method_type = self.FOLDER_TO_TYPE.get(folder, "Unknown")
        method_type = self._header(code, "method type", method_type)
        language    = self._header(code, "language",    language)
        return Method(name=fp.stem, language=language, method_type=method_type,
                      code=code.strip(), source_file=str(fp))

    def _header(self, code, key, default):
        for line in code.splitlines()[:10]:
            s = line.strip().lstrip("/#").strip()
            if s.lower().startswith(key + ":"):
                v = s.split(":", 1)[1].strip()
                if v: return v
        return default
