from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

@dataclass
class Adapter:
    name: str
    module: str
    student_java: Path          # e.g. Path("M4/Sort.java")
    package: str                # e.g. "M4"
    student_class: str          # e.g. "Sort"
    timeout_sec: float = 2.0

    def write_harness(self, harness_path: Path) -> None:
        """Generate a Java harness that calls student code and prints machine-readable results."""
        raise NotImplementedError

    def harness_main_class(self) -> str:
        """The class name to run with `java`."""
        raise NotImplementedError
