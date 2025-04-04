from flask import Flask, request, render_template, flash
import configs.keys
from flask_bootstrap import Bootstrap
from aws_functions import *


app = Flask(__name__)
Bootstrap(app)

@app.route("/")
def index():
    app.config['SECRET_KEY'] = configs.keys.SECRET_KEY_GEN()
    month_list = get_last_three_months()
    app.config['MONTH_LIST'] = month_list
    return render_template("main_page.html",months = month_list)


@app.route("/view_expense/date_range",methods = ['POST'])
def get_expense():
    dt = request.form.to_dict()
    df = query_dynamodb(dt)
    if isinstance(df,int) and df == -1:
        flash("No records found","warning")
        return render_template("main_page.html",months = app.config['MONTH_LIST'])
    else:
        print(df.head())
        graphs = generate_graphs(df,dt)
    return render_template("month_report.html",
                           date_month_range = ' to '.join(list(dt.values())),
                           columns=df.columns,
                           data=list(df.values),
                           expense_graph = graphs[0],
                           count_graph = graphs[1],
                           trend_graph = graphs[2])


@app.route("/view_expense/<month>", methods=['GET','POST'])
def get_report(month):
    df = query_dynamodb(month)
    if isinstance(df, int) and df == -1:
        flash("No records found","warning")
        return render_template("main_page.html",months = app.config['MONTH_LIST'])
    else:
        print(df.head())
        graphs = generate_graphs(df,month)
    return render_template("month_report.html",
                           date_month_range=month,
                           columns=df.columns,
                           data=list(df.values),
                           expense_graph = graphs[0],
                           count_graph = graphs[1])


@app.route("/add_expense/submit", methods=['POST'])
def add_expense_to_file():
    dt = request.form.to_dict()
    push_to_dynamodb(dt)
    flash("Expense Entered","success")
    return render_template("main_page.html",months = app.config['MONTH_LIST'])




if __name__ == "__main__":
    app.run()
