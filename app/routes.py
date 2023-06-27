from app import app
from flask import render_template, request, redirect, url_for
import os
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from app.utils import extract_tag, selectors

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    if request.method == "POST":
        product_code = request.form.get('product_code')
        url = f"https://www.ceneo.pl/{product_code}#tab=reviews"
        all_opinions =[]
        while url:
            response = requests.get(url)
            page_dom = BeautifulSoup(response.text, "html.parser")
            opinions = page_dom.select("div.js_product-review")
            if not opinions:
                error = 'Błędny kod lub nie znaleziono opinii'
                return render_template('extract.html', error=error)
            for opinion in opinions:
                single_opinion = {}
                for key, value in selectors.items():
                    single_opinion[key] = extract_tag(opinion, *value)
                all_opinions.append(single_opinion)
            try:
                url = "https://www.ceneo.pl" + extract_tag(page_dom, "a.pagination__next", "href")
            except TypeError:
                url = None
        with open(f"./app/data/opinions/{product_code}.json", "w", encoding="UTF-8") as jf:
            json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
        return redirect(url_for('product', product_code=product_code))
    return render_template('extract.html')

@app.route('/product/<product_code>')
def product(product_code):
    opinions = pd.read_json(f"./app/data/opinions/{product_code}.json")
    return render_template('product.html', product_code=product_code, opinions=opinions.to_html(header=1, classes='table table-striped table-success', table_id='opinions'))

@app.route('/products')
def products():
    all_products = []
    data_path = f"./app/data/opinions/"
    file_names = [filename for filename in os.listdir(data_path) if filename.endswith('.json')]
    for file_name in file_names:
        # with open(os.path.join(data_path, file_name), encoding='utf-8') as file:
        #     opinions = json.load(file)
        #     print(len(opinions))
        opinions = pd.read_json(os.path.join(data_path, file_name))
        print(opinions)
        opinions_count = opinions.shape[0]
        pros_count = int(opinions.pros.map(bool).sum())
        print(pros_count)
    return render_template('products.html')

@app.route('/author')
def author():
    return render_template('author.html')