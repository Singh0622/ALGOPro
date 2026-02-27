from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
import os
from dotenv import load_dotenv
import markdown
from datetime import datetime
import random
import re
import html
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Configure OpenRouter API
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Load DSA Content
def load_dsa_content():
    with open('data/dsa_content.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_quiz_templates():
    with open('data/quiz_templates.json', 'r', encoding='utf-8') as f:
        return json.load(f)

DSA_CONTENT = load_dsa_content()
QUIZ_TEMPLATES = load_quiz_templates()

def get_topic_by_id(topic_id):
    return next((t for t in DSA_CONTENT['topics'] if t['id'] == topic_id), None)

def call_openrouter(prompt, temperature=0.9, max_tokens=8000):
    """Call OpenRouter API with OpenAI GPT-OSS-120B"""
    if not OPENROUTER_API_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "DSA Learning Platform"
    }
    
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are an expert Data Structures and Algorithms instructor. Create clear, well-formatted multiple choice questions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        return None

def parse_quiz_from_llm_response(text):
    """Parse LLM response into structured quiz format - ROBUST PARSING"""
    questions = []
    
    if not text or not isinstance(text, str):
        print("ERROR: Empty or invalid text provided to parser")
        return []
    
    # Clean up the text - normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n').strip()
    
    # Split by question patterns - more flexible matching
    question_patterns = [
        r'\n\s*Question\s*\d+\s*[\.:\)]\s*',
        r'\n\s*Q\s*\d+\s*[\.:\)]\s*',
        r'\n\s*#{1,3}\s*Question\s*\d+',
        r'\n\s*\*\*Question\s*\d+\*\*',
        r'\n\s*\d+\s*[\.:\)]\s+(?=[^A-Da-d][\.:\)])',  # Number not followed by option letter
    ]
    
    question_blocks = []
    used_pattern = None
    
    for pattern in question_patterns:
        blocks = re.split(pattern, text, flags=re.IGNORECASE)
        # Filter out empty blocks and headers
        blocks = [b.strip() for b in blocks if b.strip() and len(b.strip()) > 20]
        if len(blocks) >= 1:
            question_blocks = blocks
            used_pattern = pattern
            break
    
    if not question_blocks:
        # Fallback: split by double newlines and filter for question-like content
        blocks = text.split('\n\n')
        question_blocks = [b.strip() for b in blocks if len(b.strip()) > 30]
    
    
    for i, block in enumerate(question_blocks):
        try:
            block = block.strip()
            if len(block) < 30:  # Too short to be valid
                continue
            
            # Pre-process: handle code blocks by marking them
            code_blocks = {}
            code_counter = 0
            
            def store_code(match):
                nonlocal code_counter
                key = f"__CODE_BLOCK_{code_counter}__"
                code_blocks[key] = match.group(0)
                code_counter += 1
                return key
            
            # Temporarily replace code blocks
            block_processed = re.sub(r'```[\s\S]*?```', store_code, block)
            block_processed = re.sub(r'`[^`]+`', store_code, block_processed)
            
            lines = [line.strip() for line in block_processed.split('\n') if line.strip()]
            if not lines:
                continue
            
            # Extract question text - accumulate until we hit options
            question_lines = []
            options_start_idx = 0
            in_question = True
            
            for idx, line in enumerate(lines):
                if not line:
                    continue
                
                # Check if this is an option line (more strict check)
                is_option = bool(re.match(r'^[A-D][\.\)]\s+\S', line)) or \
                           bool(re.match(r'^\([A-D]\)\s+\S', line)) or \
                           bool(re.match(r'^[A-D]:\s+\S', line))
                
                is_metadata = bool(re.match(r'^(Correct|Answer|Explanation|Reason)[\s:]', line, re.IGNORECASE))
                
                if is_option or is_metadata:
                    in_question = False
                    if is_option and options_start_idx == 0:
                        options_start_idx = idx
                    break
                
                if in_question and len(line) > 5:
                    # Restore code blocks in question text
                    for key, code in code_blocks.items():
                        line = line.replace(key, code)
                    question_lines.append(line)
            
            # Restore code blocks in all lines for option processing
            def restore_codes(line):
                for key, code in code_blocks.items():
                    line = line.replace(key, code)
                return line
            
            lines = [restore_codes(line) for line in lines]
            
            # Construct question text
            if question_lines:
                question_text = ' '.join(question_lines).strip()
                # Clean up: remove "Question X:" prefix if still present
                question_text = re.sub(r'^Question\s*\d+\s*[\.:\)]\s*', '', question_text, flags=re.IGNORECASE)
                question_text = re.sub(r'^Q\s*\d+\s*[\.:\)]\s*', '', question_text, flags=re.IGNORECASE)
            else:
                question_text = lines[0][:200] if lines else "Unknown Question"
                options_start_idx = 1
            
            # Validate question text
            if len(question_text) < 10 or question_text.lower() in ['question', 'q']:
                continue
            
            # Parse options with strict patterns
            options = {}
            correct = None
            explanation_lines = []
            
            option_patterns = [
                r'^([A-D])[\.]\s*(.+)$',      # A. text
                r'^([A-D])[\)]\s*(.+)$',       # A) text  
                r'^\(([A-D])\)\s*(.+)$',       # (A) text
                r'^([A-D]):\s*(.+)$',          # A: text
                r'^([A-D])\s+(.+)$',           # A text (space separated)
            ]
            
            parsing_options = True
            
            for line in lines[options_start_idx:]:
                line = line.strip()
                if not line:
                    continue
                
                # Try to match option (only if we haven't found 4 options yet)
                if parsing_options and len(options) < 4:
                    matched = False
                    for pattern in option_patterns:
                        match = re.match(pattern, line, re.IGNORECASE)
                        if match:
                            key, value = match.groups()
                            key = key.upper()
                            
                            # Clean up value - stop at metadata markers
                            value = re.split(r'\s+(?:Correct|Answer|Explanation|Reason)[\s:]', value, flags=re.IGNORECASE)[0]
                            value = value.strip()
                            
                            if key not in options and len(value) > 0:
                                options[key] = value[:150]
                                matched = True
                                break
                    
                    if matched:
                        continue
                    else:
                        if len(options) > 0:
                            parsing_options = False
                
                # Look for correct answer
                correct_match = re.search(r'(?:Correct|Answer)[\s:]+([A-D])', line, re.IGNORECASE)
                if correct_match:
                    correct = correct_match.group(1).upper()
                    continue
                
                # Look for explanation start
                expl_match = re.match(r'(?:Explanation|Reason)[\s:]+(.+)', line, re.IGNORECASE)
                if expl_match:
                    explanation_lines.append(expl_match.group(1).strip())
                    continue
                
                # Continue explanation if we're in explanation mode
                if explanation_lines and not re.match(r'^[A-D][\.\)]', line):
                    explanation_lines.append(line)
            
            # Build explanation
            explanation = ' '.join(explanation_lines).strip() if explanation_lines else ""
            
            # Validation - CRITICAL: Must have at least 2 options
            if len(options) < 2:
                print(f"WARNING: Block {i} has only {len(options)} options, skipping")
                continue
            
            # Fill missing options
            if len(options) < 4:
                print(f"WARNING: Question {i+1} missing options, filling placeholders")
                for key in ['A', 'B', 'C', 'D']:
                    if key not in options:
                        options[key] = f"Option {key}"
            
            # Validate correct answer
            if not correct or correct not in options:
                inferred = re.search(r'\boption\s+([A-D])\b', explanation, re.IGNORECASE)
                if inferred and inferred.group(1).upper() in options:
                    correct = inferred.group(1).upper()
                    print(f"Inferred correct answer {correct} from explanation")
                else:
                    print(f"WARNING: Question {i+1}: No valid correct answer, defaulting to A")
                    correct = 'A'
            
            if not explanation:
                explanation = f"The correct answer is {correct}. Review the related concepts to understand why."
            
            question_text = question_text[:1000].strip()
            
            questions.append({
                'question': question_text[:1000].strip(),  # Remove html.escape()
                'options': {
                    'A': options.get('A', 'Option A')[:120],  # Remove html.escape()
                    'B': options.get('B', 'Option B')[:120],
                    'C': options.get('C', 'Option C')[:120],
                    'D': options.get('D', 'Option D')[:120]
                },
                'correct': correct,
                'explanation': explanation[:350]  # Remove html.escape()
            })
            
        except Exception as e:
            print(f"ERROR parsing question block {i}: {e}")
            continue
    
    return questions

