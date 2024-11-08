from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, select
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
        """Calculate user's genre preferences based on their reviews with temporal decay"""
        genre_ratings = defaultdict(list)
        genre_weights = defaultdict(list)
        current_time = datetime.utcnow()
        
        reviews = Review.query.filter_by(user_id=self.id).join(Game).all()
        for review in reviews:
            # Calculate temporal weight (more recent reviews have more weight)
            days_old = (current_time - review.created_at).days
            temporal_weight = np.exp(-days_old/180)  # 6-month half-life
            
            genre_ratings[review.game.genre].append(review.rating)
            genre_weights[review.game.genre].append(temporal_weight)
        
        genre_scores = {}
        for genre in genre_ratings:
            ratings = np.array(genre_ratings[genre])
            weights = np.array(genre_weights[genre])
            
            # Weighted average rating
            weighted_avg = np.average(ratings, weights=weights)
            count = len(ratings)
            
            # Score combines weighted average rating and number of reviews
            genre_scores[genre] = weighted_avg * (1 - np.exp(-count/3))
            
        return genre_scores
    
    def calculate_user_similarity(self, other_user):
        """Calculate similarity between users based on ratings and temporal factors"""
        # Get common games reviewed by both users
        common_games = db.session.query(Game).join(
            Review, Review.game_id == Game.id
        ).filter(
            Review.user_id.in_([self.id, other_user.id])
        ).group_by(Game.id).having(
            func.count(Review.id) == 2
        ).all()
        
        if not common_games:
            return 0.0
        
        # Build rating vectors with temporal weights
        current_time = datetime.utcnow()
        self_ratings = []
        other_ratings = []
        weights = []
        
        for game in common_games:
            self_review = Review.query.filter_by(
                user_id=self.id,
                game_id=game.id
            ).first()
            other_review = Review.query.filter_by(
                user_id=other_user.id,
                game_id=game.id
            ).first()
            
            if self_review and other_review:
                # Calculate temporal weight
                days_old = min(
                    (current_time - self_review.created_at).days,
                    (current_time - other_review.created_at).days
                )
                temporal_weight = np.exp(-days_old/180)
                
                self_ratings.append(self_review.rating)
                other_ratings.append(other_review.rating)
                weights.append(temporal_weight)
        
        if len(self_ratings) < 2:
            return 0.0
        
        # Calculate weighted cosine similarity
        self_ratings = np.array(self_ratings) * np.array(weights)
        other_ratings = np.array(other_ratings) * np.array(weights)
        
        try:
            similarity = 1 - cosine(self_ratings, other_ratings)
            return max(0.0, similarity)  # Ensure non-negative similarity
        except:
            return 0.0
    
    def get_recommended_games(self, limit=6):
        """Get personalized game recommendations using enhanced collaborative filtering"""
        # Get user's reviewed games
        reviewed_game_ids = [r.game_id for r in Review.query.filter_by(user_id=self.id).all()]
        
        # Calculate user's genre preferences
        genre_preferences = self.get_user_genre_preferences()
        
        # Get similar users
        similar_users = User.query.filter(
            User.id != self.id
        ).all()
        
        # Calculate recommendations
        game_scores = defaultdict(float)
        genre_diversity = defaultdict(int)
        
        for other_user in similar_users:
            similarity = self.calculate_user_similarity(other_user)
            if similarity <= 0:
                continue
                
            # Get other user's reviews
            other_reviews = Review.query.filter_by(
                user_id=other_user.id
            ).filter(Review.rating >= 4).all()
            
            for review in other_reviews:
                if review.game_id in reviewed_game_ids:
                    continue
                    
                game = Game.query.get(review.game_id)
                if not game:
                    continue
                
                # Calculate recommendation score
                base_score = review.rating * similarity
                
                # Genre preference boost
                genre_boost = genre_preferences.get(game.genre, 0) * 0.3
                diversity_penalty = np.exp(-genre_diversity[game.genre])
                genre_boost *= diversity_penalty
                
                # Temporal relevance
                days_old = (datetime.utcnow() - review.created_at).days
                recency_boost = np.exp(-days_old/365) * 0.2
                
                # Popularity factors
                avg_rating = game.average_rating
                review_count = game.review_count
                popularity_score = avg_rating * (1 - np.exp(-review_count/10)) * 0.2
                
                # Final score
                final_score = base_score + genre_boost + recency_boost + popularity_score
                
                if final_score > game_scores[game.id]:
                    game_scores[game.id] = final_score
                    genre_diversity[game.genre] += 1
        
        # If no recommendations found, fall back to popularity-based
        if not game_scores:
            popular_games = Game.query.join(Review).group_by(
                Game.id
            ).having(
                func.count(Review.id) > 0
            ).order_by(
                func.avg(Review.rating).desc(),
                func.count(Review.id).desc()
            ).limit(limit).all()
            
            return popular_games
        
        # Get top recommended games with genre diversity
        recommended_games = []
        seen_genres = set()
        
        for game_id, _ in sorted(game_scores.items(), key=lambda x: x[1], reverse=True):
            game = Game.query.get(game_id)
            if game:
                if len(recommended_games) < limit * 0.7 or game.genre not in seen_genres:
                    recommended_games.append(game)
                    seen_genres.add(game.genre)
                    if len(recommended_games) >= limit:
                        break
        
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
        """Calculate the average rating for the game"""
        result = db.session.query(
            func.avg(Review.rating)
        ).filter(Review.game_id == self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def review_count(self):
        """Get the total number of reviews for the game"""
        return Review.query.filter_by(game_id=self.id).count()

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
