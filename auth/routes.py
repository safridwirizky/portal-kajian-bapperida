from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    login_required,
    login_user,
    logout_user,
)

from forms import LoginForm
from models import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    template_folder="templates",
)


# ==============================================================================
# HELPERS
# ==============================================================================

def render_login(form: LoginForm):
    """Render halaman login."""

    return render_template(
        "auth/login.html",
        form=form
    )


# ==============================================================================
# LOGIN
# ==============================================================================

@auth_bp.get("/login")
def show_login():

    form = LoginForm()

    return render_login(form)


@auth_bp.post("/login")
def login():

    form = LoginForm()

    if not form.validate_on_submit():
        return render_login(form)

    user = User.query.filter_by(
        username=form.username.data
    ).first()

    if user is None or not user.check_password(
        form.password.data
    ):

        flash(
            "Username atau password salah.",
            "danger"
        )

        return render_login(form)

    login_user(
        user,
        remember=form.remember_me.data
    )

    flash(
        "Login berhasil.",
        "success"
    )

    next_page = request.args.get("next")

    return redirect(
        next_page or url_for("home")
    )


# ==============================================================================
# LOGOUT
# ==============================================================================

@auth_bp.get("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Logout berhasil.",
        "success"
    )

    return redirect(
        url_for("home")
    )
