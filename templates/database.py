import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, validates
from sqlalchemy.sql import func
from datetime import datetime
import json
import os

# Database Configuration
DB = "quiz.db"
DATABASE_URL = "sqlite:///quiz.db"
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Legacy compatibility function
def get_legacy_db():
    """Legacy compatibility - returns sqlite3 connection"""
    return sqlite3.connect(DB)

# For backward compatibility
def db():
    """Legacy compatibility - returns sqlite3 connection"""
    return get_legacy_db()

class Question(Base):
    __tablename__ = "advanced_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # Store as JSON array
    correct = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False, default='medium')
    category = Column(String(50), nullable=False, default='General')
    explanation = Column(Text, nullable=True)
    points = Column(Integer, default=10)
    time_limit = Column(Integer, default=30)  # seconds
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    quiz_attempts = relationship("QuizAttempt", back_populates="question")
    
    @validates('difficulty')
    def validate_difficulty(self, key, difficulty):
        valid_difficulties = ['easy', 'medium', 'hard']
        if difficulty not in valid_difficulties:
            raise ValueError(f"Difficulty must be one of: {valid_difficulties}")
        return difficulty
    
    @validates('correct')
    def validate_correct(self, key, correct):
        if not isinstance(correct, int) or correct < 0:
            raise ValueError("Correct answer must be a non-negative integer")
        return correct
    
    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'options': self.options,
            'correct': self.correct,
            'difficulty': self.difficulty,
            'category': self.category,
            'explanation': self.explanation,
            'points': self.points,
            'time_limit': self.time_limit,
            'is_active': self.is_active
        }

class User(Base):
    __tablename__ = "advanced_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    total_quizzes = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    best_score = Column(Integer, default=0)
    average_accuracy = Column(Float, default=0.0)
    total_time_spent = Column(Integer, default=0)  # seconds
    streak_count = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    quiz_sessions = relationship("QuizSession", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    
    @validates('username')
    def validate_username(self, key, username):
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return username
    
    def update_stats(self, score, total, time_spent, accuracy):
        """Update user statistics after a quiz"""
        self.total_quizzes += 1
        self.total_score += score
        self.total_time_spent += time_spent
        
        if score > self.best_score:
            self.best_score = score
        
        # Update average accuracy
        self.average_accuracy = ((self.average_accuracy * (self.total_quizzes - 1)) + accuracy) / self.total_quizzes
        
        # Update experience points and level
        self.experience_points += score
        self.level = 1 + (self.experience_points // 100)  # New level every 100 XP
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'total_quizzes': self.total_quizzes,
            'total_score': self.total_score,
            'best_score': self.best_score,
            'average_accuracy': round(self.average_accuracy, 2),
            'total_time_spent': self.total_time_spent,
            'streak_count': self.streak_count,
            'longest_streak': self.longest_streak,
            'level': self.level,
            'experience_points': self.experience_points,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class QuizSession(Base):
    __tablename__ = "advanced_quiz_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("advanced_users.id"), nullable=False)
    session_token = Column(String(100), unique=True, nullable=False, index=True)
    difficulty = Column(String(20), nullable=False)
    category = Column(String(50), nullable=True)
    total_questions = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    total_possible = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    time_taken = Column(Integer, nullable=False)  # seconds
    streak_count = Column(Integer, default=0)
    powerups_used = Column(JSON, nullable=True)  # Store used powerups
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="quiz_sessions")
    attempts = relationship("QuizAttempt", back_populates="session")
    
    @validates('accuracy')
    def validate_accuracy(self, key, accuracy):
        if not 0 <= accuracy <= 100:
            raise ValueError("Accuracy must be between 0 and 100")
        return accuracy
    
    def complete_session(self):
        """Mark the session as completed"""
        self.is_completed = True
        self.completed_at = func.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'difficulty': self.difficulty,
            'category': self.category,
            'total_questions': self.total_questions,
            'score': self.score,
            'total_possible': self.total_possible,
            'accuracy': round(self.accuracy, 2),
            'time_taken': self.time_taken,
            'streak_count': self.streak_count,
            'powerups_used': self.powerups_used,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_completed': self.is_completed
        }

