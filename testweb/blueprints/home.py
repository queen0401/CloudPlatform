
from flask import Flask, render_template, flash, redirect, url_for, request, send_from_directory, session,send_file,Blueprint,current_app
from flask_uploads import UploadSet, configure_uploads, patch_request_class, ALL
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
import os
from testweb.mnist import predicted_num
from testweb.predict import detect
import zipfile
import shutil
from flask_login import login_user, logout_user, login_required, current_user
from testweb.models import User, Docker
from testweb.extensions import db
from testweb.forms import UploadImgForm,UploadForm

home_bp = Blueprint('home', __name__)



@home_bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index_bootstrap.html')

@home_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadImgForm()
    if form.validate_on_submit():
        f = form.photo.data
        filename = f.filename
        f.save(os.path.join(current_app.config['UPLOAD_PICTURE_PATH'], filename))
        flash('Upload success.')
        session['filename'] = filename
        return redirect(url_for('home.show_images'))
    return render_template('upload.html', form=form)

@home_bp.route('/uploaded-images')
def show_images():
    number = predicted_num(os.path.join(current_app.config['UPLOAD_PICTURE_PATH'], session['filename']))
    session['number'] = int(number)
    return render_template('uploaded.html')

@home_bp.route('/uploaded-images_detect')
def show_images_detect():
    detect(current_app.config['UPLOAD_PICTURE_PATH'], session['filename_detect'])
    return render_template('uploaded_detect.html')

@home_bp.route('/uploads/<path:filename>')
def get_file(filename):
    return send_from_directory(current_app.config['UPLOAD_PICTURE_PATH'], filename)

@home_bp.route('/uploads/detect_results/<path:filename>')
def get_file_detect(filename):
    return send_from_directory(current_app.config['UPLOAD_DETECTED_PICTURE_PATH'], filename)


@home_bp.route('/upload_detect', methods=['GET', 'POST'])
def upload_detect():
    form = UploadImgForm()
    if form.validate_on_submit():
        f = form.photo.data
        filename_detect = f.filename
        f.save(os.path.join(current_app.config['UPLOAD_PICTURE_PATH'], filename_detect))
        flash('Upload success.')
        session['filename_detect'] = filename_detect
        return redirect(url_for('home.show_images_detect'))
    return render_template('upload_detect.html', form=form)








@home_bp.route('/scx_upload', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        for filename in request.files.getlist('files'):
            # name = hashlib.md5(('admin' + str(time.time())).encode('utf-8')).hexdigest()[:15]
            name = filename.filename
        files = UploadSet('files', ALL)    
        try:
            savename = files.save(filename, name=name)
            if '.zip' in name and zipfile.is_zipfile(os.path.join(current_app.config['UPLOADED_FILES_DEST'], name)):
                unzip_file(os.path.join(current_app.config['UPLOADED_FILES_DEST'], name),
                           os.path.join(current_app.config['UPLOADED_FILES_DEST'], savename.split('.')[0]))
        except Exception as e:
            print(e)
        success = True
    else:
        success = False
    return render_template('file_index.html', form=form, success=success)


@home_bp.route('/manage')
def manage_file():
    files_list = os.listdir(current_app.config['UPLOADED_FILES_DEST'])

    files = UploadSet('files', ALL)

    file_path = files.path('.')
    for i in range(len(files_list)):
        if os.path.isdir(os.path.join(file_path, files_list[i])):
            files_list[i] = files_list[i] + '/'
    return render_template('file_manage.html', files_list=files_list, path='')


@home_bp.route('/open/<path:path>')
def open_file(path):
    upload_path = current_app.config['UPLOAD_PICTURE_PATH']
    file_path = os.path.abspath(os.path.join(upload_path,path))
    if os.path.isdir(file_path):
        files_list = os.listdir(file_path)
        parent_path = os.path.abspath(os.path.dirname(file_path[:-1]))
        parent_path_url = ''
        if parent_path == upload_path:
            pass
        else:
            # 处理得到可用的父级目录URL
            parent_path_url = parent_path.split(upload_path)[-1].replace('\\', '/')[1:] + '/'
        for i in range(len(files_list)):
            if os.path.isdir(os.path.join(file_path, files_list[i])):
                files_list[i] = files_list[i] + '/'
        return render_template('file_manage.html', files_list=files_list, path=path, parent_path=parent_path_url)
    else:
        file_path = file_path.replace('\\', '/')
        return send_file(file_path)


@home_bp.route('/delete/<path:path>')
def delete_file(path):
    files = UploadSet('files', ALL)
    file_path = files.path(path)
    if os.path.isdir(file_path):
        shutil.rmtree(file_path)
    else:
        os.remove(file_path)
    return redirect(request.args.get('next'))





@home_bp.route('/docker')
def apply_docker():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    users = User.query.all()
    dockers = current_user.dockers
    return render_template('docker.html' ,dockers = dockers, users = users)       
    
@home_bp.route('/docker/add')
def add_docker():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    ip = '202.120.40.153'
    port = 35000+len(current_user.dockers)
    name = current_user.username + '_' +str(len(current_user.dockers))
    docker = Docker(name = name, port = port, ip = ip)
    db.session.add(docker)
    db.session.commit()
    current_user.dockers.append(docker)
    db.session.add(current_user)
    db.session.commit()
    flash("申请成功！")
    return redirect(url_for('home.apply_docker'))

@home_bp.route('/docker/del/<int:docker_id>')
def del_docker(docker_id):
    docker = Docker.query.get(docker_id)
    db.session.delete(docker)
    db.session.commit()
    flash('删除成功！')
    users = User.query.all()
    dockers = current_user.dockers
    return render_template('docker.html' ,dockers = dockers, users = users)       

@home_bp.route('/docker/del_user/<int:user_id>')
def del_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('删除成功！')
    users = User.query.all()
    dockers = current_user.dockers
    return render_template('docker.html' ,dockers = dockers, users = users)     













