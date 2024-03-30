from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session, render_template
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
import os
from mutagen.mp3 import MP3
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips
from moviepy.video.compositing.transitions import fadein, fadeout, slide_in, slide_out
from moviepy.video.fx.resize import resize
from datetime import datetime

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['JWT_SECRET_KEY'] = 'your_secret_jwt_key_here'
app.config['UPLOAD_FOLDER'] = 'static/images'  # Update this line
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Add this line
jwt = JWTManager(app)

engine = create_engine("cockroachdb://jatin:XnJNGrozqMEp3ZnXKMe-zg@videoappilcation-4166.7s5.aws-ap-south-1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=root.crt")
db = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db.query_property()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(1024), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email
            # don't include the password
        }

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    path = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    extension = Column(String(10), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    
class Audio(Base):
    __tablename__ = 'audios'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    duration = Column(Float, nullable=False)
    path = Column(String(255), nullable=False)

    
def populate_audio_table():
    music_folder = os.path.join(app.static_folder, 'music')
    for filename in os.listdir(music_folder):
        if filename.endswith('.mp3'):
            audio = MP3(os.path.join(music_folder, filename))
            duration = audio.info.length
            path = os.path.join('music', filename)
            # Check if the audio file is already in the Audio table
            existing_audio = Audio.query.filter_by(path=path).first()
            if existing_audio is None:
                new_audio = Audio(name=filename, duration=duration, path=path)
                db.add(new_audio)
    db.commit()
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

@app.route('/')
def landing():
    return send_from_directory('static', 'landing.html')

# @app.route('/api/users')
# def api_users():
#     users_data = User.query.all()
#     return jsonify([user.to_dict() for user in users_data])

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hash_pswd = generate_password_hash(password)
        user = User(name=name, username=username, email=email, password=hash_pswd)
        db.add(user)
        db.commit()
        return redirect('/success')
    return 'Registration Form'

@app.route('/success')
def success():
    return send_from_directory('static', 'succes.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'admin_password':
        session['user'] = 'admin'
        users_data = User.query.all()  # Fetch all users from the database
        return render_template('admin.html', users=users_data)  # Render the admin.html file with the users variable

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['user'] = user.username
        session['user_id'] = user.id  # Store the user_id in the session
        session['video_generated'] = False
        
        return send_from_directory('static','homepage.html') 

    return redirect('/fail')

@app.route('/fail')
def fail():
    return send_from_directory('static', 'fail.html')
    
#added code
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/addimages', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Open the image file
            img = PILImage.open(file_path)
            # Extract its metadata
            width, height = img.size
            size = os.path.getsize(file_path)
            extension = os.path.splitext(filename)[1]

            # Save the metadata in the database
            image = Image(user_id=session['user_id'], path=filename, size=size, extension=extension, width=width, height=height)  # Only store the filename
            db.add(image)
            db.commit()

            return redirect('/addimages')
    return send_from_directory('static', 'addimages.html')
@app.route('/video', methods=['GET', 'POST'])
def video():
    if 'user_id' in session:
        user_id = session['user_id']
        images = Image.query.filter_by(user_id=user_id).order_by(Image.id.desc()).all()
        image_data = [{'path': os.path.join('images', image.path), 'id': image.id} for image in images]
        audio_data = Audio.query.all()  # Fetch all audio files
        

        if request.method == 'POST':
            try:
                selected_images = request.form.get('selectedImages').split(',')
                selected_music = request.form.get('selectedMusic').split(',')
                duration = request.form.get('duration')
                effects = request.form.get('effects')
                resolution = request.form.get('resolution')
                quality = request.form.get('quality')

                resolution_width, resolution_height = map(int, resolution.split('×'))  # Assuming resolution is in the format "width×height"

                selected_images = [Image.query.get(int(id)) for id in selected_images]
                selected_music = [Audio.query.get(int(id)) for id in selected_music]

                image_clips = []
                for image in selected_images:
                    clip = ImageClip(os.path.join(app.config['UPLOAD_FOLDER'], image.path), duration=int(duration))
                    clip = resize(clip, newsize=(resolution_width, resolution_height))  # Resize the clip based on the resolution
                    if effects == 'Fade In':
                        clip = fadein(clip, int(duration))
                    elif effects == 'Fade Out':
                        clip = fadeout(clip, int(duration))
                    elif effects == 'Zoom':
                        clip = resize(clip, lambda t : 1+0.02*t)  # Zoom-in effect
                    elif effects == 'Dissolve':
                        clip = clip.crossfadein(int(duration))  # Dissolve effect
                    image_clips.append(clip)

                audio_clips = [AudioFileClip(os.path.join(app.static_folder, audio.path)) for audio in selected_music]

                # Set the duration of each audio clip
                for clip in audio_clips:
                    clip.duration = int(duration) * len(selected_images) / len(audio_clips)

                video = concatenate_videoclips(image_clips)
                audio = concatenate_audioclips(audio_clips)
                video = video.set_audio(audio)
                output_path = os.path.join(app.static_folder, "output.mp4")
                video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', bitrate=quality)
                # Return a success message or redirect to a success page
                # After the video is generated:
                session['video_generated'] = True
                return redirect(url_for('/video'))  # Replace 'index' with your main route
            except Exception as e:
                # Print the error message and return an error message
                print(str(e))
                return "An error occurred while creating the video"
        return render_template('video.html', image_data=image_data, audio_data=audio_data)
    else:
        return redirect('/login')
@app.route('/reset_video_generated', methods=['POST'])
def reset_video_generated():
    session['video_generated'] = False
    return '', 204  # Return an empty response with a 204 status code
with app.app_context():
    Base.metadata.create_all(bind=engine)
    populate_audio_table()
    
    app.run(debug=True)
