from flask import Flask, render_template, url_for, redirect, request, session, flash
from pkg import app
from pkg.models import db, Post, Subscriber, Comment

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

@app.route('/add_comment/<int:article_id>/', methods=['POST'])
def add_comment(article_id):
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('contentPage', title=Post.query.get_or_404(article_id).title.replace(' ', '-')))
    
    comment = Comment(content=content, article_id=article_id)
    db.session.add(comment)
    db.session.commit()
    
    flash('Your comment has been added.')
    return redirect(url_for('contentPage', title=Post.query.get_or_404(article_id).title.replace(' ', '-')))








@app.route('/technical/')
def technical():
    posts = Post.query.filter_by(category='technical').order_by(Post.created_at.desc()).all()
    return render_template('users/technical.html', posts=posts)

@app.route('/conservation/')
def conservation():
    posts = Post.query.filter_by(category='conservation').order_by(Post.created_at.desc()).all()
    return render_template('users/conservation.html', posts=posts)

@app.route('/health/')
def health():
    posts = Post.query.filter_by(category='health').order_by(Post.created_at.desc()).all()
    return render_template('users/health.html', posts=posts)

@app.route('/food/')
def food():
    posts = Post.query.filter_by(category='food').order_by(Post.created_at.desc()).all()
    return render_template('users/food.html', posts=posts)

@app.route('/general/')
def general():
    posts = Post.query.filter_by(category='general').order_by(Post.created_at.desc()).all()
    return render_template('users/general.html', posts=posts)

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