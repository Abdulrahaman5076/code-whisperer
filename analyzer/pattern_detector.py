"""
Code Whisperer - Pattern Detector
Detects telltale signs of AI-generated code.
"""

import re
from dataclasses import dataclass, field
from typing import List
from .parser import ParseResult


@dataclass
class DetectedPattern:
    name: str
    confidence: float
    description: str
    location: str
    evidence: str


@dataclass
class PatternReport:
    patterns: List[DetectedPattern] = field(default_factory=list)
    ai_likelihood_score: float = 0.0
    summary: str = ""

    @property
    def is_likely_ai_generated(self) -> bool:
        return self.ai_likelihood_score > 0.5


class PatternDetector:
    """Detects patterns common in AI-generated code."""

    def detect(self, parsed: ParseResult) -> PatternReport:
        report = PatternReport()

        if not parsed:
            return report

        # Check for generic variable names
        if hasattr(parsed, 'raw_code'):
            code = parsed.raw_code
            generic_names = {'data', 'result', 'temp', 'info', 'value', 'item', 'obj', 'foo', 'bar'}
            found = [n for n in generic_names if re.search(rf'\b{n}\s*=', code)]

            if len(found) >= 3:
                report.patterns.append(DetectedPattern(
                    name="Generic Variable Names",
                    confidence=min(0.9, len(found) * 0.2),
                    description="Multiple generic variable names detected",
                    location="Throughout code",
                    evidence=f"Found: {', '.join(sorted(found))}",
                ))

        # Check for missing docstrings
        missing_docs = [f for f in parsed.functions if not f.docstring and f.complexity > 2]
        if len(missing_docs) >= 2 and len(parsed.functions) > 0:
            ratio = len(missing_docs) / len(parsed.functions)
            if ratio > 0.5:
                report.patterns.append(DetectedPattern(
                    name="Missing Docstrings",
                    confidence=min(0.9, ratio),
                    description=f"{len(missing_docs)} functions without documentation",
                    location=", ".join(f.name for f in missing_docs[:3]),
                    evidence=f"{len(missing_docs)}/{len(parsed.functions)} functions lack docstrings",
                ))

        # Check for placeholders
        if hasattr(parsed, 'raw_code'):
            code = parsed.raw_code
            placeholder_count = (
                code.count('pass') +
                code.count('TODO') +
                code.count('FIXME') +
                code.count('NotImplementedError') +
                code.count('NotImplemented')
            )
            if placeholder_count >= 2:
                report.patterns.append(DetectedPattern(
                    name="Placeholder Code",
                    confidence=min(0.85, placeholder_count * 0.2),
                    description="Placeholder or incomplete implementations found",
                    location="Multiple locations",
                    evidence=f"{placeholder_count} placeholders detected (pass, TODO, NotImplemented)",
                ))

        # Check for unused imports
        if hasattr(parsed, 'raw_code'):
            code = parsed.raw_code
            unused = []
            for imp in parsed.imports:
                if imp.module and imp.module not in code.replace(f'import {imp.module}', '').replace(f'from {imp.module}', ''):
                    unused.append(imp.module)
            if len(unused) >= 2:
                report.patterns.append(DetectedPattern(
                    name="Unused Imports",
                    confidence=min(0.8, len(unused) * 0.2),
                    description="Imports that are never used in the code",
                    location="Import section",
                    evidence=f"Unused: {', '.join(unused[:5])}",
                ))

        # Calculate overall score
        if report.patterns:
            total_confidence = sum(p.confidence for p in report.patterns)
            report.ai_likelihood_score = min(0.95, total_confidence / len(report.patterns))

        # Generate summary
        if report.ai_likelihood_score > 0.7:
            confidence = "very high"
        elif report.ai_likelihood_score > 0.5:
            confidence = "high"
        elif report.ai_likelihood_score > 0.3:
            confidence = "moderate"
        else:
            confidence = "low"

        report.summary = (
            f"There is a **{confidence} likelihood** (score: {report.ai_likelihood_score:.0%}) "
            f"that this code is AI-generated. Found {len(report.patterns)} pattern(s)."
        )

        return report