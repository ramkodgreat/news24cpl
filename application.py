from flask import( Flask, redirect, render_template, 
request, redirect, flash, url_for,session, logging)
#from data import newsArticles
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools  import wraps

app = Flask(__name__)
#configure Mysql database
app.config['SECRET_KEY'] = 'Your_secrete_string'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'ramko'
app.config['MYSQL_PASSWORD'] = '@Ramko1268'
app.config['MYSQL_DB'] = 'slumbookdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init mysql
mysql = MySQL(app)

#newsArticle =newsArticles()

@app.route("/")
def homePage():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

    #rendering the news
@app.route("/newsfeed")
def createPost():
    cur = mysql.connection.cursor()
    #get createdPost
    result = cur.execute("SELECT * FROM createPost")
    createPost = cur.fetchall()
    if result > 0:
        return render_template('newsfeed.html', createPost= createPost)
    else: 
        msg = "No post found"   

        return render_template('newsfeed.html',msg = msg)
    cur.close()

#rensering article form
@app.route("/article/<string:id>/")
def artticle(id):
    cur = mysql.connection.cursor()
    #get createdPost
    result = cur.execute("SELECT * FROM createPost WHERE id = %s", [id])
    createPost = cur.fetchone()
    return render_template("article.html", createPost = createPost)

#class for validating  register
class MyForm(Form):
    name = StringField(u'Name', validators= [validators.input_required(), validators.Length(min=3, max=50)])
    email = StringField(u'Email', validators= [validators.input_required(), validators.Length(min=3, max=50)])
    username = StringField(u'Username', validators= [validators.input_required(), validators.Length(min=3, max=50)])
    password = PasswordField('passworrd',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='password do not match')
    ])
    confirm = PasswordField('Confirm Password')


#rregistration
@app.route("/register",  methods = ['GET', 'POST'])
def register():
    form = MyForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data 
        password = sha256_crypt.encrypt(str(form.password.data))

       #create cursor
        cur = mysql.connection.cursor()
        # execute Query
        cur.execute ("INSERT INTO register (name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))
      #commit to db
        mysql.connection.commit()
        #close connection
        cur.close()
        #flash messages
        flash('Thanks for  registering', 'success')
        return redirect("/login")
    return render_template("register.html", form = form)

 # loigin   
@app.route("/login",  methods = ['GET', 'POST'])
def login():
    if request.method == 'POST': 
        username = request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM register WHERE username = %s", [username])
        if result > 0:
        #Get the stored hash
            data = cur.fetchone()
            password = data['password']
        #copare password
            if sha256_crypt.verify(password_candidate, password):
                #app.logger.info('password matched')
                session['log_in'] = True
                session['username'] = username
                flash("Logged in successfully", "success")
                return redirect(url_for("dashboard"))
            else:
                #app.r.info('password mismatch')
                error = "Invalid login details"
                return render_template("login.html", error=error)
        else:
            #app.logger.info('user not found')
            error = 'user not found'
            return render_template("login.html", error=error)
    return render_template("login.html")

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized access please login"," danger")
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard')

def dashboard():
    cur = mysql.connection.cursor()
    #get createdPost
    result = cur.execute("SELECT * FROM createPost")
    createPost = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', createPost= createPost)
    else: 
        msg = "No post found"   

        return render_template('dashboard.html',msg = msg)
    cur.close()

@app.route("/logout")
@is_logged_in 
def logout():
    session.clear()
    flash("you  are currently logged out", "success")
    return redirect(url_for('login')) 

#class for creating post form
class PostForm(Form): 
    title = StringField(u'Title', validators= [validators.input_required(), validators.Length(min=3, max=200)])
    body = StringField(u'Body', validators= [validators.input_required(), validators.Length(min=3, max=250)])

#creating post and sending to database
@app.route('/addpost', methods=['GET', 'POST'])

def addpost():
    form = PostForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        author = session['username']
        cur = mysql.connection.cursor()
        cur.execute ("INSERT INTO createPost (title, body, author) VALUES (%s, %s, %s)", (title, body, author))
        mysql.connection.commit()
        cur.close()
        flash('Article created succesfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('addpost.html', form = form)

@app.route('/edit_createpost/<string:id>', methods=['GET', 'POST'])
#@is_logged_in
def editpost(id):
    cur = mysql.connection.cursor()
    #get createdPost
    result = cur.execute("SELECT * FROM createPost WHERE id = %s", [id])
    createPost = cur.fetchone()

    form = PostForm(request.form)
    #populate the article form field
    form.title.data = createPost['title']
    form.body.data = createPost['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        #author = session['username']
        cur = mysql.connection.cursor()
        app.logger.info(title)

        cur.execute ("UPDATE createPost SET title = %s, body = %s WHERE id = %s", (title, body, id ))
        mysql.connection.commit()
        cur.close()
        flash('Article updated succesfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_createpost.html', form = form)

#Delete Article
@app.route('/delete_article/<string:id>', methods =['POST'] )
@is_logged_in
def  delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute ("DELETE FROM createPost WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Article deleted succesfully', 'success')
    return redirect(url_for('dashboard'))

if __name__ == " __main__ ":
    
    app.run (debug=True)