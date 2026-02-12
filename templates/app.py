from flask import Flask, request, redirect, session, send_file, jsonify, make_response, render_template, url_for
from functools import wraps
import os
from datetime import datetime, timedelta
import json, io
from database import get_legacy_db, init_db, create_sample_questions
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = "quiz_secret"

# Initialize database
init_db()
create_sample_questions()

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

# ==================== MAIN APPLICATION ROUTES ====================

@app.route("/")
def home():
    """Main home page with quiz interface"""
    return send_file('templates/simple_home.html')

@app.route("/quiz")
def quiz():
    """Quiz page"""
    return send_file('quiz-app.html')

@app.route("/result")
def result():
    """Result page"""
    return send_file('templates/result.html')

@app.route("/leaderboard")
def leaderboard():
    """Leaderboard page"""
    return send_file('templates/admin_dashboard.html')

# ==================== ADMIN ROUTES ====================

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper hashing)
        if username == 'admin' and password == '2026':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect('/admin/dashboard')
        else:
            error = 'Invalid credentials'
    else:
        error = None
    
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login - Quiz Management System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .login-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                width: 100%;
                max-width: 400px;
            }

            .logo {
                text-align: center;
                margin-bottom: 30px;
            }

            .logo i {
                font-size: 3rem;
                color: #667eea;
                margin-bottom: 10px;
            }

            .form-control {
                border-radius: 10px;
                border: 2px solid #e0e0e0;
                padding: 12px 15px;
                transition: all 0.3s ease;
            }

            .form-control:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .btn-login {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 10px;
                padding: 12px;
                color: white;
                font-weight: 600;
                width: 100%;
                transition: all 0.3s ease;
            }

            .btn-login:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }

            .alert {
                border-radius: 10px;
                border: none;
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from { transform: translateY(-10px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }

            .input-icon {
                position: relative;
            }

            .input-icon i {
                position: absolute;
                left: 15px;
                top: 50%;
                transform: translateY(-50%);
                color: #999;
            }

            .input-icon .form-control {
                padding-left: 45px;
            }

            .back-link {
                text-align: center;
                margin-top: 20px;
            }

            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }

            .back-link a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <i class="bi bi-shield-lock"></i>
                <h2>Admin Login</h2>
            </div>

            ''' + (f'''
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                {error}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            ''' if error else '') + '''

            <form method="POST">
                <div class="mb-3">
                    <div class="input-icon">
                        <i class="bi bi-person"></i>
                        <input type="text" class="form-control" name="username" placeholder="Admin Username" required>
                    </div>
                </div>

                <div class="mb-3">
                    <div class="input-icon">
                        <i class="bi bi-lock"></i>
                        <input type="password" class="form-control" name="password" placeholder="Admin Password" required>
                    </div>
                </div>

                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="remember" name="remember">
                        <label class="form-check-label" for="remember">
                            Remember me
                        </label>
                    </div>
                </div>

                <button type="submit" class="btn btn-login">
                    <i class="bi bi-box-arrow-in-right"></i> Login to Admin Panel
                </button>
            </form>

            <div class="back-link">
                <a href="/">
                    <i class="bi bi-arrow-left"></i> Back to Home
                </a>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.clear()
    return redirect('/admin/login')

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Main admin dashboard"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/questions")
@admin_required
def admin_questions():
    """Question management page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/leaderboard")
@admin_required
def admin_leaderboard():
    """Leaderboard management page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/medals")
@admin_required
def admin_medals():
    """Medals management page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/users")
@admin_required
def admin_users():
    """User management page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/analytics")
@admin_required
def admin_analytics():
    """Analytics page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/settings")
@admin_required
def admin_settings():
    """Settings page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/logs")
@admin_required
def admin_logs():
    """Logs page"""
    return send_file('templates/admin_dashboard.html')

@app.route("/admin/backup")
@admin_required
def admin_backup():
    """Backup page"""
    return send_file('templates/admin_dashboard.html')

# ==================== API ENDPOINTS ====================

