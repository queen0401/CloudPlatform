from testweb.extensions import db
from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import login_user, logout_user, login_required, current_user

from testweb.forms import LoginForm, RegisterForm
from testweb.models import User, Docker
from testweb.utils import redirect_back

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        admin = User.query.filter_by(username = username).first()
        if admin:
            if username == admin.username and admin.validate_password(password):
                login_user(admin, remember)
                flash('欢迎回来，{}'.format(username), 'info')
                return redirect(url_for('home.index'))
            else:
                flash('Invalid username or password.', 'warning')
        else:
            flash('No account.', 'warning')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('成功登出.', 'info')
    return redirect_back()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # name = form.name.data
        email = form.email.data.lower()
        username = form.username.data
        password = form.password.data

        user = User(email=email, username=username, is_admin = False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        # token = generate_token(user=user, operation='confirm')
        # send_confirm_email(user=user, token=token)
        # flash('Confirm email sent, check your inbox.', 'info')
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form)