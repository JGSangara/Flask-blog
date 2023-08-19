from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required

from flaskblog import db
from flaskblog.models import Post
from flaskblog.posts.forms import PostForm

posts = Blueprint("posts", __name__)


@posts.route("/post/new/", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        # Create a new post
        post = Post(
            title=form.title.data, content=form.content.data, author=current_user
        )
        # Add the post to the database
        db.session.add(post)
        db.session.commit()

        flash("Your post has been created!", "success")

        return redirect(url_for("main.home"))

    return render_template("create_post.html", title="New Post", form=form)


@posts.route("/post/<int:post_id>/")
def post(post_id):
    # Get the post with the specified id
    post = Post.query.get_or_404(post_id)
    return render_template("post.html", title=post.title, post=post)


@posts.route("/post/<int:post_id>/update/", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Check if the user is the author of the post
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        # Update the post
        post.title = form.title.data
        post.content = form.content.data
        # Commit the changes to the database
        db.session.commit()
        flash("Your post has been updated!", "success")
        return redirect(url_for("posts.post", post_id=post.id))
    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template("create_post.html", title="Update Post", form=form)


@posts.route("/post/<int:post_id>/delete/", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Check if the user is the author of the post
    if post.author != current_user:
        abort(403)
    # Delete the post
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for("main.home"))