def generate_quiz_with_llm(topic_id, difficulty='mixed', num_questions=5):
    """Generate quiz using OpenRouter OpenAI GPT-OSS-120B"""
    topic = get_topic_by_id(topic_id)
    if not topic:
        return None
    
    template = QUIZ_TEMPLATES['templates'].get(topic_id, {})
    prompt_template = template.get('prompt_template', 
        f"Generate {{count}} multiple choice questions about {{difficulty}} level {topic['title']}.")
    
    subtopics_str = ', '.join([st['name'] for st in topic['subtopics']])
    concepts_str = ', '.join([c for st in topic['subtopics'] for c in st['concepts'][:3]])
    
    prompt = f"""Generate exactly {num_questions} multiple choice questions about {topic['title']} at {difficulty} difficulty level.

TOPICS TO COVER: {subtopics_str}
KEY CONCEPTS: {concepts_str}

STRICT FORMAT FOR EACH QUESTION:

Question 1: [Clear, specific question text here]
A) [First option - make it plausible]
B) [Second option - make it plausible]
C) [Third option - make it plausible] 
D) [Fourth option - make it plausible]
Correct: [A/B/C/D]
Explanation: [2-3 sentences explaining why the correct answer is right and why others are wrong]

Question 2: [Next question...]
[Same format as above]

IMPORTANT RULES:
1. Use EXACT format shown above with "Question X:", "A)", "B)", "C)", "D)", "Correct:", "Explanation:"
2. Each question MUST have exactly 4 options labeled A, B, C, D
3. Questions should be practical and test understanding, not just memorization
4. Include code snippets where relevant
5. Make sure "Correct:" clearly states which option (A, B, C, or D) is correct
6. For code questions, put code in triple backticks with actual newlines, NOT inline
7. Explanations should teach the concept
8. Do not use markdown formatting like ** or ##
9. Ensure options are complete sentences or code, not single words when possible

Generate {num_questions} questions now following this exact format:"""
    
    response_text = call_openrouter(prompt, temperature=0.8, max_tokens=4000)
    
    if not response_text:
        print("No response from LLM, using fallback")
        return get_fallback_quiz(topic_id, difficulty, num_questions)
    
    questions = parse_quiz_from_llm_response(response_text)
    
    if len(questions) < num_questions:
        print(f"Only got {len(questions)} questions, using fallback for rest")
        if len(questions) == 0:
            return get_fallback_quiz(topic_id, difficulty, num_questions)
        # Pad with fallback questions
        fallback = get_fallback_quiz(topic_id, difficulty, num_questions - len(questions))
        if fallback:
            questions.extend(fallback['questions'][:num_questions - len(questions)])
    
    template_data = QUIZ_TEMPLATES['templates'].get(topic_id, {})
    time_per_q = template_data.get('time_per_question', 3)
    
    return {
        'title': template_data.get('title', f"{topic['title']} Quiz"),
        'description': f"AI-generated {difficulty} difficulty quiz on {topic['title']}",
        'time_limit': num_questions * time_per_q,
        'questions': questions[:num_questions],
        'generated_at': datetime.now().isoformat(),
        'difficulty': difficulty
    }

