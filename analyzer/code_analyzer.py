"""
Code Whisperer - Code Analyzer
Calculates code quality metrics: complexity, maintainability, Halstead metrics.
"""

import math
from dataclasses import dataclass, field
from typing import List
from .parser import ParseResult


@dataclass
class CodeMetrics:
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    average_function_length: float = 0.0
    average_complexity: float = 0.0
    maintainability_index: float = 0.0
    code_quality_grade: str = "N/A"
    complex_functions: List[str] = field(default_factory=list)
    long_functions: List[str] = field(default_factory=list)


class CodeAnalyzer:
    """Performs static code analysis and calculates quality metrics."""

    def analyze(self, parsed: ParseResult) -> CodeMetrics:
        metrics = CodeMetrics()

        if not parsed:
            return metrics

        metrics.total_lines = parsed.total_lines
        metrics.total_functions = len(parsed.functions)
        metrics.total_classes = len(parsed.classes)

        # Classify lines
        if hasattr(parsed, 'raw_code'):
            lines = parsed.raw_code.splitlines()
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics.blank_lines += 1
                elif stripped.startswith('#') or stripped.startswith('//'):
                    metrics.comment_lines += 1
                else:
                    metrics.code_lines += 1

        # Function metrics
        if parsed.functions:
            total_len = 0
            total_comp = 0
            for func in parsed.functions:
                func_lines = len(func.code_snippet.splitlines()) if func.code_snippet else 0
                total_len += func_lines
                total_comp += func.complexity
                if func.complexity > 10:
                    metrics.complex_functions.append(func.name)
                if func_lines > 50:
                    metrics.long_functions.append(func.name)

            metrics.average_function_length = total_len / len(parsed.functions)
            metrics.average_complexity = total_comp / len(parsed.functions)

        # Maintainability Index
        avg_len = max(metrics.average_function_length, 1)
        avg_comp = metrics.average_complexity
        metrics.maintainability_index = max(0, min(100, round(
            171 - 5.2 * math.log(avg_len) - 0.23 * avg_comp - 16.2 * math.log(avg_len), 2
        )))

        # Grade
        mi = metrics.maintainability_index
        if mi >= 85:
            metrics.code_quality_grade = "A (Excellent)"
        elif mi >= 70:
            metrics.code_quality_grade = "B (Good)"
        elif mi >= 55:
            metrics.code_quality_grade = "C (Average)"
        elif mi >= 40:
            metrics.code_quality_grade = "D (Below Average)"
        else:
            metrics.code_quality_grade = "F (Poor)"

        return metrics

    def get_recommendations(self, metrics: CodeMetrics) -> List[str]:
        recommendations = []

        if metrics.average_complexity > 5:
            recommendations.append("Break down complex functions into smaller, focused units.")

        if metrics.average_function_length > 20:
            recommendations.append("Functions are quite long. Aim for under 20 lines per function.")

        if metrics.code_lines > 0 and metrics.comment_lines < metrics.code_lines * 0.1:
            recommendations.append("Add more comments and docstrings to improve documentation.")

        if metrics.complex_functions:
            recommendations.append(
                f"Refactor {len(metrics.complex_functions)} complex function(s): "
                f"{', '.join(metrics.complex_functions[:3])}"
            )

        if metrics.maintainability_index < 40:
            recommendations.append("Overall maintainability is poor. Consider a major refactoring.")

        if not recommendations:
            recommendations.append("Code looks good! No major issues detected.")

        return recommendations