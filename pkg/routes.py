from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from pkg import app
from pkg.models import db, Post, Subscriber, Comment, User, Bookmark, Like, Podcast

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

@app.errorhandler(400)
def bad_request_error(error):
    return render_template('page400.html'), 400


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('page403.html'), 403


@app.errorhandler(500)
def internal_error(error):
    return render_template('page500.html'), 500


@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('page503.html'), 503


import re

def slugify(title):
    return re.sub(r'\W+', '-', title.lower())



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

        existing_name = User.query.filter_by(name = name).first()
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists. Please log in.')
            return redirect(url_for('userLogin'))
        
        if existing_name:
            flash('Name already exists. Please use another.')
            return redirect(url_for('userSignup'))

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
            return redirect(url_for('feed', username=user.name))
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
    if 'user_id' not in session and request.method == 'GET':
        flash('Please log in to access your profile.')
        return redirect(url_for('userLogin'))

    user = User.query.filter_by(name=username).first_or_404()
    
    # Count the number of comments the user has made
    comments_made_count = Comment.query.filter_by(user_id=user.id).count()

    return render_template('users/profile.html', user=user, comments_made_count=comments_made_count)


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
        user.profile_picture = filename
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

    # Fetch the newest five comments
    newest_five_comments = Comment.query.filter_by(article_id=article.id).order_by(Comment.created_at.desc()).limit(5).all()
    comments_numbers = Comment.query.filter_by(article_id=article.id).all()

    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    return render_template('users/contentPageBase.html', 
                           article=article, 
                           related_articles=related_articles, 
                           video_name=video_name, 
                           comments=newest_five_comments,  # pass only the 5 newest comments
                           user=user,
                           comments_numbers = comments_numbers)




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

# Function to get an article by title
def get_article_by_title(article_title):
    title = article_title.replace('-', ' ')
    return Post.query.filter_by(title=title).first_or_404()

# Function to get comments for an article by its id
def get_comments_for_article(article_id):
    return Comment.query.filter_by(article_id=article_id).order_by(Comment.created_at.desc()).all()

# Route to access the comment page using the article title
@app.route('/comment/<title>', methods=['GET', 'POST'])
def commentPage(title):
    article = get_article_by_title(title)
    comments = get_comments_for_article(article.id)
    
    return render_template('users/commentPage.html', article=article, comments=comments)

@app.route('/comment/<title>/post', methods=['POST'])
def post_comment(title):
    if 'user_id' not in session:
        flash("You must be logged in to post a comment.", "warning")
        return redirect(url_for('userLogin'))
    
    comment_text = request.form.get('comment')
    
    if not comment_text:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for('commentPage', title=title))
    
    article = get_article_by_title(title)
    
    try:
        new_comment = Comment(
            comment=comment_text,
            article_id=article.id,
            user_id=session['user_id']
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment posted successfully!", "success")
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for('commentPage', title=title))