@app.route("/api/quiz/start", methods=['POST'])
def start_quiz():
    """Start a new quiz session"""
    try:
        data = request.get_json()
        username = data.get('username', 'Anonymous')
        category = data.get('category', 'all')
        difficulty = data.get('difficulty', 'easy')
        
        # Get questions from database
        conn = get_legacy_db()
        cur = conn.cursor()
        
        if category == 'all':
            cur.execute("SELECT * FROM questions WHERE difficulty = ? ORDER BY RANDOM() LIMIT 10", (difficulty,))
        else:
            cur.execute("SELECT * FROM questions WHERE difficulty = ? AND category = ? ORDER BY RANDOM() LIMIT 10", 
                       (difficulty, category))
        
        questions = cur.fetchall()
        conn.close()
        
        if not questions:
            return jsonify({'error': 'No questions found'}), 404
        
        # Convert to list of dictionaries
        question_list = []
        for q in questions:
            question_list.append({
                'id': q[0],
                'question': q[1],
                'options': json.loads(q[2]),
                'correct': q[3],
                'difficulty': q[4]
            })
        
        # Store session data
        session['quiz_session'] = {
            'username': username,
            'category': category,
            'difficulty': difficulty,
            'questions': question_list,
            'current_question': 0,
            'score': 0,
            'answers': [],
            'start_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'questions': question_list,
            'total_questions': len(question_list)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/quiz/answer", methods=['POST'])
def submit_answer():
    """Submit answer for current question"""
    try:
        if 'quiz_session' not in session:
            return jsonify({'error': 'No active quiz session'}), 400
        
        data = request.get_json()
        answer = data.get('answer')
        
        quiz_session = session['quiz_session']
        current_q = quiz_session['current_question']
        questions = quiz_session['questions']
        
        if current_q >= len(questions):
            return jsonify({'error': 'Quiz already completed'}), 400
        
        # Check answer
        correct_answer = questions[current_q]['correct']
        is_correct = answer == correct_answer
        
        # Update score
        if is_correct:
            quiz_session['score'] += 1
        
        # Store answer
        quiz_session['answers'].append({
            'question_id': questions[current_q]['id'],
            'user_answer': answer,
            'is_correct': is_correct
        })
        
        # Move to next question
        quiz_session['current_question'] += 1
        
        # Save to database
        conn = get_legacy_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO scores (username, score, total, time, created) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            quiz_session['username'],
            quiz_session['score'],
            len(questions),
            0,  # Will be calculated when quiz ends
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()
        
        # Check if quiz is completed
        is_completed = quiz_session['current_question'] >= len(questions)
        
        response = {
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'current_question': quiz_session['current_question'],
            'score': quiz_session['score'],
            'is_completed': is_completed
        }
        
        if is_completed:
            # Calculate final results
            start_time = datetime.fromisoformat(quiz_session['start_time'])
            end_time = datetime.now()
            time_taken = int((end_time - start_time).total_seconds())
            
            response.update({
                'final_score': quiz_session['score'],
                'total_questions': len(questions),
                'percentage': round((quiz_session['score'] / len(questions)) * 100, 2),
                'time_taken': time_taken
            })
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/leaderboard")
def get_leaderboard():
    """Get leaderboard data"""
    try:
        conn = get_legacy_db()
        cur = conn.cursor()
        
        difficulty = request.args.get('difficulty', 'all')
        limit = int(request.args.get('limit', 10))
        
        if difficulty == 'all':
            cur.execute("""
                SELECT username, score, total, created 
                FROM scores 
                ORDER BY score DESC, created DESC 
                LIMIT ?
            """, (limit,))
        else:
            cur.execute("""
                SELECT username, score, total, created 
                FROM scores 
                WHERE id IN (
                    SELECT id FROM scores WHERE difficulty = ?
                )
                ORDER BY score DESC, created DESC 
                LIMIT ?
            """, (difficulty, limit))
        
        results = cur.fetchall()
        conn.close()
        
        leaderboard = []
        for i, row in enumerate(results, 1):
            leaderboard.append({
                'rank': i,
                'username': row[0],
                'score': row[1],
                'total': row[2],
                'percentage': round((row[1] / row[2]) * 100, 2) if row[2] > 0 else 0,
                'date': row[3]
            })
        
        return jsonify({'leaderboard': leaderboard})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/stats")
@admin_required
def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        conn = get_legacy_db()
        cur = conn.cursor()
        
        # Get basic stats
        cur.execute("SELECT COUNT(*) FROM questions")
        total_questions = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT username) FROM scores")
        total_users = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM scores")
        total_attempts = cur.fetchone()[0]
        
        cur.execute("SELECT AVG(score * 100.0 / total) FROM scores WHERE total > 0")
        avg_score = cur.fetchone()[0] or 0
        
        # Get recent activity
        cur.execute("""
            SELECT username, score, total, created 
            FROM scores 
            ORDER BY created DESC 
            LIMIT 5
        """)
        recent_activity = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            'total_questions': total_questions,
            'total_users': total_users,
            'total_attempts': total_attempts,
            'avg_score': round(avg_score, 2),
            'recent_activity': [
                {
                    'username': row[0],
                    'score': row[1],
                    'total': row[2],
                    'date': row[3]
                } for row in recent_activity
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/questions", methods=['GET', 'POST', 'PUT', 'DELETE'])
@admin_required
def manage_questions():
    """Manage questions CRUD operations"""
    try:
        conn = get_legacy_db()
        cur = conn.cursor()
        
        if request.method == 'GET':
            # Get all questions
            cur.execute("SELECT * FROM questions ORDER BY id DESC")
            questions = cur.fetchall()
            
            question_list = []
            for q in questions:
                question_list.append({
                    'id': q[0],
                    'question': q[1],
                    'options': json.loads(q[2]),
                    'correct': q[3],
                    'difficulty': q[4]
                })
            
            conn.close()
            return jsonify({'questions': question_list})
        
        elif request.method == 'POST':
            # Add new question
            data = request.get_json()
            cur.execute("""
                INSERT INTO questions (question, options, correct, difficulty) 
                VALUES (?, ?, ?, ?)
            """, (
                data['question'],
                json.dumps(data['options']),
                data['correct'],
                data['difficulty']
            ))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Question added successfully'})
        
        elif request.method == 'PUT':
            # Update question
            data = request.get_json()
            cur.execute("""
                UPDATE questions 
                SET question = ?, options = ?, correct = ?, difficulty = ? 
                WHERE id = ?
            """, (
                data['question'],
                json.dumps(data['options']),
                data['correct'],
                data['difficulty'],
                data['id']
            ))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Question updated successfully'})
        
        elif request.method == 'DELETE':
            # Delete question
            question_id = request.args.get('id')
            cur.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Question deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/users")
@admin_required
def get_users():
    """Get all users"""
    try:
        conn = get_legacy_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT username, 
                   COUNT(*) as total_quizzes,
                   MAX(score) as best_score,
                   AVG(score * 100.0 / total) as avg_accuracy,
                   MAX(created) as last_activity
            FROM scores 
            GROUP BY username 
            ORDER BY total_quizzes DESC
        """)
        
        users = cur.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'username': user[0],
                'total_quizzes': user[1],
                'best_score': user[2],
                'avg_accuracy': round(user[3] or 0, 2),
                'last_activity': user[4]
            })
        
        return jsonify({'users': user_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/export")
@admin_required
def export_data():
    """Export data as CSV"""
    try:
        export_type = request.args.get('type', 'scores')
        
        conn = get_legacy_db()
        cur = conn.cursor()
        
        if export_type == 'scores':
            cur.execute("SELECT username, score, total, created FROM scores ORDER BY created DESC")
            data = cur.fetchall()
            headers = ['Username', 'Score', 'Total', 'Date']
        elif export_type == 'questions':
            cur.execute("SELECT * FROM questions ORDER BY id")
            data = cur.fetchall()
            headers = ['ID', 'Question', 'Options', 'Correct', 'Difficulty']
        else:
            return jsonify({'error': 'Invalid export type'}), 400
        
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{export_type}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/analytics")
@admin_required
def get_analytics():
    """Get analytics data"""
    try:
        conn = get_legacy_db()
        cur = conn.cursor()
        
        # Daily quiz attempts for last 7 days
        cur.execute("""
            SELECT DATE(created) as date, COUNT(*) as attempts
            FROM scores 
            WHERE created >= date('now', '-7 days')
            GROUP BY DATE(created)
            ORDER BY date
        """)
        daily_attempts = cur.fetchall()
        
        # Performance by difficulty
        cur.execute("""
            SELECT difficulty, AVG(score * 100.0 / total) as avg_score, COUNT(*) as count
            FROM scores s
            JOIN questions q ON s.question_id = q.id
            GROUP BY difficulty
        """)
        difficulty_performance = cur.fetchall()
        
        # Top categories
        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM questions
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        """)
        top_categories = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            'daily_attempts': [{'date': row[0], 'attempts': row[1]} for row in daily_attempts],
            'difficulty_performance': [{'difficulty': row[0], 'avg_score': row[1], 'count': row[2]} for row in difficulty_performance],
            'top_categories': [{'category': row[0], 'count': row[1]} for row in top_categories]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/logs")