class QuizAttempt(Base):
    __tablename__ = "advanced_quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("advanced_quiz_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("advanced_questions.id"), nullable=False)
    user_answer = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Integer, nullable=False)  # seconds
    answered_at = Column(DateTime, default=func.now())
    
    # Relationships
    session = relationship("QuizSession", back_populates="attempts")
    question = relationship("Question", back_populates="quiz_attempts")
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'time_taken': self.time_taken,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }

class Achievement(Base):
    __tablename__ = "advanced_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    icon = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    condition_type = Column(String(50), nullable=False)  # score, accuracy, streak, etc.
    condition_value = Column(Float, nullable=False)
    points = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")
    
    def check_condition(self, user_stats):
        """Check if user meets the achievement condition"""
        if self.condition_type == 'score':
            return user_stats.get('score', 0) >= self.condition_value
        elif self.condition_type == 'accuracy':
            return user_stats.get('accuracy', 0) >= self.condition_value
        elif self.condition_type == 'streak':
            return user_stats.get('streak', 0) >= self.condition_value
        elif self.condition_type == 'quizzes':
            return user_stats.get('total_quizzes', 0) >= self.condition_value
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value,
            'points': self.points,
            'is_active': self.is_active
        }

class UserAchievement(Base):
    __tablename__ = "advanced_user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("advanced_users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("advanced_achievements.id"), nullable=False)
    unlocked_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None
        }

class Leaderboard(Base):
    __tablename__ = "advanced_leaderboard"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    time_taken = Column(Integer, nullable=False)
    difficulty = Column(String(20), nullable=False)
    category = Column(String(50), nullable=True)
    achieved_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'score': self.score,
            'accuracy': round(self.accuracy, 2),
            'time_taken': self.time_taken,
            'difficulty': self.difficulty,
            'category': self.category,
            'achieved_at': self.achieved_at.isoformat() if self.achieved_at else None
        }

