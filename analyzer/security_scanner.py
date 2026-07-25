"""
Code Whisperer - Security Scanner
Scans code for vulnerabilities and anti-patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class SecurityIssue:
    severity: str
    category: str
    line: int
    description: str
    suggestion: str
    code_snippet: str = ""
    cwe_id: str = ""


@dataclass
class SecurityReport:
    issues: List[SecurityIssue] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "CRITICAL")

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "HIGH")

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "MEDIUM")

    @property
    def low_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "LOW")

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0


class SecurityScanner:
    """Scans source code for security vulnerabilities."""

    RULES = [
        (r'(?:api[_-]?key|apikey|secret[_-]?key|password|passwd|token)\s*[:=]\s*["\'][^"\']{8,}["\']',
         "CRITICAL", "HARDCODED_SECRET",
         "Hardcoded secret or API key found.",
         "Use environment variables: os.getenv('SECRET_NAME')", "CWE-798"),
        (r'eval\s*\(', "CRITICAL", "CODE_INJECTION",
         "eval() executes arbitrary code from strings.",
         "Use json.loads() or ast.literal_eval() instead.", "CWE-95"),
        (r'exec\s*\(', "CRITICAL", "CODE_INJECTION",
         "exec() executes arbitrary Python code.",
         "Remove exec() entirely. There is no safe use case.", "CWE-95"),
        (r'os\.system\s*\(', "HIGH", "COMMAND_INJECTION",
         "os.system() enables command injection.",
         "Use subprocess.run() with shell=False and argument lists.", "CWE-78"),
        (r'subprocess\.\w+\s*\([^)]*shell\s*=\s*True', "HIGH", "COMMAND_INJECTION",
         "subprocess with shell=True is vulnerable.",
         "Set shell=False and pass arguments as a list.", "CWE-78"),
        (r'pickle\.loads?\s*\(', "MEDIUM", "UNSAFE_DESERIALIZATION",
         "pickle can execute arbitrary code during deserialization.",
         "Use json.loads() instead.", "CWE-502"),
        (r'password\s*=\s*input\s*\(', "MEDIUM", "PASSWORD_VISIBLE",
         "Password input may be visible on screen.",
         "Use getpass.getpass() for password input.", "CWE-549"),
        (r'except\s*:', "LOW", "BARE_EXCEPT",
         "Bare except clause catches everything including KeyboardInterrupt.",
         "Catch specific exceptions: except ValueError:", "CWE-396"),
    ]

    def scan(self, code: str) -> SecurityReport:
        report = SecurityReport()
        lines = code.splitlines()

        for pattern, severity, category, description, suggestion, cwe_id in self.RULES:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                line_no = code[:match.start()].count("\n") + 1
                snippet = ""
                if line_no <= len(lines):
                    snippet = lines[line_no - 1].strip()[:100]

                report.issues.append(SecurityIssue(
                    severity=severity,
                    category=category,
                    line=line_no,
                    description=description,
                    suggestion=suggestion,
                    code_snippet=snippet,
                    cwe_id=cwe_id,
                ))

        return report