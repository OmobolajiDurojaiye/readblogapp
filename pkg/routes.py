from flask import Flask, render_template, url_for, redirect, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from pkg import app
from pkg.models import db, Post, Subscriber, Comment, User

#custom errors
@app.errorhandler(404)
def not_found_error(error):
    return render_template('page404.html')

@app.route('/', methods=['GET'])
@app.route('/index/', methods=['GET'])
def index():
    trending_post = Post.query.filter_by(status='published').order_by(Post.created_at.desc()).first()
    conservation_posts = Post.query.filter_by(category='conservation', status='published').order_by(Post.created_at.desc()).limit(4).all()
    technical_posts = Post.query.filter_by(category='technical', status='published').order_by(Post.created_at.desc()).limit(4).all()
    health_posts = Post.query.filter_by(category='health', status='published').order_by(Post.created_at.desc()).limit(4).all()
    food_posts = Post.query.filter_by(category='food', status='published').order_by(Post.created_at.desc()).limit(5).all()
    return render_template('users/index.html', trending_post=trending_post, conservation_posts=conservation_posts,
                                              technical_posts=technical_posts,
                                              health_posts=health_posts, food_posts=food_posts)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        # Perform a case-insensitive search
        posts = Post.query.filter(
            Post.title.ilike(f'%{query}%') | 
            Post.content.ilike(f'%{query}%') |
            Post.description.ilike(f'%{query}%'),
            Post.status == 'published'
        ).order_by(Post.created_at.desc()).all()
    else:
        posts = []

    return render_template('search_results.html', posts=posts, query=query)


@app.route('/get-started/signup/', methods=['GET', 'POST'])
def userSignup():
    background_image = url_for('static', filename='images/food.jpg')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists. Please log in.')
            return redirect(url_for('userLogin'))

        new_user = User(name=name, email=email)
        new_user.password = password 

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.')
        return redirect(url_for('userLogin'))

    return render_template('users/userAuth.html', background_image=background_image)


@app.route('/get-started/login/', methods=['GET', 'POST'])
def userLogin():
    background_image = url_for('static', filename='images/food.jpg')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('profile'))
        else:
            flash('Login failed. Please check your email and password.')

    return render_template('users/login.html', background_image=background_image)


@app.route('/logout/')
def userLogout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('userLogin'))



@app.route('/user-profile/')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access your profile.')
        return redirect(url_for('userLogin'))

    user = User.query.get(session['user_id'])
    return render_template('users/profile.html', user=user)



@app.route('/article/<title>/')
def contentPage(title):
    title = title.replace('-', ' ')
    article = Post.query.filter_by(title=title).first_or_404()
    
    if article.view_count is None:
        article.view_count = 0
    article.view_count += 1
    db.session.commit()

    previous_article = Post.query.filter(Post.created_at < article.created_at).order_by(Post.created_at.desc()).first()
    next_article = Post.query.filter(Post.created_at > article.created_at).order_by(Post.created_at.asc()).first()
    
    related_articles = [prev for prev in [previous_article, next_article] if prev]

    video_name = article.video_name if article.video_name else 'default'

    comments = Comment.query.filter_by(article_id=article.id).order_by(Comment.created_at.desc()).all()

    return render_template('users/contentPageBase.html', article=article, related_articles=related_articles, video_name=video_name, comments=comments)

@app.route('/add_comment/<int:article_id>', methods=['POST'])
def add_comment(article_id):
    name = request.form.get('name')
    email = request.form.get('email')
    comment_text = request.form.get('comment')

    new_comment = Comment(name=name, email=email, comment=comment_text, article_id=article_id)
    db.session.add(new_comment)
    db.session.commit()

    flash('Your comment has been added!', 'success')
    return redirect(url_for('contentPage', title=Post.query.get_or_404(article_id).title))


# @app.route('/categories/')
# def categories():
#     background_image = url_for('static', filename='images/food.jpg')
#     return render_template('users/categoriesPageTemplateBase.html', background_image=background_image)



@app.route('/technical/')
def technical():
    background_image = url_for('static', filename='images/technical.jpg')
    popular = Post.query.filter_by(category='technical').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='technical').order_by(Post.created_at.desc()).all()
    return render_template('users/technical.html', posts=posts, background_image=background_image, popular=popular)


@app.route('/conservation/')
def conservation():
    background_image = url_for('static', filename='images/conservation.jpg')
    popular = Post.query.filter_by(category='conservation').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='conservation').order_by(Post.created_at.desc()).all()
    return render_template('users/conservation.html', posts=posts, background_image=background_image, popular=popular)

@app.route('/health/')
def health():
    background_image = url_for('static', filename='images/health.jpg')
    popular = Post.query.filter_by(category='health').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='health').order_by(Post.created_at.desc()).all()
    return render_template('users/health.html', posts=posts, background_image=background_image, popular=popular)

@app.route('/food/')
def food():
    background_image = url_for('static', filename='images/food.jpg')
    popular = Post.query.filter_by(category='food').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='food').order_by(Post.created_at.desc()).all()
    return render_template('users/food.html', posts=posts, background_image=background_image, popular=popular)

@app.route('/general/')
def general():
    background_image = url_for('static', filename='images/general.jpg')
    popular = Post.query.filter_by(category='general').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='general').order_by(Post.created_at.desc()).all()
    return render_template('users/general.html', posts=posts, background_image=background_image, popular=popular)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        existing_subscriber = Subscriber.query.filter_by(email=email).first()
        if existing_subscriber:
            flash('You are already subscribed.')
        else:
            new_subscriber = Subscriber(email=email)
            db.session.add(new_subscriber)
            db.session.commit()
            flash('You have successfully subscribed!')
    return redirect(url_for('index'))