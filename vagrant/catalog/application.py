# application.py
from models import Base, User, Product
from flask import Flask
app = Flask(__name__)

@app.route('/')
@app.route('/categories')
def getCategories():
    return "Categories go here"

@app.route('/1/items')
def getCategoryItems():
    return "Items within a given cat go here."

@app.route('/categories/new')
def createNewCategory():
    return "Page to create new categories"

@app.route('/categories/edit')
def editCategory():
    return "Edit a category."

@app.route('/categories/delete')
def deleteCategory():
    return "Delete a category."

@app.route('/1/1')
def getItemDetail():
    return "Page to view details of an item."

@app.route('/1/1/edit')
def editItem():
    return "Edit a category item."

@app.route('/1/1/delete')
def deleteItem():
    return "Delete a category item."

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
