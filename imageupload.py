from flask import Flask,render_template,request,redirect,flash,session,make_response
import os;
import boto;
from filechunkio import FileChunkIO;
import math;
import base64
from boto.s3.key import Key

app = Flask(__name__)
app.secret_key = '<SECRET_KEY>'

UPLOAD_FOLDER=os.path.dirname(__file__)+"/tmp/";
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER;
ACCESS_KEY='<ACCESS_KEY>';
SECRET_KEY='<SECRET_KEY>';



@app.route('/',methods=['POST','GET'])
def login_page():
    if request.method=='GET':
        return render_template("login.html");
    else:
        user_name = request.form['user_name'];
        pass_word = request.form['pass_word'];
        conn = boto.connect_s3(ACCESS_KEY, SECRET_KEY);
        bucket = conn.get_bucket('<BUCKET_NAME>');
        check = False;
        k = Key(bucket);
        k.key = 'users.txt'
        if not os.path.exists(UPLOAD_FOLDER + str(k.key)):
            k.get_contents_to_filename(UPLOAD_FOLDER + 'users.txt');
        list = [];
        with open(UPLOAD_FOLDER + 'users.txt', 'rb') as f:
            for line in f:
                print "Line :", line;
                list = line.strip().split("=");
                print list[0], list[1];
                if list[0] == user_name and list[1] == pass_word:
                    check = True;
                    break;
                else:
                    check = False;
        os.remove(UPLOAD_FOLDER + 'users.txt');
        if check == True:
            session['user_name']=user_name;
            return redirect("/home");
        else:
            flash('Invalid username or password');
            return render_template("login.html");

@app.route('/home',methods=['GET'])
def home_page():
    filelist = retrieve_files();
    return render_template("fileupload.html",files=filelist);


@app.route('/upload',methods=['POST'])
def upload():
    f = request.files['fileToUpload'];
    file_name = f.filename;
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name));
    conn=boto.connect_s3(ACCESS_KEY,SECRET_KEY);
    bucket=conn.get_bucket('<BUCKET_NAME>');
    upload_request = bucket.initiate_multipart_upload(session['user_name']+"/"+file_name);
    file_size = os.stat(UPLOAD_FOLDER+file_name).st_size
    print "File size :",file_size;

    block_size=2000000;
    block_count=int(math.ceil(file_size / float(block_size)))
    for i in range(block_count):
        offset = block_size * i
        bytes = min(block_size, file_size - offset)
        with FileChunkIO(UPLOAD_FOLDER+file_name, 'r', offset=offset,bytes=bytes) as fp:
            upload_request.upload_part_from_file(fp, part_num=i + 1)
    upload_request.complete_upload();
    os.remove(UPLOAD_FOLDER + file_name);
    flash('File uploaded successfully.');
    return redirect("/home");



def retrieve_files():
    conn = boto.connect_s3(ACCESS_KEY, SECRET_KEY);
    bucket = conn.get_bucket('BUCKET_NAME>');
    list=[];
    for k in bucket.list():
        if session['user_name'] in str(k.key):
            dict={};
            file_contents=k.get_contents_as_string();
            dict['file_name']=str(k.key).rsplit("/")[1];
            dict['file_image']="data:image/jpeg;base64,"+base64.b64encode(file_contents);
            list.append(dict);
    return list;

def to_read_file_contents(filename):
    conn = boto.connect_s3(ACCESS_KEY, SECRET_KEY);
    bucket = conn.get_bucket('<BUCKET_NAME>');

@app.route('/delete/<file_name>',methods=['GET'])
def delete_file(file_name):
    print "Delete file";
    conn = boto.connect_s3(ACCESS_KEY, SECRET_KEY);
    bucket = conn.get_bucket('<BUCKET_NAME');
    for k in bucket.list():
        if session['user_name'] in str(k.key) and file_name in str(k.key):
            k.delete();
    return redirect("/home");


@app.route('/download/<file_name>',methods=['GET'])
def download_file(file_name):
    print "Download file";
    file_contents='';
    conn = boto.connect_s3(ACCESS_KEY, SECRET_KEY);
    bucket = conn.get_bucket('<BUCKET_NAME>');
    for k in bucket.list():
        if session['user_name'] in str(k.key) and file_name in str(k.key):
            file_contents = k.get_contents_as_string();
    response = make_response(file_contents);
    response.headers["Content-Disposition"] = "attachment; filename="+file_name;
    response.headers["mimetype"]="image/jpeg";
    return response


@app.route('/logout',methods=['GET'])
def logout():
    session.pop('user_name', None);
    return redirect("/");




if __name__ == '__main__':
    app.run(host='<AWS_PUBLIC_DNS>',port='<PORT>',debug=True);
    #app.run();