# Database Functions
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with all tables"""
    # Create legacy tables for simple Flask app first
    conn = get_legacy_db()
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            options TEXT,
            correct INTEGER,
            difficulty TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            score INTEGER,
            total INTEGER,
            time INTEGER,
            created TEXT
        )""")
        conn.commit()
        print("Legacy tables created")
    except Exception as e:
        print(f"Error creating legacy tables: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    # Create SQLAlchemy tables (these will be separate from legacy tables)
    try:
        Base.metadata.create_all(bind=engine)
        print("SQLAlchemy tables created")
    except Exception as e:
        print(f"Error creating SQLAlchemy tables: {e}")
    
    # Create default achievements if they don't exist
    try:
        session = SessionLocal()
        if session.query(Achievement).count() == 0:
            default_achievements = [
                Achievement(name="First Quiz", description="Complete your first quiz", icon="🎯", 
                          category="milestone", condition_type="quizzes", condition_value=1),
                Achievement(name="Quiz Master", description="Complete 10 quizzes", icon="🏆", 
                          category="milestone", condition_type="quizzes", condition_value=10),
                Achievement(name="Perfect Score", description="Get 100% accuracy", icon="💯", 
                          category="performance", condition_type="accuracy", condition_value=100),
                Achievement(name="Speed Demon", description="Complete quiz in under 30 seconds", icon="⚡", 
                          category="performance", condition_type="time", condition_value=30),
                Achievement(name="On Fire", description="Get a streak of 5 correct answers", icon="🔥", 
                          category="performance", condition_type="streak", condition_value=5),
                Achievement(name="High Scorer", description="Score 100 points or more", icon="🌟", 
                          category="performance", condition_type="score", condition_value=100),
            ]
            
            for achievement in default_achievements:
                session.add(achievement)
            
            session.commit()
            print("Default achievements created")
        session.close()
    except Exception as e:
        print(f"Error creating default achievements: {e}")

def create_sample_questions():
    """Create sample questions for testing"""
    # Create for SQLAlchemy system
    session = SessionLocal()
    try:
        if session.query(Question).count() == 0:
            sample_questions = [
                Question(
                    question="What is the capital of France?",
                    options=["Berlin", "Madrid", "Paris", "Rome"],
                    correct=2,
                    difficulty="easy",
                    category="Geography",
                    explanation="Paris has been the capital of France since 987 AD.",
                    points=10,
                    time_limit=30
                ),
                Question(
                    question="What is the largest planet in our solar system?",
                    options=["Earth", "Mars", "Jupiter", "Saturn"],
                    correct=2,
                    difficulty="medium",
                    category="Science",
                    explanation="Jupiter is the largest planet with a mass greater than all other planets combined.",
                    points=20,
                    time_limit=25
                ),
                Question(
                    question="What is the speed of light in vacuum?",
                    options=["299,792 km/s", "199,792 km/s", "399,792 km/s", "99,792 km/s"],
                    correct=0,
                    difficulty="hard",
                    category="Physics",
                    explanation="The speed of light is exactly 299,792,458 meters per second.",
                    points=30,
                    time_limit=20
                ),
                Question(
                    question="Who painted the Mona Lisa?",
                    options=["Van Gogh", "Da Vinci", "Picasso", "Rembrandt"],
                    correct=1,
                    difficulty="medium",
                    category="Art",
                    explanation="Leonardo da Vinci painted the Mona Lisa between 1503 and 1519.",
                    points=20,
                    time_limit=25
                ),
                Question(
                    question="What is 2 + 2?",
                    options=["3", "4", "5", "6"],
                    correct=1,
                    difficulty="easy",
                    category="Mathematics",
                    explanation="2 + 2 = 4 is basic addition.",
                    points=10,
                    time_limit=15
                )
            ]
            
            for question in sample_questions:
                session.add(question)
            
            session.commit()
            print("Sample questions created for SQLAlchemy")
    except Exception as e:
        session.rollback()
        print(f"Error creating SQLAlchemy sample questions: {e}")
    finally:
        session.close()
    
    # Create for legacy system
    conn = get_legacy_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM questions")
        if cur.fetchone()[0] == 0:
            sample_questions_legacy = [
                ("What is the capital of France?", '["Berlin", "Madrid", "Paris", "Rome"]', 2, "easy"),
                ("What is the largest planet in our solar system?", '["Earth", "Mars", "Jupiter", "Saturn"]', 2, "medium"),
                ("What is the speed of light in vacuum?", '["299,792 km/s", "199,792 km/s", "399,792 km/s", "99,792 km/s"]', 0, "hard"),
                ("Who painted the Mona Lisa?", '["Van Gogh", "Da Vinci", "Picasso", "Rembrandt"]', 1, "medium"),
                ("What is 2 + 2?", '["3", "4", "5", "6"]', 1, "easy"),
                ("What is the largest ocean on Earth?", '["Atlantic", "Indian", "Arctic", "Pacific"]', 3, "easy"),
                ("Who wrote Romeo and Juliet?", '["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"]', 1, "medium"),
                ("What is the chemical symbol for gold?", '["Go", "Gd", "Au", "Ag"]', 2, "medium"),
                ("How many continents are there?", '["5", "6", "7", "8"]', 2, "easy"),
                ("What year did World War II end?", '["1943", "1944", "1945", "1946"]', 2, "medium")
            ]
            
            cur.executemany(
                "INSERT INTO questions(question, options, correct, difficulty) VALUES(?, ?, ?, ?)",
                sample_questions_legacy
            )
            conn.commit()
            print("Sample questions created for legacy system")
    finally:
        conn.close()

# Utility Functions
def backup_database():
    """Create a backup of the database"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"quiz_backup_{timestamp}.db"
    
    if os.path.exists("quiz.db"):
        shutil.copy2("quiz.db", backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    return None

def get_database_stats():
    """Get database statistics"""
    session = SessionLocal()
    try:
        stats = {
            'total_questions': session.query(Question).count(),
            'total_users': session.query(User).count(),
            'total_sessions': session.query(QuizSession).count(),
            'total_attempts': session.query(QuizAttempt).count(),
            'total_achievements': session.query(Achievement).count(),
            'active_users': session.query(User).filter(User.is_active == True).count()
        }
        return stats
    finally:
        session.close()

# Legacy compatibility functions
def db():
    """Legacy compatibility - returns SQLAlchemy session"""
    return SessionLocal()

def close_db(session):
    """Close database session"""
    session.close()
