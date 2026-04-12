#IMPORTS
from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid

#INIT
app = Flask(__name__)
app.secret_key = "lol"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scholium.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


#DATABASE
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(100), unique=True, nullable=False)
	password_hash = db.Column(db.String(255), nullable=False)
	uploads = db.relationship("Upload", backref="user", lazy=True)
		
	is_admin = db.Column(db.Boolean, default=False)
	is_restricted = db.Column(db.Boolean, default=False)
	
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)
	def check_password(self, password):
		return check_password_hash(self.password_hash, password)
	def __repr__(self):
 	   return f"<User {self.id}: {self.username}>"

class Upload(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)
	subject = db.Column(db.String(100))
	filename = db.Column(db.String(255), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	
	def __repr__(self):
   	 return f"<Upload {self.id}: {self.title}>"

#ROUTES
@app.route("/")
def index():
	user_id = session.get("user_id")
	if user_id:
		return redirect("/dashboard")
	return render_template("index.html")
	
	
@app.route("/login", methods=["GET","POST"])
def login():
	if request.method == "POST":
		user_id = session.get("user_id")
		if user_id:
			return redirect("/dashboard")	
		username = request.form["username"]
		password = request.form["password"]
		user = User.query.filter_by(username=username).first()
		
		if user and user.check_password(password):
			session["user_id"] = user.id
			session["is_admin"] = user.is_admin
			if session.get("is_admin"):
				return redirect("/admin")
			return redirect("/dashboard")
		return render_template("index.html", error="Invalid username or password")
	return redirect("/")

@app.route("/signup", methods=["GET", "POST"])
def signup():
	user_id = session.get("user_id")
	if user_id:
		return redirect("/dashboard")
	if request.method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")
		confirm_password = request.form.get("confirm-password")
		if User.query.filter_by(username=username).first():
			return render_template("signup.html", error = "Username already exists")
		if not password == confirm_password:
			return render_template("signup.html", error="Password does't match")
		new_user = User(username=username)
		new_user.set_password(password)
		db.session.add(new_user)
		db.session.commit()
		
		session["user_id"] = new_user.id
		session["is_admin"] = new_user.is_admin
		return redirect("/dashboard")
	return render_template("signup.html")
	

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/") 


@app.route("/admin")
def admin():
	user_id = session.get("user_id")
	if not user_id:
		return redirect("/")
	user = User.query.get(user_id)
	if not user.is_admin:
		return "Access Denied", 403
		
	all_users = User.query.all()
	users_data = [
		{
			"id": u.id,
			"username": u.username,
			"is_restricted": u.is_restricted
		}  for u in all_users
	]
	all_uploads = Upload.query.all()
	uploads_data = [
	    {
	        "id": u.id,
	        "title": u.title,
	        "subject": (u.subject or "Other").title(),
	        "filename": u.filename,
	        "uploader": u.user.username,
	        "user_id": u.user_id
	    }
   	 for u in all_uploads
	]
	users_data.sort(key=lambda user: user["username"])
	subjects = sorted({u["subject"] for u in uploads_data})	
	return render_template(
    "admin.html",
    user=user,
    users=users_data,
    subjects=subjects,
    uploads=uploads_data
    )

@app.route("/dashboard")
def dashboard():
	user_id = session.get("user_id")
	if not user_id:
		return redirect("/")
	user = User.query.get(user_id)
	if not user:
		session.clear()
		return redirect("/")
	if user.is_admin:
		return redirect("/admin")
	all_uploads = Upload.query.all()	
	uploads_data = [
    {
        "id": u.id,
        "filename": u.filename,
        "title": u.title,
        "subject": (u.subject or "Other").title(),
        "uploader": u.user.username,
        "user_id": u.user_id
    }
    for u in all_uploads
]
	subjects = sorted({u["subject"] for u in uploads_data})	
	return render_template(
    "dashboard.html",
    user=user,
    uploads_data=uploads_data,
    subjects=subjects,
    current_user_id=user_id,
    is_restricted=user.is_restricted
)

@app.route("/change", methods=["GET", "POST"])
def change():
	user_id = session.get("user_id")
	if not user_id:
		return redirect("/")
	user = User.query.get(user_id)
	if request.method == "POST":
		curpass = request.form.get("curpass")
		newpass = request.form.get("newpass")
		newpass_confirm = request.form["newpass-confirm"]
		if not user.check_password(curpass):
			return render_template("change.html", error="Incorrect current password")
		if not newpass == newpass_confirm:
			return render_template("change.html", error="New password does not match")
		user.set_password(newpass)
		db.session.commit()
		return redirect("/dashboard")
	return render_template("change.html")

@app.route("/restrictions", methods=["POST"])
def restrictions():
    user_id = request.form.get("user_id")
    action = request.form.get("action")
    user = User.query.get(user_id)

    if action == "restrict":
        user.is_restricted = True
    elif action == "unrestrict":
        user.is_restricted = False
    db.session.commit()

    return redirect("/admin")
    

 
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
 
@app.route("/upload_file", methods=["POST"])
def upload_file():
	user_id = session.get("user_id")
	user = User.query.get(user_id)
	if user.is_restricted:
	    return "You are restricted from uploading", 403
	if not user_id:
		return redirect("/")
	file = request.files.get("file")
	title = request.form.get("title")
	subject = request.form.get("subject")
	
	if not file or file.filename == "":
		return "No file selected"
	if not allowed_file(file.filename):
		return "Invalid file type"
	
	filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
	
	file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
	file.save(file_path)
	
	new_upload = Upload(
		title = title,
		filename = filename,
		subject = subject,
		user_id = user_id	
	)
	db.session.add(new_upload)
	db.session.commit()
	
	return redirect("/dashboard")

@app.route("/uploads/<filename>")
def uploads(filename):
	return send_from_directory(app.config["UPLOAD_FOLDER"] , filename)
	

@app.route("/images/<img>")
def images(img):
  return send_from_directory(app.config["IMAGE_FOLDER"], img)

    
@app.route("/delete_upload/<int:upload_id>", methods=["POST"])
def delete_upload(upload_id):
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "Unauthorized"}, 401

    user = User.query.get(user_id)
    upload = Upload.query.get_or_404(upload_id)
    if upload.user.id != user.id and not user.is_admin:
        return {"error": "Forbidden"}, 403 

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], upload.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(upload)
    db.session.commit()

    return {"success": True}
    

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )
    

@app.route("/edit_upload/<int:upload_id>", methods=["POST"])
def edit_upload(upload_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")

    upload = Upload.query.get_or_404(upload_id)

    if upload.user_id != user_id:
        return "Forbidden", 403
        
    upload.title = request.form.get("title")
    upload.subject = request.form.get("subject")

    file = request.files.get("file")

    if file and file.filename != "":
        if allowed_file(file.filename):
            old_path = os.path.join(app.config["UPLOAD_FOLDER"], upload.filename)
            if os.path.exists(old_path):
                os.remove(old_path)

            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            upload.filename = filename

    db.session.commit()

    return redirect("/dashboard")


#RUN
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin")
            admin.set_password("root") 
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created (username: admin, password: root)")
        else:
            print("ℹ️ Admin user already exists.")
            
        app.run(debug=True)