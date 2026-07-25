"""
Code Whisperer - Models
Database models for storing analysis history and caching results.
"""

from django.db import models
import hashlib
import json

class AnalysisHistory(models.Model):
    """Stores past code analyses for user reference."""
    
    code_hash = models.CharField(max_length=64, unique=True, db_index=True)
    code_snippet = models.TextField(blank=True)
    code_language = models.CharField(max_length=50, default='python')
    total_lines = models.IntegerField(default=0)
    total_functions = models.IntegerField(default=0)
    total_classes = models.IntegerField(default=0)
    analysis_result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Analysis Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analysis {self.code_hash[:10]}... ({self.total_functions} functions)"
    
    @classmethod
    def get_or_create_from_code(cls, code: str):
        """Get cached analysis or create placeholder for new code."""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        obj, created = cls.objects.get_or_create(
            code_hash=code_hash,
            defaults={'code_snippet': code[:500]}
        )
        return obj, created

class SecurityIssue(models.Model):
    """Stores security issues found during analysis."""
    
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
        ('INFO', 'Info'),
    ]
    
    analysis = models.ForeignKey(AnalysisHistory, on_delete=models.CASCADE, related_name='security_issues')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    category = models.CharField(max_length=100)
    line_number = models.IntegerField()
    description = models.TextField()
    suggestion = models.TextField()
    code_snippet = models.TextField(blank=True)
    
    class Meta:
        ordering = ['severity', 'line_number']
    
    def __str__(self):
        return f"[{self.severity}] {self.category} at line {self.line_number}"

class PatternDetection(models.Model):
    """Stores AI-generated code patterns found during analysis."""
    
    analysis = models.ForeignKey(AnalysisHistory, on_delete=models.CASCADE, related_name='patterns')
    pattern_name = models.CharField(max_length=200)
    confidence = models.FloatField()
    description = models.TextField()
    location = models.CharField(max_length=500)
    evidence = models.TextField()
    
    class Meta:
        ordering = ['-confidence']
    
    def __str__(self):
        return f"{self.pattern_name} ({self.confidence:.0%})"