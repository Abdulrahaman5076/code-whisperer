"""
Code Whisperer - Views
Handle HTTP requests and render responses.
"""

import hashlib
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from .forms import CodeAnalysisForm
from .models import AnalysisHistory, SecurityIssue, PatternDetection
from .parser import CodeParser
from .graph_engine import GraphEngine
from .impact_engine import ImpactAnalyzer
from .security_scanner import SecurityScanner
from .pattern_detector import PatternDetector
from .code_analyzer import CodeAnalyzer
from .gemini_engine import GeminiEngine
from utils.validators import RateLimiter
from utils.cache import AnalysisCache

# Initialize components
parser = CodeParser()
graph_engine = GraphEngine()
impact_analyzer = ImpactAnalyzer()
security_scanner = SecurityScanner()
pattern_detector = PatternDetector()
code_analyzer = CodeAnalyzer()
rate_limiter = RateLimiter()
cache = AnalysisCache()

def home_view(request):
    """Render the home page with the code input form."""
    form = CodeAnalysisForm()
    return render(request, 'home.html', {
        'form': form,
        'recent_analyses': AnalysisHistory.objects.all()[:5],
    })

@require_http_methods(["POST"])
def analyze_view(request):
    """Process the code analysis form and return results."""
    form = CodeAnalysisForm(request.POST)
    
    if not form.is_valid():
        return render(request, 'home.html', {
            'form': form,
            'errors': form.errors,
        })
    
    # Rate limiting
    client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    if not rate_limiter.is_allowed(client_ip):
        messages.error(request, 'Rate limit exceeded. Please wait before submitting again.')
        return redirect('home')
    
    code = form.cleaned_data['code']
    api_key = form.cleaned_data['api_key'] or settings.GEMINI_API_KEY
    language = form.cleaned_data.get('language', 'auto')
    
    # Check cache
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    cached_result = cache.get(code_hash)
    
    if cached_result:
        return render(request, 'result.html', cached_result)
    
    start_time = time.time()
    
    # Parse code
    parsed, parse_error = parser.parse(code, language)
    
    if parse_error:
        return render(request, 'error.html', {
            'error_type': 'Parse Error',
            'error_message': parse_error,
            'code_snippet': code[:500],
        })
    
    # Build dependency graph
    G = graph_engine.build(parsed)
    
    # Run security scan
    security_report = security_scanner.scan(code)
    
    # Detect AI patterns
    pattern_report = pattern_detector.detect(parsed)
    
    # Calculate code metrics
    metrics = code_analyzer.analyze(parsed)
    recommendations = code_analyzer.get_recommendations(metrics)
    
    # Impact analysis for key functions
    impact_results = {}
    for func in parsed.functions[:10]:  # Analyze top 10 functions
        impact = impact_analyzer.analyze(G, func.name)
        impact_results[func.name] = impact
    
    # AI Explanation (if API key available)
    ai_explanation = None
    if api_key:
        try:
            gemini = GeminiEngine(api_key)
            summary = (
                f"Functions: {[f.name for f in parsed.functions]}\n"
                f"Classes: {[c.name for c in parsed.classes]}\n"
                f"Entry Points: {parsed.entry_points}\n"
                f"Orphans: {parsed.orphans}"
            )
            ai_explanation = gemini.explain_code(code, summary)
        except Exception as e:
            ai_explanation = f"AI explanation unavailable: {str(e)}"
    
    # Save to database
    analysis, created = AnalysisHistory.objects.get_or_create(
        code_hash=code_hash,
        defaults={
            'code_snippet': code[:500],
            'code_language': parsed.language,
            'total_lines': parsed.total_lines,
            'total_functions': len(parsed.functions),
            'total_classes': len(parsed.classes),
        }
    )
    
    if created:
        # Save security issues
        for issue in security_report.issues:
            SecurityIssue.objects.create(
                analysis=analysis,
                severity=issue.severity,
                category=issue.category,
                line_number=issue.line,
                description=issue.description,
                suggestion=issue.suggestion,
                code_snippet=issue.code_snippet,
            )
        
        # Save patterns
        for pattern in pattern_report.patterns:
            PatternDetection.objects.create(
                analysis=analysis,
                pattern_name=pattern.name,
                confidence=pattern.confidence,
                description=pattern.description,
                location=pattern.location,
                evidence=pattern.evidence,
            )
    
    processing_time = round(time.time() - start_time, 2)
    
    # Build result context
    context = {
        'parsed': parsed,
        'security_report': security_report,
        'pattern_report': pattern_report,
        'metrics': metrics,
        'recommendations': recommendations,
        'impact_results': impact_results,
        'ai_explanation': ai_explanation,
        'entry_points': parsed.entry_points,
        'orphans': parsed.orphans,
        'call_graph': parsed.call_graph,
        'processing_time': processing_time,
        'code_hash': code_hash,
        'analysis': analysis,
    }
    
    # Cache the result
    cache.set(code_hash, context)
    
    return render(request, 'result.html', context)

def history_view(request):
    """Show past analyses."""
    analyses = AnalysisHistory.objects.all()
    paginator = Paginator(analyses, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'history.html', {
        'page_obj': page_obj,
    })

def analysis_detail_view(request, code_hash):
    """Show a specific past analysis."""
    analysis = get_object_or_404(AnalysisHistory, code_hash=code_hash)
    security_issues = analysis.security_issues.all()
    patterns = analysis.patterns.all()
    
    return render(request, 'analysis_detail.html', {
        'analysis': analysis,
        'security_issues': security_issues,
        'patterns': patterns,
    })