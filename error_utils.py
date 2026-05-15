from flask import render_template


def render_error(title, message):

    return render_template(
        "error.html",
        title=title,
        message=message
    )