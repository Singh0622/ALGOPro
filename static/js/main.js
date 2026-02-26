// DSA Learning Platform - Main JavaScript

// ==========================================
// GLOBAL QUIZ STATE
// ==========================================
let quizState = {
    currentQuestion: 0,
    totalQuestions: 0,
    timeLeft: 0,
    timerInterval: null,
    answers: {},
    startTime: null,
    isQuizActive: false
};

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Main.js loaded');
    
    // Check if we're on a quiz page
    if (document.querySelector('.question-card')) {
        console.log('Quiz page detected, initializing...');
        initQuiz();
    }
    
    initializeSyntaxHighlighting();
    initializeSmoothScrolling();
    initializeTooltips();
});

// ==========================================
// QUIZ INITIALIZATION - CRITICAL FIX
// ==========================================
function initQuiz() {
    const questionCards = document.querySelectorAll('.question-card');
    quizState.totalQuestions = questionCards.length;
    
    if (quizState.totalQuestions === 0) {
        console.error('No questions found!');
        return;
    }
    
    console.log('Initializing quiz with', quizState.totalQuestions, 'questions');
    
    // Get time limit from the timer display
    const timerEl = document.getElementById('timer');
    if (timerEl) {
        const timeText = timerEl.textContent;
        const parts = timeText.split(':');
        quizState.timeLeft = (parseInt(parts[0]) * 60) + parseInt(parts[1]);
    } else {
        quizState.timeLeft = quizState.totalQuestions * 3 * 60;
    }
    
    quizState.startTime = Date.now();
    quizState.isQuizActive = true;
    quizState.currentQuestion = 0;
    quizState.answers = {};
    
    // CRITICAL FIX: Setup event listeners using delegation
    setupOptionListeners();
    
    // CRITICAL: Start timer
    startQuizTimer();
    
    // Update initial display
    updateQuizProgress();
    updateAnsweredCount();
}

// ==========================================
// OPTION SELECTION - CRITICAL FIX
// ==========================================
function setupOptionListeners() {
    // Use event delegation on the document
    document.addEventListener('click', function(e) {
        // Check if clicked element is an option label or inside one
        const label = e.target.closest('.option-label');
        if (!label) return;
        
        // Get the associated radio button
        const radioId = label.getAttribute('for');
        if (!radioId) return;
        
        const radio = document.getElementById(radioId);
        if (!radio || !radio.name.startsWith('question_')) return;
        
        // Prevent default to handle manually
        e.preventDefault();
        
        // Check this radio
        radio.checked = true;
        
        // Handle the selection
        handleOptionSelect(radio);
    });
    
    console.log('Click event delegation setup complete');
}

function handleOptionSelect(radio) {
    const name = radio.name;
    const questionIdx = name.replace('question_', '');
    const selectedValue = radio.value;
    
    console.log('Option selected - Question:', questionIdx, 'Value:', selectedValue);
    
    // Store answer
    quizState.answers[questionIdx] = selectedValue;
    
    // Visual feedback - ONLY for this question
    const questionCard = document.getElementById('question-card-' + questionIdx);
    if (questionCard) {
        // Remove selected from all options in this question
        questionCard.querySelectorAll('.option-item').forEach(function(opt) {
            opt.classList.remove('selected');
        });
        
        // Add selected to clicked option
        radio.closest('.option-item').classList.add('selected');
    }
    
    updateAnsweredCount();
}

// ==========================================
// TIMER - CRITICAL FIX
// ==========================================
function startQuizTimer() {
    console.log('Starting timer with', quizState.timeLeft, 'seconds');
    
    if (quizState.timerInterval) {
        clearInterval(quizState.timerInterval);
    }
    
    updateTimerDisplay();
    
    quizState.timerInterval = setInterval(function() {
        quizState.timeLeft--;
        updateTimerDisplay();
        
        if (quizState.timeLeft <= 0) {
            clearInterval(quizState.timerInterval);
            submitQuiz(true);
        }
    }, 1000);
    
    console.log('Timer started');
}