@admin_required
def get_logs():
    """Get system logs"""
    try:
        # For now, return recent quiz activities as logs
        conn = get_legacy_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 'Quiz Completed' as action, username, 
                   score || '/' || total as details, created
            FROM scores 
            ORDER BY created DESC 
            LIMIT 50
        """)
        
        logs = cur.fetchall()
        conn.close()
        
        return jsonify({
            'logs': [
                {
                    'action': row[0],
                    'user': row[1],
                    'details': row[2],
                    'timestamp': row[3]
                } for row in logs
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/backup", methods=['POST'])
@admin_required
def create_backup():
    """Create database backup"""
    try:
        import shutil
        from datetime import datetime
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"quiz_backup_{timestamp}.db"
        backup_path = os.path.join("backups", backup_filename)
        
        # Create backups directory if it doesn't exist
        os.makedirs("backups", exist_ok=True)
        
        # Copy database file
        shutil.copy2("quiz.db", backup_path)
        
        return jsonify({
            'success': True,
            'message': f'Backup created successfully: {backup_filename}',
            'filename': backup_filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/settings", methods=['GET', 'POST'])
@admin_required
def manage_settings():
    """Manage system settings"""
    try:
        if request.method == 'GET':
            # Return current settings (for now, return defaults)
            return jsonify({
                'questions_per_quiz': 10,
                'time_limit': 30,
                'passing_score': 60,
                'allow_negative_marking': False,
                'show_correct_answers': True
            })
        
        elif request.method == 'POST':
            # Update settings (for now, just return success)
            data = request.get_json()
            # In a real implementation, you would save these to a settings file or database
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/admin/medals")
@admin_required
def get_medals():
    """Get medals/achievements data"""
    try:
        conn = get_legacy_db()
        cur = conn.cursor()
        
        # Get medal statistics
        cur.execute("""
            SELECT 
                CASE 
                    WHEN score * 100.0 / total >= 90 THEN 'Gold'
                    WHEN score * 100.0 / total >= 75 THEN 'Silver'
                    WHEN score * 100.0 / total >= 60 THEN 'Bronze'
                    ELSE 'None'
                END as medal,
                COUNT(*) as count
            FROM scores
            WHERE total > 0
            GROUP BY medal
            ORDER BY 
                CASE medal
                    WHEN 'Gold' THEN 1
                    WHEN 'Silver' THEN 2
                    WHEN 'Bronze' THEN 3
                    WHEN 'None' THEN 4
                END
        """)
        
        medal_stats = cur.fetchall()
        conn.close()
        
        return jsonify({
            'medals': [
                {'type': row[0], 'count': row[1]} for row in medal_stats
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== STATIC FILES AND ASSETS ====================

@app.route("/favicon.ico")
def favicon():
    """Serve favicon"""
    return '', 204

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files"""
    return send_file(os.path.join('static', filename))

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
