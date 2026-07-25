"""
Code Whisperer - Code Parser
Parses source code into structured data using AST for Python, regex for JS/TS.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class FunctionInfo:
    name: str
    line: int
    args: List[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    complexity: int = 0
    code_snippet: str = ""


@dataclass
class ClassInfo:
    name: str
    line: int
    methods: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ImportInfo:
    module: str
    alias: Optional[str] = None
    names: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    language: str
    total_lines: int
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    call_graph: Dict[str, List[str]]
    entry_points: List[str]
    orphans: List[str]
    raw_code: str = ""


class CodeParser:
    """Parses source code into a structured representation."""

    def parse(self, code: str, language: str = "auto") -> Tuple[Optional[ParseResult], Optional[str]]:
        if language == "auto":
            language = self._detect_language(code)

        if language == "python":
            return self._parse_python(code)
        elif language in ("javascript", "typescript"):
            return self._parse_javascript(code, language)
        return None, f"Unsupported language: {language}"

    def _detect_language(self, code: str) -> str:
        py_keywords = ["def ", "class ", "import ", "from ", "print(", "elif ", "self."]
        js_keywords = ["function ", "const ", "let ", "var ", "=>", "console.log", "require("]
        py_score = sum(1 for kw in py_keywords if kw in code)
        js_score = sum(1 for kw in js_keywords if kw in code)
        return "python" if py_score >= js_score else "javascript"

    def _parse_python(self, code: str) -> Tuple[Optional[ParseResult], Optional[str]]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return None, f"Syntax error at line {e.lineno}: {e.msg}"

        functions, classes, imports = [], [], []
        call_graph = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func = FunctionInfo(
                    name=node.name,
                    line=node.lineno,
                    args=[a.arg for a in node.args.args],
                    returns=self._get_return(node),
                    docstring=ast.get_docstring(node),
                    decorators=self._get_decorators(node),
                    complexity=self._complexity(node),
                    code_snippet=ast.get_source_segment(code, node) or "",
                )
                functions.append(func)
                call_graph[func.name] = self._get_calls(node)

            elif isinstance(node, ast.ClassDef):
                cls = ClassInfo(
                    name=node.name,
                    line=node.lineno,
                    methods=[m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    bases=self._get_bases(node),
                    docstring=ast.get_docstring(node),
                )
                classes.append(cls)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(module=alias.name, alias=alias.asname))
            elif isinstance(node, ast.ImportFrom):
                imports.append(ImportInfo(module=node.module or "", names=[a.name for a in node.names]))

        all_called = set()
        for callees in call_graph.values():
            all_called.update(callees)

        entry_points = [f.name for f in functions if f.name not in all_called]
        orphans = [f.name for f in functions if not call_graph.get(f.name) and f.name not in all_called]

        return ParseResult(
            language="python",
            total_lines=len(code.splitlines()),
            functions=functions,
            classes=classes,
            imports=imports,
            call_graph=call_graph,
            entry_points=entry_points,
            orphans=orphans,
            raw_code=code,
        ), None

    def _get_return(self, node: ast.FunctionDef) -> Optional[str]:
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            if isinstance(node.returns, ast.Constant):
                return str(node.returns.value)
        return None

    def _get_decorators(self, node: ast.FunctionDef) -> List[str]:
        decs = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decs.append(d.id)
            elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                decs.append(d.func.id)
        return decs

    def _get_calls(self, node: ast.AST) -> List[str]:
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))

    def _get_bases(self, node: ast.ClassDef) -> List[str]:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        return bases

    def _complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _parse_javascript(self, code: str, language: str) -> Tuple[Optional[ParseResult], Optional[str]]:
        functions = []
        imports = []

        pattern = r'(?:function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>)'
        for match in re.finditer(pattern, code):
            name = match.group(1) or match.group(3)
            if name:
                args_str = match.group(2) or match.group(4) or ""
                args = [a.strip() for a in args_str.split(",") if a.strip()]
                line = code[:match.start()].count("\n") + 1
                functions.append(FunctionInfo(name=name, line=line, args=args))

        import_pattern = r'(?:import\s+.*?from\s+["\']([^"\']+)["\']|require\(["\']([^"\']+)["\']\))'
        for match in re.finditer(import_pattern, code):
            module = match.group(1) or match.group(2)
            if module:
                imports.append(ImportInfo(module=module))

        return ParseResult(
            language=language,
            total_lines=len(code.splitlines()),
            functions=functions,
            classes=[],
            imports=imports,
            call_graph={},
            entry_points=[f.name for f in functions],
            orphans=[],
            raw_code=code,
        ), None