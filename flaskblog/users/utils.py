import os
import secrets

from flask import current_app, url_for
from flask_mail import Message
from PIL import Image

from flaskblog import mail


def save_picture(form_picture):
    # Generate a random filename
    random_hex = secrets.token_hex(8)
    # Get the file extension of the picture
    _, f_ext = os.path.splitext(form_picture.filename)
    # Create a new filename
    picture_fn = random_hex + f_ext
    # Get the path to the picture
    picture_path = os.path.join(
        current_app.root_path, "static/profile_pics", picture_fn
    )
    # Resize the picture
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    # Save the picture to the filesystem
    i.save(picture_path)
    return picture_fn


def delete_picture(old_picture):
    # Check if the old picture is not the default picture
    if old_picture != "default.jpg":
        picture_path = os.path.join(
            current_app.root_path, "static", "profile_pics", old_picture
        )
        if os.path.exists(picture_path):
            os.remove(picture_path)


def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for("users.reset_token", token=token, _external=True)

    msg = Message(
        "Password Reset Request", sender="noreply@demo.com", recipients=[user.email]
    )
    msg.body = f"""To reset your password, visit the following link:
    {reset_url}
    If you did not make this request then simply ignore this email and no changes will be made.
    """

    mail.send(msg)
