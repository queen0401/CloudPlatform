
# import logging
import os
# from logging.handlers import SMTPHandler, RotatingFileHandler

import click
from flask import Flask, render_template, request
from flask_login import current_user
from flask_sqlalchemy import get_debug_queries
from flask_wtf.csrf import CSRFError
from flask_uploads import UploadSet, configure_uploads, patch_request_class, ALL

from testweb.blueprints.auth import auth_bp
from testweb.blueprints.home import home_bp

from testweb.extensions import bootstrap, db, login_manager, csrf, ckeditor, moment, toolbar, migrate
from testweb.models import User, Docker
from testweb.settings import config

# basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))






# current_app.secret_key = os.getenv('SECRET_KEY', 'secret string')

def getAllDirRE(path, sp=""):
    # 得到当前目录下所有的文件
    filesList = os.listdir(path)
    if not filesList:
        return
    # 处理每一个文件
    sp += "   "
    for fileName in filesList:
        try:
            filename = fileName.encode('cp437').decode('utf-8')
        except:
            try:
                filename = fileName.encode('cp437').decode('gbk')
            except:
                filename = fileName.encode('utf-8').decode('utf-8')
        os.chdir(path)
        os.rename(fileName, filename)  # 重命名文件
        # 判断是否是路径（用绝对路径）
        fileAbsPath = os.path.join(path, filename)
        if os.path.isdir(fileAbsPath):
            # print(sp + "目录：", fileName)
            # 递归调用
            getAllDirRE(fileAbsPath, sp)
        else:
            # print(sp + "普通文件：", fileName)
            pass


def unzip_file(zip_src, dst_dir):
    """
    解压zip文件
    :param zip_src: zip文件的全路径
    :param dst_dir: 要解压到的目的文件夹
    :return:
    """
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, "r")
        for file in fz.namelist():
            fz.extract(file, dst_dir)
        fz.close()
        getAllDirRE(dst_dir)
        # 解压并重命名之后，需切换目录，
        os.chdir(current_app.config['UPLOADED_FILES_DEST'])
    else:
        return "请上传zip类型压缩文件"


def fk(app):
    files = UploadSet('files', ALL)
    configure_uploads(app, files)
    patch_request_class(app, size=15 * 1024 * 1024 * 1024)  # set maximum file size, default is 64MB



def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('testweb')
    app.config.from_object(config[config_name])


    register_extensions(app)
    register_blueprints(app)
    register_commands(app)

    register_shell_context(app)
    register_template_context(app)
    register_request_handlers(app)
    fk(app)
    return app



# def register_logging(app):
#     class RequestFormatter(logging.Formatter):

#         def format(self, record):
#             record.url = request.url
#             record.remote_addr = request.remote_addr
#             return super(RequestFormatter, self).format(record)

#     request_formatter = RequestFormatter(
#         '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
#         '%(levelname)s in %(module)s: %(message)s'
#     )

#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     file_handler = RotatingFileHandler(os.path.join(basedir, 'logs/testweb.log'),
#                                        maxBytes=10 * 1024 * 1024, backupCount=10)
#     file_handler.setFormatter(formatter)
#     file_handler.setLevel(logging.INFO)

#     mail_handler = SMTPHandler(
#         mailhost=app.config['MAIL_SERVER'],
#         fromaddr=app.config['MAIL_USERNAME'],
#         toaddrs=['ADMIN_EMAIL'],
#         subject='Bluelog Application Error',
#         credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
#     mail_handler.setLevel(logging.ERROR)
#     mail_handler.setFormatter(request_formatter)

#     if not app.debug:
#         app.logger.addHandler(mail_handler)
#         app.logger.addHandler(file_handler)


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    ckeditor.init_app(app)
    moment.init_app(app)
    toolbar.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Docker = Docker)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        user = User.query.first()

        return dict(
            user=user)


# def register_errors(app):
#     @app.errorhandler(400)
#     def bad_request(e):
#         return render_template('errors/400.html'), 400

#     @app.errorhandler(404)
#     def page_not_found(e):
#         return render_template('errors/404.html'), 404

#     @app.errorhandler(500)
#     def internal_server_error(e):
#         return render_template('errors/500.html'), 500

#     @app.errorhandler(CSRFError)
#     def handle_csrf_error(e):
#         return render_template('errors/400.html', description=e.description), 400


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()

    def init():
        """Building testweb."""

        click.echo('Initializing the database...')
        db.create_all()

        user = User.query.filter_by(is_admin = False).first()
        if user is None:
            click.echo('Creating the temporary administrator account...')
            user = User(
                username='admin',
                is_admin = True
            )
            user.set_password('12345678')
            db.session.add(user)

        db.session.commit()
        click.echo('Done.')

    # @app.cli.command()
    # @click.option('--category', default=10, help='Quantity of categories, default is 10.')
    # @click.option('--post', default=50, help='Quantity of posts, default is 50.')
    # @click.option('--comment', default=500, help='Quantity of comments, default is 500.')
    # def forge(category, post, comment):
    #     """Generate fake data."""
    #     from testweb.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_links

    #     db.drop_all()
    #     db.create_all()

    #     click.echo('Generating the administrator...')
    #     fake_admin()

    #     click.echo('Generating %d categories...' % category)
    #     fake_categories(category)

    #     click.echo('Generating %d posts...' % post)
    #     fake_posts(post)

    #     click.echo('Generating %d comments...' % comment)
    #     fake_comments(comment)

    #     click.echo('Generating links...')
    #     fake_links()

    #     click.echo('Done.')


def register_request_handlers(app):
    @app.after_request
    def query_profiler(response):
        for q in get_debug_queries():
            if q.duration >= app.config['BLUELOG_SLOW_QUERY_THRESHOLD']:
                app.logger.warning(
                    'Slow query: Duration: %fs\n Context: %s\nQuery: %s\n '
                    % (q.duration, q.context, q.statement)
                )
        return response