function updateTimerDisplay() {
    const timerEl = document.getElementById('timer');
    if (!timerEl) return;
    
    const minutes = Math.floor(quizState.timeLeft / 60);
    const seconds = quizState.timeLeft % 60;
    
    timerEl.textContent = minutes + ':' + seconds.toString().padStart(2, '0');
    
    if (quizState.timeLeft < 60) {
        timerEl.className = 'stat-value text-danger';
    } else if (quizState.timeLeft < 180) {
        timerEl.className = 'stat-value text-warning';
    } else {
        timerEl.className = 'stat-value text-primary';
    }
}

// ==========================================
// NAVIGATION
// ==========================================
function nextQuestion() {
    console.log('Next clicked, current:', quizState.currentQuestion);
    
    if (quizState.currentQuestion < quizState.totalQuestions - 1) {
        const currentCard = document.getElementById('question-card-' + quizState.currentQuestion);
        if (currentCard) {
            currentCard.classList.add('d-none');
        }
        
        quizState.currentQuestion++;
        const nextCard = document.getElementById('question-card-' + quizState.currentQuestion);
        if (nextCard) {
            nextCard.classList.remove('d-none');
        }
        
        updateQuizProgress();
    }
}

function previousQuestion() {
    console.log('Previous clicked, current:', quizState.currentQuestion);
    
    if (quizState.currentQuestion > 0) {
        const currentCard = document.getElementById('question-card-' + quizState.currentQuestion);
        if (currentCard) {
            currentCard.classList.add('d-none');
        }
        
        quizState.currentQuestion--;
        const prevCard = document.getElementById('question-card-' + quizState.currentQuestion);
        if (prevCard) {
            prevCard.classList.remove('d-none');
        }
        
        updateQuizProgress();
    }
}

function updateQuizProgress() {
    const progress = ((quizState.currentQuestion + 1) / quizState.totalQuestions) * 100;
    
    const bar = document.getElementById('progress-bar');
    const counter = document.getElementById('question-counter');
    
    if (bar) bar.style.width = progress + '%';
    if (counter) counter.textContent = (quizState.currentQuestion + 1) + '/' + quizState.totalQuestions;
}

function updateAnsweredCount() {
    const display = document.getElementById('score-display');
    if (display) {
        display.textContent = Object.keys(quizState.answers).length;
    }
}

// ==========================================
// HINT AND EXPLANATION
// ==========================================
function showHint(index) {
    const hint = document.getElementById('hint-' + index);
    if (hint) hint.classList.remove('d-none');
}

function explainQuestion(index) {
    const box = document.getElementById('ai-explain-' + index);
    if (!box) return;
    
    box.classList.remove('d-none');
    
    const card = document.getElementById('question-card-' + index);
    const title = card ? card.querySelector('.card-title').textContent : '';
    
    fetch('/api/explain', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            concept: title,
            context: 'Quiz Question',
            difficulty: 'intermediate'
        })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        box.innerHTML = '<div class="ai-explanation-content">' + data.explanation + '</div>';
    })
    .catch(function() {
        box.innerHTML = '<div class="text-danger">Failed to load explanation.</div>';
    });
}

// ==========================================
// SUBMIT QUIZ
// ==========================================
function submitQuiz(autoSubmit) {
    const answeredCount = Object.keys(quizState.answers).length;
    
    if (!autoSubmit && answeredCount < quizState.totalQuestions) {
        const countEl = document.getElementById('answered-count');
        if (countEl) countEl.textContent = answeredCount;
        
        const modal = new bootstrap.Modal(document.getElementById('submitModal'));
        modal.show();
        return;
    }
    
    if (quizState.timerInterval) {
        clearInterval(quizState.timerInterval);
    }
    
    const timeTaken = Math.floor((Date.now() - quizState.startTime) / 1000);
    const mins = Math.floor(timeTaken / 60);
    const secs = timeTaken % 60;
    
    console.log('Submitting answers:', quizState.answers);
    
    fetch('/api/submit-quiz', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({answers: quizState.answers})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        displayResults(data, mins + ':' + secs.toString().padStart(2, '0'));
    })
    .catch(function(err) {
        alert('Error submitting quiz: ' + err.message);
    });
}

