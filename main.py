from flask import Flask, request, render_template, flash, url_for, redirect,session
from configs.keys import *
from flask_bootstrap import Bootstrap
from scripts.aws_functions import *
from frontend.validation import *
from frontend.login import *
from flask_login import logout_user, LoginManager, login_user, login_required, current_user
from frontend.user import *
from sqlalchemy import URL


url_object = URL.create(
    "mysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,  # plain (unescaped) text
    host=MYSQL_HOST,
    database=MYSQL_DB,
)
print(url_object)
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = url_object
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
db.init_app(app)
with app.app_context():
    db.create_all()
app.config['SECRET_KEY'] = SECRET_KEY_GEN()
Bootstrap(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'
login_manager.refresh_view = 'login'
login_manager.needs_refresh_message = 'Session Expired. Please login again'



@login_manager.user_loader
def get_user_by_id(user_id):
    user = User.query.filter_by(uid = user_id).first()
    return user


@app.route("/")
def index():
    month_list = get_last_three_months()
    print(session.items())
    if '_user_id' not in session.keys():
        return render_template("main_page.html",user = False)
    return render_template("main_page.html",months = month_list,user = True,username = User.query.filter_by(uid = session['_user_id']).first().username)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if not validate_form(request):
            flash("Bad format of username or password", "warning")
            return render_template("login_page.html")

        user  = authenticate(request.form['username'], request.form['password'])
        if user is not None:
            login_user(user, duration = timedelta(days = 1))
            flash("Logged in successfully", "success")
            next = request.args.get('next')
            return redirect(next or url_for('index'))
        else:
            flash("Invalid username or password", "warning")
            return redirect(url_for('login'))
    return render_template('login_page.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup_page.html")
    resp = create_user(request.form.to_dict())
    if isinstance(resp, str):
        flash("User Already Exists", "warning")
        return render_template("signup_page.html")
    elif resp is None:
        flash("Error in creating user", "warning")
        return render_template("signup_page.html")
    else:
        flash("User Created Successfully", "success")
        return redirect(url_for('login'))

@app.route('/logout',methods = ['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for('index'))


@app.route("/add_expense/submit_file", methods=['POST'])
@login_required
def parse_file():
    file = request.form.to_dict()
    print(file)
    #if file.name.split('.')[-1] == 'pdf':
    #    pass
    #elif file.name.split('.')[-1] == 'jpg':
    #    pass
    #else:
    #    flash("File type not supported", "warning")
    flash("File Uploaded successfully", "warning")
    return redirect(url_for('index'))


@app.route("/view_expense/date_range", methods=['POST'])
@login_required
def get_expense():
    dt = request.form.to_dict()
    df = query_dynamodb(dt,User.query.filter_by(uid=session['_user_id']).first().username)
    if isinstance(df, int) and df == -1:
        try:
            flash("No records found", "warning")
        except Exception as e:
            print(e)
        return redirect(url_for('index'))
    else:
        print(df.head())
        graphs = generate_graphs(df, dt)
    return render_template("month_report.html",
                           date_month_range=' to '.join(list(dt.values())),
                           columns=df.columns,
                           data=list(df.values),
                           expense_graph=graphs[0],
                           count_graph=graphs[1],
                           trend_graph=graphs[2])


@app.route("/view_expense/<month>", methods=['GET', 'POST'])
@login_required
def get_report(month):
    print(session)
    df = query_dynamodb(month,User.query.filter_by(uid=session['_user_id']).first().username)
    if isinstance(df, int) and df == -1:
        try:
            flash("No records found", "warning")
        except Exception as e:
            print(e)
        return redirect(url_for('index'))
    else:
        print(df.head())
        graphs = generate_graphs(df, month)
    return render_template("month_report.html",
                           date_month_range=month,
                           columns=df.columns,
                           data=list(df.values),
                           expense_graph=graphs[0],
                           count_graph=graphs[1])


@app.route("/add_expense/submit", methods=['POST'])
@login_required
def add_expense_to_file():
    dt = request.form.to_dict()
    try:
        resp = push_to_dynamodb(dt, User.query.filter_by(uid=session['_user_id']).first().username)
        if resp == -1:
            flash("DB resources not available ", "warning")
        else:
            flash("Expense added successfully", "success")
    except Exception as e:
        print(e)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug = True)
