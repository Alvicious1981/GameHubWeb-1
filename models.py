from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    reviews = db.relationship('Review', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_recommended_games(self, limit=6):
        # Get user's reviewed games
        reviewed_games = db.session.query(Game.id).join(Review).filter(Review.user_id == self.id).subquery()
        
        # Get user's preferred genres based on highly rated games (rating >= 4)
        preferred_genres = db.session.query(Game.genre).join(Review).filter(
            Review.user_id == self.id,
            Review.rating >= 4
        ).group_by(Game.genre).all()
        preferred_genres = [genre[0] for genre in preferred_genres]
        
        # Build recommendation query
        recommendation_query = db.session.query(
            Game,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).outerjoin(Review).group_by(Game.id).filter(
            ~Game.id.in_(reviewed_games)  # Exclude already reviewed games
        )
        
        if preferred_genres:
            recommendation_query = recommendation_query.filter(Game.genre.in_(preferred_genres))
        
        # Order by average rating and review count
        recommendations = recommendation_query.order_by(
            func.avg(Review.rating).desc(),
            func.count(Review.id).desc()
        ).limit(limit).all()
        
        return [game[0] for game in recommendations]

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    release_date = db.Column(db.Date)
    genre = db.Column(db.String(50))
    reviews = db.relationship('Review', backref='game', lazy='dynamic')
    guides = db.relationship('Guide', backref='game', lazy='dynamic')
    
    @property
    def average_rating(self):
        return db.session.query(func.avg(Review.rating)).filter(Review.game_id == self.id).scalar() or 0
    
    @property
    def review_count(self):
        return self.reviews.count()

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Guide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