function confirmSubmit() {
    const modalEl = document.getElementById('submitModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
    submitQuiz(true);
}

function displayResults(data, timeStr) {
    const quizContainer = document.getElementById('quiz-container');
    const resultsContainer = document.getElementById('results-container');
    
    if (quizContainer) quizContainer.classList.add('d-none');
    if (resultsContainer) resultsContainer.classList.remove('d-none');
    
    const scoreEl = document.getElementById('final-score');
    const msgEl = document.getElementById('result-message');
    const circle = document.getElementById('final-score-circle');
    
    if (scoreEl) scoreEl.textContent = Math.round(data.score) + '%';
    if (document.getElementById('correct-count')) {
        document.getElementById('correct-count').textContent = data.correct;
    }
    if (document.getElementById('wrong-count')) {
        document.getElementById('wrong-count').textContent = data.total - data.correct;
    }
    if (document.getElementById('time-taken')) {
        document.getElementById('time-taken').textContent = timeStr;
    }
    
    if (circle) {
        if (data.score >= 80) {
            circle.style.borderColor = '#28a745';
            if (msgEl) msgEl.textContent = '🌟 Excellent! Mastery achieved!';
        } else if (data.score >= 60) {
            circle.style.borderColor = '#ffc107';
            if (msgEl) msgEl.textContent = '👍 Good job! Keep practicing!';
        } else {
            circle.style.borderColor = '#dc3545';
            if (msgEl) msgEl.textContent = '📚 Keep learning! Review the topic.';
        }
    }
    
    if (data.improved) {
        const badge = document.getElementById('improvement-badge');
        if (badge) {
            badge.innerHTML = '<span class="badge bg-success fs-6">🎉 New Personal Best! (Previous: ' + data.previous_best + '%)</span>';
        }
    }
    
    const container = document.getElementById('review-questions');
    if (container) {
        container.innerHTML = '';
        
        data.results.forEach(function(result, idx) {
            const isCorrect = result.is_correct;
            const card = document.createElement('div');
            card.className = 'card mb-3 ' + (isCorrect ? 'border-success' : 'border-danger');
            
            let optionsHtml = '';
            Object.entries(result.options).forEach(function([k, v]) {
                let cls = 'p-2 mb-1 rounded ';
                if (k === result.correct_answer) cls += 'bg-success text-white';
                else if (k === result.user_answer && !isCorrect) cls += 'bg-danger text-white';
                else cls += 'bg-light';
                
                let mark = '';
                if (k === result.correct_answer) mark = ' ✓';
                else if (k === result.user_answer && !isCorrect) mark = ' ✗ (Your answer)';
                
                optionsHtml += '<div class="' + cls + '">' + k + '. ' + v + mark + '</div>';
            });
            
            card.innerHTML = 
                '<div class="card-header ' + (isCorrect ? 'bg-success' : 'bg-danger') + ' text-white d-flex justify-content-between">' +
                    '<span>Question ' + (idx + 1) + '</span>' +
                    '<span>' + (isCorrect ? '✓ Correct' : '✗ Wrong') + '</span>' +
                '</div>' +
                '<div class="card-body">' +
                    '<p class="fw-bold">' + result.question + '</p>' +
                    '<div class="options-review">' + optionsHtml + '</div>' +
                    (result.explanation ? '<div class="alert alert-info mt-3"><strong>Explanation:</strong> ' + result.explanation + '</div>' : '') +
                '</div>';
            
            container.appendChild(card);
        });
    }
    
    window.scrollTo(0, 0);
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================
function initializeSyntaxHighlighting() {
    if (typeof hljs !== 'undefined') {
        hljs.highlightAll();
    }
}

function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({behavior: 'smooth', block: 'start'});
            }
        });
    });
}

function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// ==========================================
// KEYBOARD SHORTCUTS
// ==========================================
document.addEventListener('keydown', function(e) {
    if (!quizState.isQuizActive) return;
    
    if (e.key === 'ArrowRight') {
        e.preventDefault();
        nextQuestion();
    }
    if (e.key === 'ArrowLeft') {
        e.preventDefault();
        previousQuestion();
    }
    if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        submitQuiz();
    }
});

// ==========================================
// GLOBAL EXPORTS
// ==========================================
window.nextQuestion = nextQuestion;
window.previousQuestion = previousQuestion;
window.submitQuiz = submitQuiz;
window.confirmSubmit = confirmSubmit;
window.showHint = showHint;
window.explainQuestion = explainQuestion;