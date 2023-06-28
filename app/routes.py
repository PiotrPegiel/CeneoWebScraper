from app import app
from flask import render_template, request, redirect, url_for, send_from_directory, current_app, send_file
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
                error = 'Błędny kod, nie znaleziono opinii, lub Ceneo mówi "NIE"'
                return render_template('extract.html', error=error)
            name = page_dom.select_one("h1.product-top__product-info__name").text
            for opinion in opinions:
                single_opinion = {}
                for key, value in selectors.items():
                    single_opinion[key] = extract_tag(opinion, *value)
                all_opinions.append(single_opinion)
            try:
                url = "https://www.ceneo.pl" + extract_tag(page_dom, "a.pagination__next", "href")
            except TypeError:
                url = None
        # Zapisywanie opinii do pliku
        with open(f"./app/data/opinions/{product_code}.json", "w", encoding="UTF-8") as jf:
            json.dump(all_opinions, jf, indent=4, ensure_ascii=False)

        # !Analiza danych!
        # Odczytanie pliku
        data_path = f"./app/data/opinions/"
        file_name = f"{product_code}.json"
        file_path = os.path.join(data_path, file_name)
        opinions = pd.read_json(file_path)
        # Zamiana ',' na '.'
        opinions.rating = opinions.rating.map(lambda x: float(x.split("/")[0].replace(",", ".")))
        # Przypisanie statystyk
        product = {'name': name, 'path': file_path, 'url': url, 'opinions_count': opinions.shape[0],
                   'pros_count': opinions.pros.map(bool).sum(), 'cons_count': opinions.cons.map(bool).sum(),
                   'avg_rating': opinions.rating.mean().round(2)}


        # Przejście na stronę produktu
        return redirect(url_for('product', product_code=product_code))
    return render_template('extract.html')

@app.route('/product/<product_code>')
def product(product_code):
    opinions = pd.read_json(f"./app/data/opinions/{product_code}.json")
    return render_template('product.html', product_code=product_code, opinions=opinions.to_html(header=1, classes='w-full text-sm text-left text-gray-500 dark:text-gray-400', table_id='opinions'))

@app.route('/products')
def products():
    all_products = []
    data_path = f"./app/data/opinions/"
    file_names = [filename for filename in os.listdir(data_path) if filename.endswith('.json')]
    for file_name in file_names:
        file_path = os.path.join(data_path, file_name)
        opinions = pd.read_json(file_path)
        opinions.rating = opinions.rating.map(lambda x: float(x.split("/")[0].replace(",",".")))
        code = file_name.split(".")
        url = f"https://www.ceneo.pl/{code[0]}"

        # error handling in case of "Ceneo wpierdala się z rowerka"
        response = requests.get(url)
        page_dom = BeautifulSoup(response.text, "html.parser")
        name = page_dom.select_one("h1.product-top__product-info__name")
        if not name:
            name = code[0]
        else:
            name = name.text

        # Przypisanie danych
        product = {
            'name': name,
            'code': code[0],
            'path': file_path,
            'url': url,
            'opinions_count': opinions.shape[0],
            'pros_count': opinions.pros.map(bool).sum(),
            'cons_count': opinions.cons.map(bool).sum(),
            'avg_rating': opinions.rating.mean().round(2)}
        all_products.append(product)
    return render_template('products.html', list=all_products)

# Pobieranie wskazanych plików przez products
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(f'data/opinions', filename, as_attachment=True)

@app.route('/author')
def author():
    return render_template('author.html')
