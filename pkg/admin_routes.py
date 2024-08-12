from flask import Flask, render_template, render_template_string, url_for, redirect, request, session, flash
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
from pkg import app, mail
from pkg.models import db, Admin, Post, Subscriber
from flask_mail import Message

# Custom errors
@app.errorhandler(404)
def not_found_error(error):
    return render_template('page404.html')


UPLOAD_FOLDER = 'pkg/static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.password_hash == password: 
            session['admin_id'] = admin.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard')) 
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('admin/adminLogin.html')
    

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/admin-dashboard/')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    total_articles = Post.query.count()
    conservation_articles = Post.query.filter_by(category='Conservation').count()
    health_articles = Post.query.filter_by(category='Health').count()
    technical_articles = Post.query.filter_by(category='Technical').count()
    general_articles = Post.query.filter_by(category='General').count()
    food_articles = Post.query.filter_by(category='Food').count()

    return render_template(
        'admin/index.html', 
        total_articles=total_articles,
        conservation_articles=conservation_articles,
        health_articles=health_articles,
        technical_articles=technical_articles,
        general_articles=general_articles,
        food_articles=food_articles
    )

@app.route('/admin/admin/new-post/')
def addNewPost():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('admin/newpost.html')

@app.route('/admin/posts/new', methods=['POST'])
def save_new_post():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    article_content = request.form['article_content']
    category = request.form['category']
    status = request.form['status']
    description = request.form.get('description')
    youtube_link = request.form.get('youtube_link')
    video_name = request.form.get('video_name') 

    cover_image_filename = None

    # Handle cover_image upload
    if 'cover_image' in request.files:
        cover_image = request.files['cover_image']
        if cover_image and allowed_file(cover_image.filename):
            filename = secure_filename(cover_image.filename)
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_image.save(cover_image_path)
            cover_image_filename = filename

    # Create a new Post object
    new_post = Post(
        title=title,
        content=article_content,
        category=category,
        status=status,
        description=description,
        cover_image_url=cover_image_filename,
        youtube_link=youtube_link,
        video_name=video_name  
    )

    try:
        db.session.add(new_post)
        db.session.commit()

        # Send email notifications to subscribers
        send_article_notification(new_post)

        flash('The article has been created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error posting article: {str(e)}', 'danger')

    return redirect(url_for('addNewPost'))


def send_article_notification(post):
    subscribers = Subscriber.query.all()
    article_url = url_for('contentPage', title=post.title.replace(' ', '-'), _external=True)
    subject = f"New Article Posted: {post.title}"
    cover_image_url = url_for('static', filename='uploads/' + post.cover_image_url, _external=True)

    for subscriber in subscribers:
        msg = Message(
            subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[subscriber.email]
        )

        msg.html = render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    background-color: #f4f4f9;
                    color: #333;
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #fff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }
                .header {
                    background-color: #0b0c10;
                    color: #66fcf1;
                    text-align: center;
                    padding: 30px 20px;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                }
                .content {
                    padding: 30px 20px;
                }
                .cover-image {
                    width: 100%;
                    max-width: 600px;
                    height: auto;
                    display: block;
                    margin-bottom: 20px;
                    border-radius: 8px 8px 0 0;
                }
                .title {
                    text-align: center;
                    font-size: 24px;
                    font-weight: 600;
                    margin: 20px 0;
                    color: #444;
                }
                .content p {
                    font-size: 16px;
                    line-height: 1.6;
                    color: #555;
                }
                .content a {
                    color: #1a73e8;
                    text-decoration: none;
                }
                .footer {
                    background-color: #333;
                    color: #aaa;
                    text-align: center;
                    padding: 20px;
                    font-size: 14px;
                }
                .footer a {
                    color: #66fcf1;
                    text-decoration: none;
                }
                @media only screen and (max-width: 600px) {
                    .header, .content, .footer {
                        padding: 15px;
                    }
                    .header h1 {
                        font-size: 24px;
                    }
                    .title {
                        font-size: 20px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Rēadmire</h1>
                </div>
                <div class="content">
                    <img src="{{ cover_image_url }}" alt="Cover Image" class="cover-image">
                    <h2 class="title">{{ post.title }}</h2>
                    <p>Hello,</p>
                    <p>A new article has been posted: <strong>{{ post.title }}</strong></p>
                    <p>You can read it <a href="{{ article_url }}">here</a>.</p>
                    <p>Best Regards,</p>
                    <p>Rēadmire Team</p>
                </div>
                <div class="footer">
                    &copy; 2024 Rēadmire. All rights reserved. <br>
                    # <a href="{{ unsubscribe_url }}">Unsubscribe</a>
                </div>
            </div>
        </body>
        </html>
        """, cover_image_url=cover_image_url, post=post, article_url=article_url)

        try:
            mail.send(msg)
        except Exception as e:
            print(f'Error sending email to {subscriber.email}: {str(e)}')




@app.route('/admin/manage-articles/')
def manageArticles():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    articles = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/managepost.html', articles=articles)

@app.route('/admin/update-article/<int:id>/', methods=['GET', 'POST'])
def updateArticle(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    article = Post.query.get_or_404(id)
    
    if request.method == 'POST':
        article.title = request.form['title']
        article.content = request.form['content']
        article.category = request.form['category']
        article.status = request.form['status']
        article.description = request.form.get('description', '')
        article.cover_image_url = request.form.get('cover_image_url', '')
        article.youtube_link = request.form.get('youtube_link', '')
        article.video_name = request.form.get('video_name', '') 
        
        db.session.commit()
        return redirect(url_for('manageArticles'))
    
    return render_template('admin/update.html', article=article)


@app.route('/admin/delete-article/<int:id>/', methods=['POST'])
def deleteArticle(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    article = Post.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    
    return redirect(url_for('manageArticles'))


@app.route('/admin/update-articles/')
def updateArticles():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('admin/update.html')

@app.route('/admin/send-announcement/', methods=['GET', 'POST'])
def send_announcement():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        subject = request.form.get('subject')
        message_body = request.form.get('message')
        subscribers = Subscriber.query.all()
        for subscriber in subscribers:
            msg = Message(subject, sender="app.config['MAIL_USERNAME']", recipients=[subscriber.email])
            msg.body = message_body
            mail.send(msg)
        flash('Announcement sent to all subscribers!')
        return redirect(url_for('send_announcement'))
    return render_template('admin/announcement.html')
