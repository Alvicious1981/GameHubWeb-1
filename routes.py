from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, Game, Review, News, Guide
from forms import LoginForm, RegisterForm, ReviewForm, GuideForm

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
    return render_template('home.html', games=games, news=news)

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
    games = Game.query.all()
    return render_template('games/list.html', games=games)

@games_bp.route('/guides')
def guides():
    guides = Guide.query.order_by(Guide.created_at.desc()).all()
    return render_template('games/guides.html', guides=guides)

@news_bp.route('/')
def index():
    news = News.query.order_by(News.created_at.desc()).all()
    return render_template('news/index.html', news=news)

@reviews_bp.route('/')
def index():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('reviews/index.html', reviews=reviews)

@profile_bp.route('/')
@login_required
def index():
    return render_template('profile/index.html')
