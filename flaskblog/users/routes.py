from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from flaskblog import bcrypt, db
from flaskblog.models import Post, User

from .forms import (LoginForm, RegistrationForm, RequestResetForm,
                    ResetPasswordForm, UpdateAccountForm)
from .utils import delete_picture, save_picture, send_reset_email

users = Blueprint("users", __name__)


@users.route("/register/", methods=["GET", "POST"])
def register():
    # If the user is already logged in, redirect them to the home page
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        # Create a new user
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        # Add the new user to the database
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("users.login"))
    return render_template("register.html", title="Register", form=form)


@users.route("/login/", methods=["GET", "POST"])
def login():
    # If the user is already logged in, redirect them to the home page
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        # Check if the user exists
        user = User.query.filter_by(email=form.email.data).first()
        # Check if the password is correct
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            # Get the page the user was trying to access before logging in
            next_page = request.args.get("next")
            # If there is no next page, redirect to the home page
            if not next_page:
                next_page = url_for("main.home")
            return redirect(next_page)
            flash("You have been logged in!", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Login unsuccessful. Please check email and password.", "danger")
    return render_template("login.html", title="Login", form=form)


@users.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@users.route("/account/", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            # Save the picture to the filesystem
            picture_file = save_picture(form.picture.data)
            # Delete the old profile picture
            delete_picture(current_user.image_file)
            # Update the user's profile picture
            current_user.image_file = picture_file
        # Update the user's username and email
        current_user.username = form.username.data
        current_user.email = form.email.data
        # Commit the changes to the database
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("users.account"))
    elif request.method == "GET":
        # Populate the form with the user's current username and email
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )


@users.route("/user/<string:username>/")
def user_posts(username):
    page = request.args.get("page", 1, type=int)
    # Get the user with the specified username
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        Post.query.filter_by(author=user)
        .order_by(Post.date_posted.desc())
        .paginate(page=page, per_page=5)
    )
    return render_template("user_posts.html", posts=posts, user=user)


@users.route("/reset_password/", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RequestResetForm()
    if form.validate_on_submit():
        # Get the user with the specified email
        user = User.query.filter_by(email=form.email.data).first()
        # Send an email to the user with a token to reset their password
        send_reset_email(user)
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        return redirect(url_for("users.login"))

    return render_template("reset_request.html", title="Reset Password", form=form)


@users.route("/reset_password/<token>/", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    # Verify the token
    user = User.verify_reset_token(token)
    print(user)
    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("users.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        # Update the user's password
        user.password = hashed_password
        # Commit the changes to the database
        db.session.commit()
        flash("Your password has been updated! You are now able to log in.", "success")
        return redirect(url_for("users.login"))
    return render_template("reset_token.html", title="Reset Password", form=form)
