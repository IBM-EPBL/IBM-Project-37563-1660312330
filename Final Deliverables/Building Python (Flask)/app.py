from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import pickle
import os.path
import cv2
from skimage import feature
import re

app = Flask(__name__)

app.secret_key = 'xyzsdfg'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Vin@yag2405'
app.config['MYSQL_DB'] = 'pd'

mysql = MySQL(app)

@app.route('/')

def home():
    return render_template('home.html')

@app.route('/info')
def info():
    return render_template('info.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, password,))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            mesage = 'Logged in successfully !'
            return render_template('user.html', mesage=mesage)
        else:
            mesage = 'Please enter correct email / password !'
    return render_template('login.html', mesage=mesage)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email,))
        account = cursor.fetchone()
        if account:
            mesage = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = 'Invalid email address !'
        elif not userName or not password or not email:
            mesage = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s)', (userName, email, password,))
            mysql.connection.commit()
            mesage = 'You have successfully registered !'
    elif request.method == 'POST':
        mesage = 'Please fill out the form !'
    return render_template('register.html', mesage=mesage)


@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if request.form.get('predict') == 'predict':
            f = request.files['file']  # requesting the file
            basepath = os.path.dirname(__file__)  # storing the file directory
            filepath = os.path.join(basepath, "uploads", f.filename)
            f.save(filepath)  # saving the file

            # loading the saved model
            model = pickle.loads(open('parkinson.pkl', "rb").read())

            # pre-process the image in the same manner we did earlier
            image = cv2.imread(filepath)
            output = image.copy()

            # load the input image,convert it to the grqyscale and resize
            output = cv2.resize(output, (128, 128))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = cv2.resize(image, (200, 200))
            image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

            # quantify the image and make predictions based on the extracted
            # featuresnusing the last trained random forest
            features = feature.hog(image, orientations=9,
                                   pixels_per_cell=(10, 10), cells_per_block=(2, 2),
                                   transform_sqrt=True, block_norm="L1")

            preds = model.predict([features])
            print(preds)
            ls = ["healthy", "parkinson"]
            result = ls[preds[0]]

            # draw the coloured class label on the output image and add it ot
            # the set of the output images
            color = (0, 255, 0) if result == "healthy" else (0, 0, 255)
            cv2.putText(output, result, (3, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.imshow("Output", output)
            cv2.waitKey(0)
        return result
    return None

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8000,debug=False)