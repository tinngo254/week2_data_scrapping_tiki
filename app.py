from flask import Flask, render_template
from bs4 import BeautifulSoup
from collections import deque
import requests
import sqlite3
import time


TIKI_URL = 'https://tiki.vn'

app = Flask(__name__)

conn = sqlite3.connect('tiki_products.db')
cur = conn.cursor()

class Category:
  def __init__(self, cat_id, name, url, parent_id):
      self.cat_id = cat_id
      self.name = name
      self.url = url
      self.parent_id = parent_id

  def __repr__(self):
      return "ID: {}, Name: {}, URL: {}, Parent_id: {}".format(self.cat_id, self.name, self.url, self.parent_id)

  def save_to_db(self):
      query = """
          INSERT INTO categories (name, url, parent_id)
          VALUES (?, ?, ?);
      """
      val = (self.name, self.url, self.parent_id)
      try:
          cur.execute(query, val)
          self.cat_id = cur.lastrowid
      except Exception as err:
          print('ERROR WHEN INSERT:', err)

class Product:
  def __init__(self, prod_id, name, brand, price, tiki_now, cat_id, review, url):
      self.prod_id = prod_id
      self.name = name      
      self.brand = brand
      self.price = price
      self.tiki_now = tiki_now      
      self.review = review
      self.url = url
      self.cat_id = cat_id

  def __repr__(self):
      return "ID: {}, Name: {}, Brand: {}, Price: {}, TikiNOW: {}, Cat_id: {}, Review: {}, URL: {}".format(self.prod_id, self.name, self.brand, self.price, self.tiki_now, self.cat_id, self.review, self.url)

  def save_to_db(self):
      query = """
          INSERT INTO products (name, brand, price, tiki_now, cat_id, review, url)
          VALUES (?, ?, ?, ?, ?, ?, ?);
      """
      val = (self.name, self.brand, self.price, self.tiki_now, self.cat_id, self.review, self.url)
      try:
          cur.execute(query, val)
          self.prod_id = cur.lastrowid
      except Exception as err:
          print('ERROR WHEN INSERT:', err)

# Categories Table
def create_categories_tabl():
    query = """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            url TEXT,
            parent_id INTEGER,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) 
    """
    try:
        cur.execute(query)
    except Exception as err:
        print('ERROR BY CREATING TABLE NAME', err)

def select_all_cat():
  return cur.execute('SELECT * FROM categories;').fetchall()

def delete_all_cat():
  return cur.execute('DELETE FROM categories;')

# Products Table
def create_products_tabl():
    query = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            brand VARCHAR(255),
            price FLOAT,
            tiki_now INTEGER,
            cat_id INTEGER,
            review INTEGER,
            url TEXT,            
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    try:
        cur.execute(query)
    except Exception as err:
        print('ERROR BY CREATING TABLE NAME', err)

def select_all_prod():
  return cur.execute('SELECT * FROM products;').fetchall()

def delete_all_prod():
  return cur.execute('DELETE FROM products;')

# Functions to crawl data
def get_url(url):
    time.sleep(1)
    try:
        response = requests.get(url).text
        response = BeautifulSoup(response, 'html.parser')
        return response
    except Exception as err:
        print('ERROR BY REQUEST:', err)

# --Functions for cats
def get_main_categories(save_db = False):
    soup = get_url(TIKI_URL)

    result = []
    
    for a in soup.findAll('a', class_ = 'MenuItem__MenuLink-tii3xq-1 efuIbv'):
        cat_id = None
        name = a.find('span', {'class':'text'}).text
        url = a['href']
        parent_id = None

        cat = Category(cat_id, name, url, parent_id)
        if save_db:
            cat.save_to_db()
        result.append(cat)
    return result

def get_sub_categories(category, save_db=False):
    name = category.name
    url = category.url

    result = []

    try:
        soup = get_url(url)
        div_containers = soup.findAll('div', {'class': 'list-group-item is-child'})
        for div in div_containers:
            sub_id = None
            sub_name = div.a.text
            sub_url = 'http://tiki.vn' + div.a['href']
            sub_parent_id = category.cat_id

            sub = Category(sub_id, sub_name, sub_url, sub_parent_id)
            if save_db:
                sub.save_to_db()
            result.append(sub)            
    except Exception as err:
        print('ERROR BY GETTING SUB CATEGORIES:', err)
    return result

def get_all_categories(main_categories):
    de = deque(main_categories)
    count = 0

    while de:
        parent_cat = de.popleft()
        sub_cats = get_sub_categories(parent_cat,save_db= True)
        de.extend(sub_cats)
        count += 1

        if count % 100 == 0:
            print(count, 'times') 

def get_products_from_sub(sub_category, save_db=False):
    name = sub_category.name
    url = sub_category.url

    result = []  

    try:
        soup = get_url(url)
        div_products = soup.findAll('div', {'class': 'product-item'})
        for div in div_products:
            prod_id = None
            prod_name = div['data-title']      
            prod_brand = div['data-brand']
            prod_price = div['data-price']
            if div.find(class_ = "tikicon icon-tikinow"):
              prod_tiki_now = 1
            else:
              prod_tiki_now = 0               
            prod_review = 0
            prod_url = div.a['href']
            prod_cat_id = sub_category.cat_id  

            prod = Product(prod_id, prod_name, prod_brand, prod_price, prod_tiki_now, prod_cat_id, prod_review, prod_url)
            if save_db:
                prod.save_to_db()
            result.append(prod)            
    except Exception as err:
        print('ERROR BY GETTING PRODUCTS:', err)
    return result  

def get_all_products(sub_categories):
    de = deque(sub_categories)
    count = 0

    while de:
        sub_parent_cat = de.popleft()
        prods = get_products_from_sub(sub_parent_cat,save_db= True)
        de.extend(prods)
        count += 1

        if count % 100 == 0:
            print(count, 'times') 


@app.route('/')
def index():
    create_categories_tabl()
    create_products_tabl()
    main_categories = get_main_categories(save_db=True)
    main0 = main_categories[0]
    main1 = main_categories[1]
    main2 = main_categories[2]
    main3 = main_categories[3]
    main4 = main_categories[4]
    main5 = main_categories[5]
    # get_all_categories
    # get_all_categories(main0)
    # sub_main0 = get_sub_categories(main0)
    # get_all_categories(main1)
    # sub_main1 = get_sub_categories(main1)
    # get_all_categories(main2)
    # sub_main2 = get_sub_categories(main2)
    
    # # get_all_products
    # get_all_products(sub_main0)
    # get_all_products(sub_main1)
    # get_all_products(sub_main2)
    return render_template('index.html')

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
 