def get_fallback_quiz(topic_id, difficulty, num_questions):
    """Get fallback quiz from templates"""
    fallback = QUIZ_TEMPLATES['fallback_quizzes'].get(topic_id)
    if not fallback:
        # Generic fallback
        return {
            'title': f"{topic_id.replace('-', ' ').title()} Quiz",
            'description': "Basic quiz on fundamental concepts",
            'time_limit': num_questions * 3,
            'questions': [
                {
                    'question': f'What is a key concept in {topic_id.replace("-", " ")}?',
                    'options': {
                        'A': 'Fundamental understanding required',
                        'B': 'Advanced optimization technique',
                        'C': 'Memory management strategy',
                        'D': 'Algorithm design pattern'
                    },
                    'correct': 'A',
                    'explanation': 'This tests basic conceptual understanding of the topic.'
                }
            ] * num_questions,
            'generated_at': datetime.now().isoformat(),
            'difficulty': difficulty,
            'fallback': True
        }
    
    questions = fallback['questions'][:num_questions]
    # Duplicate if needed
    while len(questions) < num_questions:
        questions.extend(fallback['questions'][:num_questions - len(questions)])
    
    return {
        'title': fallback['title'],
        'description': fallback['description'] + " (Offline Mode)",
        'time_limit': fallback.get('time_limit', num_questions * 3),
        'questions': questions[:num_questions],
        'generated_at': datetime.now().isoformat(),
        'difficulty': difficulty,
        'fallback': True
    }