def get_article_by_comment_id(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        post = Post.query.get(comment.article_id)
        if post:
            return post.title.replace(' ', '-')
    return ''

@app.route('/comment/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    if 'user_id' not in session:
        flash("You must be logged in to like a comment.", "warning")
        return redirect(url_for('userLogin'))

    user_id = session['user_id']

    # Check if the user has already liked the comment
    existing_like = Like.query.filter_by(user_id=user_id, comment_id=comment_id).first()

    if existing_like:
        flash("You have already liked this comment.", "info")
    else:
        try:
            new_like = Like(user_id=user_id, comment_id=comment_id)
            db.session.add(new_like)
            db.session.commit()
            flash("Comment liked successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    # Ensure get_article_by_comment_id() works correctly
    article_title = get_article_by_comment_id(comment_id)
    return redirect(url_for('commentPage', title=article_title))

@app.route('/comment/<int:comment_id>/respond', methods=['POST'])
def respond_to_comment(comment_id):
    if 'user_id' not in session:
        flash('You need to be logged in to respond to comments.', 'warning')
        return redirect(url_for('userLogin'))

    parent_comment = Comment.query.get_or_404(comment_id)
    comment_text = request.form['comment']

    new_comment = Comment(
        comment=comment_text,
        article_id=parent_comment.article_id,  # Keep the same article ID
        user_id=session['user_id'],  # Get current logged-in user ID
        parent_comment_id=comment_id  # Set the parent comment ID
    )

    db.session.add(new_comment)
    db.session.commit()

    flash('Your response has been posted.', 'success')
    return redirect(url_for('commentPage', title=parent_comment.post.title.replace(' ', '-')))



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

@app.route('/leaderboard')
def leaderboard():
    # Fetch all users and calculate their scores
    users = User.query.all()

    user_scores = []
    for user in users:
        # Get the number of comments made by this user
        comment_count = Comment.query.filter_by(user_id=user.id).count()

        # Calculate the total score (adjust the weighting as needed)
        score = user.articles_viewed + (2 * comment_count)

        # Append the user and their score to the list
        user_scores.append((user, score))

    # Sort the users by their score in descending order
    user_scores.sort(key=lambda x: x[1], reverse=True)

    # Split the top users for the podium and others
    podium_users = [x[0] for x in user_scores[:3]]
    other_users = [x[0] for x in user_scores[3:]]

    return render_template('users/leaderboard.html', podium_users=podium_users, other_users=other_users)

@app.route('/media')
def media():
    if 'user_id' not in session:
        flash('You need to log in to access the media.')
        return redirect(url_for('userLogin')) 
    
    return render_template('users/mediaPage.html')

@app.route('/audio-page')
def audio():
    if 'user_id' not in session:
        flash('You need to log in to access podcasts.')
        return redirect(url_for('userLogin')) 
    
    podcasts = Podcast.query.order_by(Podcast.uploaded_at.desc()).all()
    return render_template('users/audioPage.html', podcasts=podcasts)


@app.route('/bookmarks')
def bookmarks():
    if 'user_id' not in session:
        flash('You need to log in to view your bookmarks.')
        return redirect(url_for('userLogin'))  # Assuming you have a login route
    
    user_id = session['user_id']
    bookmarks = Bookmark.query.filter_by(user_id=user_id).order_by(Bookmark.created_at.desc()).all()
    
    # Fetch the articles corresponding to the bookmarks
    saved_articles = [Post.query.get(bookmark.post_id) for bookmark in bookmarks]
    
    return render_template('users/bookmark.html', saved_articles=saved_articles)

@app.route('/bookmark/<int:post_id>', methods=['POST'])
def bookmark_article(post_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash("You must be logged in to bookmark an article.", "warning")
        return redirect(url_for('userLogin'))

    # Get the logged-in user ID
    user_id = session['user_id']

    # Check if the article is already bookmarked by the user
    existing_bookmark = Bookmark.query.filter_by(user_id=user_id, post_id=post_id).first()
    if existing_bookmark:
        flash('You have already bookmarked this article.', 'warning')
    else:
        # Create a new bookmark entry
        new_bookmark = Bookmark(user_id=user_id, post_id=post_id)
        db.session.add(new_bookmark)
        db.session.commit()
        flash('Article bookmarked successfully!', 'success')

    # Redirect back to the article page
    article = Post.query.get_or_404(post_id)
    return redirect(url_for('contentPage', title=article.title.replace(' ', '-')))

@app.route('/remove_bookmark/<int:post_id>', methods=['POST'])
def remove_bookmark(post_id):
    if 'user_id' not in session:
        flash('You need to log in to perform this action.')
        return redirect(url_for('userLogin'))  # Redirect to login if not logged in

    user_id = session['user_id']
    bookmark = Bookmark.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        flash('Bookmark removed successfully.')
    else:
        flash('Bookmark not found.')

    return redirect(url_for('bookmarks')) 
