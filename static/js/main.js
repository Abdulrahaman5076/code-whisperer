// Code Whisperer - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textarea
    const textarea = document.querySelector('textarea');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 500) + 'px';
        });
    }
    
    // Tab support in textarea
    if (textarea) {
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 4;
            }
        });
    }
    
    // Confirm before leaving with unsaved code
    let codeChanged = false;
    if (textarea) {
        textarea.addEventListener('input', function() {
            codeChanged = true;
        });
    }
    
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function() {
            codeChanged = false;
        });
    }
    
    window.addEventListener('beforeunload', function(e) {
        if (codeChanged && textarea && textarea.value.trim()) {
            e.preventDefault();
            e.returnValue = 'You have unsaved code. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
    
    // Smooth scroll to results
    const resultsGrid = document.querySelector('.results-grid');
    if (resultsGrid) {
        resultsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Copy code hash to clipboard
    const hashElements = document.querySelectorAll('.analysis-hash, .history-card-header code');
    hashElements.forEach(function(el) {
        el.style.cursor = 'pointer';
        el.title = 'Click to copy hash';
        el.addEventListener('click', function() {
            const hash = this.textContent.replace('...', '').trim();
            navigator.clipboard.writeText(hash).then(function() {
                const original = el.textContent;
                el.textContent = 'Copied!';
                setTimeout(function() {
                    el.textContent = original;
                }, 1500);
            });
        });
    });
});