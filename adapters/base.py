from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

@dataclass
class Adapter:
    name: str
    module: str
    student_files: list
    package: str
    student_class: str
    timeout_sec: float = 2.0

    def write_harness(self, harness_path: Path, method: dict) -> None:
        """Generate a Java harness that calls student code and prints machine-readable results."""
        raise NotImplementedError

    def harness_main_class(self) -> str:
        """The class name to run with `java`."""
        raise NotImplementedError
    
    def methods(self) -> list:
        """Returns a list of method dicts with keys: name, return_type, params."""
        raise NotImplementedError
    