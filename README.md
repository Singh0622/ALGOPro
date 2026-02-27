# ALGOPro - AI-Powered DSA Learning Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**ALGOPro** is an intelligent learning platform that transforms how students master Data Structures and Algorithms through AI-generated personalized content, adaptive quizzes, and real-time assistance.

![Platform Screenshot](screenshot.png)

## 🎯 Problem Statement

Students face critical challenges in self-directed learning:
- **Complex concepts** are difficult to grasp without personalized explanations
- **Online searches** yield irrelevant or overly advanced results
- **Teachers are unavailable** 24/7 for immediate doubt resolution
- **Static quiz banks** lead to memorization rather than understanding
- **Fragmented tools** waste time switching between platforms

## ✨ Solution Overview

ALGOPro addresses these challenges through:

| Feature | Description |
|---------|-------------|
| 🤖 **AI Tutor** | Explains concepts in Beginner/Intermediate/Advanced terms |
| 📝 **Dynamic Quizzes** | Unlimited AI-generated questions prevent memorization |
| 💻 **Code Analysis** | Instant debugging help and optimization suggestions |
| 📊 **Progress Tracking** | Visual analytics identify strengths and weaknesses |
| 🎥 **Video Integration** | Curated content with AI-powered explanations |

## 🚀 Live Demo

**Deployed Application:** [https://algopro.onrender.com](https://algopro-ena1.onrender.com)


## 🛠️ Tech Stack

### Backend
- **Python 3.8+** - Core language
- **Flask** - Web framework
- **OpenRouter API** - LLM integration (GPT-OSS-120B)
- **Markdown** - Content rendering

### Frontend
- **HTML5 + Jinja2** - Templating
- **Bootstrap 5** - Responsive UI
- **Chart.js** - Data visualization
- **Highlight.js** - Code syntax highlighting

### AI Integration
- **Multi-pattern regex parser** - Handles diverse LLM outputs
- **Dynamic prompt engineering** - Context-aware quiz generation
- **Response sanitization** - XSS protection

## 📁 Project Structure

ALGOPro/

      ├── app.py                      # Main Flask application
      ├── requirements.txt            # Python dependencies
      ├── .env                        # Environment variables (not in repo)
      ├── .env.example                # Environment template
      ├── .gitignore                  # Git ignore rules
      ├── data/
      │   ├── dsa_content.json        # Topic structure & metadata
      │   └── quiz_templates.json     # Quiz generation templates
      ├── templates/                  # Jinja2 HTML templates
      │   ├── base.html
      │   ├── index.html
      │   ├── topic.html
      │   ├── quiz.html
      │   ├── practice.html
      │   └── generate_quiz.html
      └── static/
      ├── css/style.css          # Custom styles
      └── js/main.js             # Client-side logic


## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Git
- OpenRouter API key ([Get one free](https://openrouter.ai))

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ALGOPro.git
   cd ALGOPro

2. **Create virtual environment**
   python -m venv venv

    Windows-
    venv\Scripts\activate

    Mac/Linux-
    source venv/bin/activate
3. **Install dependencies**
    pip install -r requirements.txt

4. **Configure environment variables**
    cp .env.example .env
    Edit .env file:
    OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
    FLASK_SECRET_KEY=your-random-secret-key-here

5. **Run the application**
    python app.py

6. **Open in browser**
    http://localhost:5000

🧠 Core Algorithm: LLM Response Parser
The platform's robustness comes from a multi-layer parsing strategy:
    # 1. Multi-pattern question segmentation
patterns = [

          r'Question \d+:',      # "Question 1:"
          r'Q\d+:',              # "Q1:"
          r'#{1,3} Question',    # "### Question 1"
          r'\*\*Question',       # "**Question 1**"
          r'\d+\.'               # "1. What..."
]

2. Code block preservation
Extract ```code``` → placeholders → parse → restore

3. Component extraction
Question text → Options → Correct answer → Explanation

4. Validation & auto-repair
Ensures 4 options, infers missing answers, fills placeholders

Success Rate: Handles 95% of LLM output variations.
📊 Features in Detail

AI-Generated Quizzes
* Unlimited unique questions per topic
* Adaptive difficulty (Easy/Medium/Hard/Mixed)
* Instant feedback with detailed explanations
* Progress tracking across attempts

AI Learning Assistant
* Real-time concept explanations
* Three difficulty levels
* Code snippet examples
* Table and list formatting

Code Analysis Tool
* Paste code for instant review
* Bug detection and fixes
* Optimization suggestions
* Syntax highlighting

Practice Problems
* 50+ curated LeetCode problems
* Filter by category and difficulty
* Direct links to solve
* Local progress tracking

#.🔒 Security Measures

      ✅ API keys stored in environment variables
      ✅ .env excluded from Git (.gitignore)
      ✅ HTML escaping for XSS prevention
      ✅ Session-based user state management
      ✅ No sensitive data in client-side code
