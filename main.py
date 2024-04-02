from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm
from flask_gravatar import Gravatar
from functools import wraps
from forms import RegisterForm, CreatePostForm, LoginForm, CommentForm
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('8BYkEfBA6O6donzWlSihBXox7C0sKR6b')
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
#'sqlite:///blog.db'
#postgres://angelaweb_user:taei13IlfdsfPSDvMsud9kuRUm4ezhlt@dpg-co61j44f7o1s73a9rl00-a.oregon-postgres.render.com/angelaweb
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)



##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('Users', back_populates='postes')
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments =  relationship('Comment', back_populates='comment_post')

class Users(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(100))
    postes = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='comment_author')

    
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    comment_author = relationship('Users',back_populates='comments')
    post_id =  db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    comment_post = relationship('BlogPost', back_populates='comments')






login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).filter_by(id=int(user_id)).first()


def admin_only(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if current_user.id != 1:
            return abort(403)
        return func(*args, **kwargs)
    
    return wrapper


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, user=current_user)


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    error = None


    if form.validate_on_submit():
        email = form.email.data
        check_email = db.session.query(Users).filter_by(email=email).first()
        
        if check_email == email:
            error = 'This email is already exist!'
            
        
        else:
            password = form.password.data
            name = form.name.data
            hashed_password = generate_password_hash(password=password,method='pbkdf2:sha256',salt_length=8)
            db.session.add(Users(email=email,name=name,password=hashed_password))
            db.session.commit()
            return redirect(url_for('login'))
    return render_template("register.html", form=form, error=error,user=current_user)


@app.route('/login', methods=['GET','POST'])  

def login():
    form = LoginForm()
    error = None

    if current_user.is_authenticated:
        return redirect(url_for('get_all_posts'))

    if form.validate_on_submit():
        try:
            user = db.session.query(Users).filter_by(email=form.email.data).first()
            password = check_password_hash(user.password,form.password.data)
            if password:
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                error = 'Your Password is Invaild!, Please Try Again!'

        except:
            error = 'This Email does not exist, Please Try Again!'







    return render_template("login.html",form=form, error=error, user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    form = CommentForm()
    comments = Comment.query.all()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        text = form.comment.data
        new_comment = Comment(text=text,post_id=post_id,author_id=current_user.id)
        db.session.add(new_comment)
        db.session.commit()



    requested_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=requested_post, user=current_user, form=form,comments=comments, gravatar=gravatar)


@app.route("/about")
def about():

    return render_template("about.html", user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", user=current_user)


@app.route("/new-post",methods=['GET','POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, user=current_user)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run()
