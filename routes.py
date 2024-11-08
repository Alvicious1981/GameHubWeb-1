from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, Game, Review, News, Guide
from forms import LoginForm, RegisterForm, ReviewForm, GuideForm, GameFilterForm
from sqlalchemy import func, and_
from datetime import datetime

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
games_bp = Blueprint('games', __name__, url_prefix='/games')
news_bp = Blueprint('news', __name__, url_prefix='/news')
reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@main_bp.route('/')
def index():
    games = Game.query.order_by(Game.release_date.desc()).limit(6).all()
    news = News.query.order_by(News.created_at.desc()).limit(3).all()
    
    try:
        if current_user.is_authenticated:
            recommended_games = current_user.get_recommended_games(limit=6)
            if not recommended_games:
                recommended_games = get_popular_games(limit=6)
        else:
            recommended_games = get_popular_games(limit=6)
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        recommended_games = []
    
    return render_template('home.html', 
                         games=games, 
                         news=news, 
                         recommended_games=recommended_games)

def get_popular_games(limit=6):
    """Get popular games based on ratings and review count"""
    try:
        # Get games with their average ratings and review counts
        games = db.session.query(Game).all()
        
        # Sort games by their average rating and review count
        rated_games = [(game, game.average_rating, game.review_count) for game in games]
        rated_games.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Return the top games
        return [game for game, _, _ in rated_games[:limit]]
    except Exception as e:
        print(f"Error getting popular games: {e}")
        return []

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid email or password')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@games_bp.route('/')
def list():
    filter_form = GameFilterForm()
    genres = [(g.genre, g.genre) for g in Game.query.with_entities(Game.genre).distinct().order_by(Game.genre)]
    filter_form.genre.choices = [('all', 'All Genres')] + genres
    
    selected_genre = request.args.get('genre', 'all')
    filter_form.genre.default = selected_genre
    
    query = Game.query
    if selected_genre != 'all':
        query = query.filter(Game.genre == selected_genre)
    
    games = query.all()
    return render_template('games/list.html', games=games, filter_form=filter_form)

@games_bp.route('/guides')
def guides():
    guides = Guide.query.order_by(Guide.created_at.desc()).all()
    form = GuideForm()
    return render_template('games/guides.html', guides=guides, form=form)

@news_bp.route('/')
def index():
    news = News.query.order_by(News.created_at.desc()).all()
    return render_template('news/index.html', news=news)

@reviews_bp.route('/')
def index():
    reviews = Review.query.join(Game).order_by(Review.created_at.desc()).all()
    form = ReviewForm()
    return render_template('reviews/index.html', reviews=reviews, form=form)

@profile_bp.route('/')
@login_required
def index():
    recommended_games = current_user.get_recommended_games(limit=6)
    return render_template('profile/index.html', recommended_games=recommended_games)