@app.route('/')
def index():
    quiz_progress = session.get('quiz_progress', {})
    return render_template('index.html', topics=DSA_CONTENT['topics'], quiz_progress=quiz_progress)

@app.route('/topic/<topic_id>')
def topic(topic_id):
    topic_data = get_topic_by_id(topic_id)
    if not topic_data:
        return "Topic not found", 404
    
    quiz_score = session.get('quiz_progress', {}).get(topic_id, None)
    return render_template('topic.html', topic=topic_data, quiz_score=quiz_score)

@app.route('/generate-quiz/<topic_id>', methods=['GET', 'POST'])
def generate_quiz_page(topic_id):
    topic_data = get_topic_by_id(topic_id)
    if not topic_data:
        return "Topic not found", 404
    
    if request.method == 'POST':
        difficulty = request.form.get('difficulty', 'mixed')
        num_questions = int(request.form.get('num_questions', 5))
        
        quiz_data = generate_quiz_with_llm(topic_id, difficulty, num_questions)
        
        if not quiz_data:
            return "Failed to generate quiz", 500
        
        session['current_quiz'] = {
            'topic_id': topic_id,
            'quiz_data': quiz_data,
            'start_time': datetime.now().isoformat(),
            'answers': {}
        }
        
        return redirect(url_for('take_quiz', topic_id=topic_id))
    
    return render_template('generate_quiz.html', topic=topic_data)

@app.route('/quiz/<topic_id>')
def take_quiz(topic_id):
    quiz_session = session.get('current_quiz')
    
    if not quiz_session or quiz_session.get('topic_id') != topic_id:
        quiz_data = generate_quiz_with_llm(topic_id, 'mixed', 5)
        if not quiz_data:
            return "Failed to generate quiz", 500
        
        session['current_quiz'] = {
            'topic_id': topic_id,
            'quiz_data': quiz_data,
            'start_time': datetime.now().isoformat(),
            'answers': {}
        }
        quiz_session = session['current_quiz']
    
    quiz_data = quiz_session['quiz_data']
    topic_data = get_topic_by_id(topic_id)

    for q in quiz_data['questions']:
        q['question_html'] = markdown.markdown(q['question'], extensions=['fenced_code', 'nl2br'])
    
    # DEBUG: Print quiz data
    for i, q in enumerate(quiz_data['questions']):
        print(f"Q{i+1}: {q['question'][:50]}... Options: {list(q['options'].keys())}")
    
    return render_template('quiz.html', 
                         topic=topic_data, 
                         quiz=quiz_data, 
                         questions=quiz_data['questions'])

@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    user_answers = data.get('answers', {})
    
    print(f"Received answers: {user_answers}")  # Debug
    
    quiz_session = session.get('current_quiz')
    if not quiz_session:
        return jsonify({'error': 'No active quiz session'}), 400
    
    quiz_data = quiz_session['quiz_data']
    questions = quiz_data['questions']
    topic_id = quiz_session['topic_id']
    
    
    correct_count = 0
    results = []
    
    for i, question in enumerate(questions):
        user_answer = user_answers.get(str(i), '').upper()
        correct_answer = question['correct'].upper()
        is_correct = user_answer == correct_answer
        
        
        if is_correct:
            correct_count += 1
        
        results.append({
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'explanation': question.get('explanation', ''),
            'options': question['options']
        })
    
    score = (correct_count / len(questions)) * 100 if questions else 0
    passed = score >= 70
    
    quiz_progress = session.get('quiz_progress', {})
    prev_best = quiz_progress.get(topic_id, {}).get('score', 0)
    
    if topic_id not in quiz_progress or score > prev_best:
        quiz_progress[topic_id] = {
            'score': round(score, 1),
            'correct': correct_count,
            'total': len(questions),
            'passed': passed,
            'last_attempt': datetime.now().isoformat(),
            'difficulty': quiz_data.get('difficulty', 'mixed')
        }
        session['quiz_progress'] = quiz_progress
        improved = score > prev_best
    else:
        improved = False
    
    session.pop('current_quiz', None)
    
    return jsonify({
        'score': round(score, 1),
        'correct': correct_count,
        'total': len(questions),
        'passed': passed,
        'improved': improved,
        'previous_best': prev_best if topic_id in quiz_progress else 0,
        'results': results,
        'topic_id': topic_id,
        'generated_at': quiz_data.get('generated_at'),
        'was_fallback': quiz_data.get('fallback', False)
    })

