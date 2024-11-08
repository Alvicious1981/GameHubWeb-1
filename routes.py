from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, Game, Review, News, Guide
from forms import LoginForm, RegisterForm, ReviewForm, GuideForm, GameFilterForm
from sqlalchemy import func

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
    
    # Get recommended games if user is logged in
    if current_user.is_authenticated:
        recommended_games = current_user.get_recommended_games(limit=6)
    else:
        # For non-logged in users, show popular games based on ratings
        recommended_games = db.session.query(Game).join(
            Review,
            Game.id == Review.game_id
        ).group_by(Game.id).order_by(
            func.avg(Review.rating).desc(),
            func.count(Review.id).desc()
        ).limit(6).all()
    
    return render_template('home.html', games=games, news=news, recommended_games=recommended_games)

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
    # Get all unique genres for the filter dropdown
    genres = [(g[0], g[0]) for g in db.session.query(Game.genre).distinct().order_by(Game.genre)]
    filter_form.genre.choices = [('all', 'All Genres')] + genres
    
    # Apply genre filter if selected
    selected_genre = request.args.get('genre', 'all')
    filter_form.genre.default = selected_genre
    
    query = Game.query
    if selected_genre != 'all':
        query = query.filter(Game.genre == selected_genre)
    
    games = query.all()
    return render_template('games/list.html', games=games, filter_form=filter_form, func=func, Review=Review)

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
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    form = ReviewForm()
    return render_template('reviews/index.html', reviews=reviews, form=form)

@profile_bp.route('/')
@login_required
def index():
    # Get recommended games for the user's profile page
    recommended_games = current_user.get_recommended_games(limit=6)
    return render_template('profile/index.html', recommended_games=recommended_games)
