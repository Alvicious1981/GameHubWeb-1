from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
import numpy as np
from scipy.spatial.distance import cosine
from collections import defaultdict

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
    
    def get_user_genre_preferences(self):
        """Calculate user's genre preferences based on their reviews"""
        genre_ratings = defaultdict(list)
        for review in self.reviews:
            genre_ratings[review.game.genre].append(review.rating)
        
        genre_scores = {}
        for genre, ratings in genre_ratings.items():
            avg_rating = np.mean(ratings)
            count = len(ratings)
            # Weight by both average rating and number of reviews
            genre_scores[genre] = avg_rating * (1 - np.exp(-count/3))
            
        return genre_scores
    
    def calculate_user_similarity(self, other_user):
        """Calculate similarity between two users based on their ratings"""
        # Get all games rated by both users
        common_games = db.session.query(Review.game_id).filter(
            Review.user_id == self.id
        ).intersect(
            db.session.query(Review.game_id).filter(Review.user_id == other_user.id)
        ).all()
        
        if not common_games:
            return 0.0
            
        # Build rating vectors for common games
        self_ratings = []
        other_ratings = []
        
        for game_id in common_games:
            self_review = Review.query.filter_by(user_id=self.id, game_id=game_id[0]).first()
            other_review = Review.query.filter_by(user_id=other_user.id, game_id=game_id[0]).first()
            
            self_ratings.append(self_review.rating)
            other_ratings.append(other_review.rating)
            
        # Calculate cosine similarity
        if len(self_ratings) < 2:
            return 0.0
            
        return 1 - cosine(self_ratings, other_ratings)
    
    def get_recommended_games(self, limit=6):
        """Get personalized game recommendations using collaborative filtering and weighted preferences"""
        # Get user's reviewed games
        reviewed_games = db.session.query(Game.id).join(Review).filter(Review.user_id == self.id).subquery()
        
        # Calculate user's genre preferences
        genre_preferences = self.get_user_genre_preferences()
        
        # Get all users who have reviewed similar games
        similar_users = db.session.query(User).join(Review).filter(
            User.id != self.id,
            Review.game_id.in_(db.session.query(reviewed_games))
        ).distinct().all()
        
        # Calculate user similarities and get their highly rated games
        user_similarities = {}
        recommended_scores = defaultdict(float)
        
        for other_user in similar_users:
            similarity = self.calculate_user_similarity(other_user)
            if similarity > 0:
                user_similarities[other_user.id] = similarity
                
                # Get highly rated games from similar user
                other_reviews = Review.query.filter_by(user_id=other_user.id).filter(Review.rating >= 4).all()
                for review in other_reviews:
                    if review.game_id not in reviewed_games:
                        # Calculate recommendation score based on multiple factors
                        game = review.game
                        
                        # Base score from similar user's rating
                        base_score = review.rating * similarity
                        
                        # Genre preference boost
                        genre_boost = genre_preferences.get(game.genre, 0) * 0.3
                        
                        # Recency boost (newer reviews have more weight)
                        days_old = (datetime.utcnow() - review.created_at).days
                        recency_boost = np.exp(-days_old/365) * 0.2
                        
                        # Popular game boost
                        avg_rating = db.session.query(func.avg(Review.rating)).filter(Review.game_id == game.id).scalar() or 0
                        rating_count = db.session.query(func.count(Review.id)).filter(Review.game_id == game.id).scalar()
                        popularity_boost = (avg_rating * (1 - np.exp(-rating_count/10))) * 0.2
                        
                        # Combine all factors
                        final_score = base_score + genre_boost + recency_boost + popularity_boost
                        recommended_scores[game.id] = max(recommended_scores[game.id], final_score)
        
        # Get top recommended games
        recommended_game_ids = sorted(recommended_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not recommended_game_ids:
            # Fallback to popularity-based recommendations if no collaborative filtering results
            return db.session.query(
                Game,
                func.avg(Review.rating).label('avg_rating'),
                func.count(Review.id).label('review_count')
            ).outerjoin(Review).group_by(Game.id).filter(
                ~Game.id.in_(reviewed_games)
            ).order_by(
                func.avg(Review.rating).desc(),
                func.count(Review.id).desc()
            ).limit(limit).all()
        
        # Fetch and return recommended games
        recommended_games = []
        for game_id, _ in recommended_game_ids[:limit]:
            game = Game.query.get(game_id)
            if game:
                recommended_games.append(game)
                
        return recommended_games

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
