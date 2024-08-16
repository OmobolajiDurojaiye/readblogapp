from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from pkg import app
from pkg.models import db, Post, Subscriber, Comment, User

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            return redirect(url_for('profile', username=user.name))
        else:
            flash('Login failed. Please check your email and password.')

    return render_template('users/login.html', background_image=background_image)



@app.route('/logout/')
def userLogout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('userLogin'))

@app.route('/feed/')
def feed():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    # Fetch the latest articles
    latest_articles = Post.query.order_by(Post.created_at.desc()).limit(5).all()

    # Fetch category-specific articles
    conservation_articles = Post.query.filter_by(category='Conservation').order_by(Post.created_at.desc()).limit(10).all()
    general_articles = Post.query.filter_by(category='General').order_by(Post.created_at.desc()).limit(10).all()
    food_articles = Post.query.filter_by(category='Food').order_by(Post.created_at.desc()).limit(10).all()
    health_articles = Post.query.filter_by(category='Health').order_by(Post.created_at.desc()).limit(10).all()
    technical_articles = Post.query.filter_by(category='Technical').order_by(Post.created_at.desc()).limit(10).all()

    top_articles = Post.query.order_by(Post.view_count.desc()).limit(5).all()

    top_users = User.query.order_by(User.articles_viewed.desc()).limit(5).all()

    return render_template('users/feed.html', 
                           latest_articles=latest_articles, 
                           conservation_articles=conservation_articles,
                           general_articles=general_articles,
                           food_articles=food_articles,
                           health_articles=health_articles,
                           technical_articles=technical_articles,
                           top_articles=top_articles,
                           top_users=top_users,
                           user=user)





@app.route('/user-profile/<username>/')
def profile(username):
    if 'user_id' not in session:
        flash('Please log in to access your profile.')
        return redirect(url_for('userLogin'))

    user = User.query.filter_by(name=username).first_or_404()
    return render_template('users/profile.html', user=user)

@app.route('/update-profile-picture/<username>/', methods=['POST'])
def update_profile_picture(username):
    if 'user_id' not in session:
        flash('Please log in to update your profile picture.')
        return redirect(url_for('userLogin'))

    user = User.query.filter_by(name=username).first_or_404()

    if 'profile_picture' not in request.files:
        flash('No file part')
        return redirect(url_for('profile', username=username))

    file = request.files['profile_picture']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile', username=username))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Update user profile picture filename in the database
        user.profile_picture = filename  # Add this field to your User model
        db.session.commit()
        flash('Profile picture updated successfully!')
    else:
        flash('Invalid file type')

    return redirect(url_for('profile', username=username))



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

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    return render_template('users/contentPageBase.html', article=article, related_articles=related_articles, video_name=video_name, comments=comments, user=user)

@app.route('/track_article_view/<int:article_id>/', methods=['GET'])
def track_article_view(article_id):
    user_id = session.get('user_id')
    
    if user_id:
        user = User.query.get(user_id)
        if user:
            if user.articles_viewed is None:
                user.articles_viewed = 0
            
            user.articles_viewed += 1
            db.session.commit()
            return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "failed"}), 400



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

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('users/technical.html', posts=posts, background_image=background_image, popular=popular, user=user)


@app.route('/conservation/')
def conservation():
    background_image = url_for('static', filename='images/conservation.jpg')
    popular = Post.query.filter_by(category='conservation').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='conservation').order_by(Post.created_at.desc()).all()
    
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    
    return render_template('users/conservation.html', posts=posts, background_image=background_image, popular=popular, user=user)


@app.route('/health/')
def health():
    background_image = url_for('static', filename='images/health.jpg')
    popular = Post.query.filter_by(category='health').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='health').order_by(Post.created_at.desc()).all()

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('users/health.html', posts=posts, background_image=background_image, popular=popular, user=user)

@app.route('/food/')
def food():
    background_image = url_for('static', filename='images/food.jpg')
    popular = Post.query.filter_by(category='food').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='food').order_by(Post.created_at.desc()).all()

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('users/food.html', posts=posts, background_image=background_image, popular=popular, user=user)

@app.route('/general/')
def general():
    background_image = url_for('static', filename='images/general.jpg')
    popular = Post.query.filter_by(category='general').order_by(Post.view_count.desc()).limit(5).all()
    posts = Post.query.filter_by(category='general').order_by(Post.created_at.desc()).all()

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('users/general.html', posts=posts, background_image=background_image, popular=popular, user=user)

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