@app.route('/api/regenerate-quiz', methods=['POST'])
def regenerate_quiz():
    data = request.json
    topic_id = data.get('topic_id')
    difficulty = data.get('difficulty', 'mixed')
    num_questions = data.get('num_questions', 5)
    
    if not topic_id:
        return jsonify({'error': 'Topic ID required'}), 400
    
    quiz_data = generate_quiz_with_llm(topic_id, difficulty, num_questions)
    
    if not quiz_data:
        return jsonify({'error': 'Failed to generate quiz'}), 500
    
    session['current_quiz'] = {
        'topic_id': topic_id,
        'quiz_data': quiz_data,
        'start_time': datetime.now().isoformat(),
        'answers': {}
    }
    
    return jsonify({
        'success': True,
        'redirect': f'/quiz/{topic_id}'
    })

@app.route('/api/explain', methods=['POST'])
def explain_concept():
    data = request.json
    concept = data.get('concept', '')
    context = data.get('context', '')
    difficulty = data.get('difficulty', 'beginner')
    
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'AI service not configured'}), 503
    
    prompt = f"""
    You are an expert DSA instructor teaching a {difficulty}-level student.
    
    Topic: {concept}
    Context: {context}
    
    Provide a comprehensive explanation including:
    1. Intuitive understanding (real-world analogy)
    2. Formal definition
    3. Step-by-step algorithm explanation
    4. Time and space complexity analysis
    5. Common pitfalls and how to avoid them
    6. When to use this data structure/algorithm
    
    Format with clear headings and code examples where relevant.
    Keep it engaging and educational.

    IMPORTANT TABLE FORMATTING RULES:
    - Tables MUST have proper markdown syntax
    - Each row on its own line
    - Header separator line required: |---|---|
    - Example:
    | Column1 | Column2 |
    |---------|---------|
    | Value1  | Value2  |
    """
    
    response_text = call_openrouter(prompt, temperature=0.7, max_tokens=8000)
    
    if not response_text:
        return jsonify({'error': 'Failed to get AI explanation'}), 500
    
    explanation = markdown.markdown(response_text, extensions=['tables', 'fenced_code'])
    return jsonify({'explanation': explanation})

@app.route('/api/code-help', methods=['POST'])
def code_help():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')
    issue = data.get('issue', '')
    
    if not OPENROUTER_API_KEY:
        return jsonify({'error': 'AI service not configured'}), 503
    
    prompt = f"""
    You are a code reviewer and debugging assistant. Analyze the following {language} code:
    
    ```{language}
    {code}
    ```
    
    Issue/Question: {issue}
    
    Provide:
    1. Code review and potential bugs
    2. Optimization suggestions
    3. Explanation of the logic
    4. Corrected code if needed
    
    Be constructive and educational.
    """
    
    response_text = call_openrouter(prompt, temperature=0.7, max_tokens=1500)
    
    if not response_text:
        return jsonify({'error': 'Failed to analyze code'}), 500
    
    return jsonify({'analysis': markdown.markdown(response_text, extensions=['tables', 'fenced_code'])})

@app.route('/practice')
def practice():
    return render_template('practice.html', problems=DSA_CONTENT['practice_problems'])

@app.route('/leaderboard')
def leaderboard():
    mock_leaderboard = [
        {'name': 'Alice', 'score': 95, 'topic': 'Arrays & Strings'},
        {'name': 'Bob', 'score': 90, 'topic': 'Dynamic Programming'},
        {'name': 'Charlie', 'score': 88, 'topic': 'Graphs'},
    ]
    return render_template('leaderboard.html', leaderboard=mock_leaderboard)

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    app.run(debug=True, port=5000)
