from app import app
from flask import render_template, request, redirect, url_for

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/extract", methods=['POST', 'GET'])
def extract():
    if request.method == 'POST':
        product_code = request.form.get('product_code')
        return redirect(url_for('product', code=product_code))
    return render_template("extract.html")

@app.route("/product")
def product(code):
    return render_template("product.html", product_code=code)

@app.route("/products")
def products():
    return render_template("products.html")

@app.route("/author")
def author():
    return render_template("author.html")