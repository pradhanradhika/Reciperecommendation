import subprocess
from datetime import datetime

import MySQLdb
from flask import Flask, render_template, request, jsonify, session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import ast
import numpy as np
from config import Config
from flask import redirect, url_for, flash
from flask_mysqldb import MySQL
#from utils.word2vec_model import load_model
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

model = Word2Vec.load("C:/Users/Radhika/PycharmProjects/RecipeRecommendation/flaskr/models/recipe_word2vec.model")
data = pd.read_csv('C:/Users/Radhika/PycharmProjects/RecipeRecommendation/flaskr/cleaned_data.csv')  # Adjust path if needed

#model=load_model()
app.config.from_object(Config)

app.config['MYSQL_HOST'] = 'localhost'  # Your MySQL host
app.config['MYSQL_USER'] = 'root'  # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'Ra@238gs'  # Your MySQL password
app.config['MYSQL_DB'] = 'recipe-rec'  # Your database name

mysql = MySQL(app)
app.secret_key = 'your_secret_key'

# Load and process the dataset
my_data = pd.read_csv(r'C:\Users\Radhika\Downloads\cleaned_data.csv')
my_data['ingredients'] = my_data['ingredients'].apply(ast.literal_eval)

print(my_data.columns)
all_ingredients = []
for ingredients_list in my_data['ingredients']:
    if isinstance(ingredients_list, list):
        all_ingredients.extend(ingredients_list)

vectorizer = TfidfVectorizer()
if all_ingredients:
    vectorizer.fit(all_ingredients)

def ingredients_to_vector(ingredients_list):
    ingredients_string = ' '.join(ingredients_list)
    return vectorizer.transform([ingredients_string]).toarray()[0]


def get_top_recipe_indices_from_ingredients(ingredients_list, top_n=5):
    user_vector = ingredients_to_vector(ingredients_list)

    # Create a list to store recipe indices and their similarity scores
    similarity_scores = []

    for index, row in my_data.iterrows():
        recipe_vector = ingredients_to_vector(row['ingredients'])
        similarity = np.dot(user_vector, recipe_vector) / (np.linalg.norm(user_vector) * np.linalg.norm(recipe_vector))

        # Store the index and its similarity score
        similarity_scores.append((index, similarity))

    # Sort recipes by similarity in descending order
    sorted_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

    # Return the indices of the top N recipes
    top_recipe_indices = [index for index, score in sorted_scores[:top_n]]
    return top_recipe_indices

@app.route('/')
def home():
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check for empty fields
        if not name or not email or not password:
            flash('Please enter your name, email, and password', 'error')
            return redirect(url_for('signup'))

        # Check if the email is already registered
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user:
            flash('Email already registered!', 'error')
        else:
            # Insert the user into the database
            cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, password))
            mysql.connection.commit()
            cursor.close()
            flash('Successfully signed up! You can now sign in.', 'success')
            return redirect(url_for('signin'))

    return render_template('login.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check for empty fields
        if not email or not password:
            flash('Please enter your email and password', 'error')
            return redirect(url_for('signin'))

        # Check if the user exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id,name,email FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Set session data for the logged-in user
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = email
            session['logged_in'] = True
            session.permanent = True  # Keeps the session alive until the set session lifetime expires

            flash('Successfully signed in!', 'success')
            # Redirect to a welcome page or user dashboard
            return redirect(url_for('index_page'))  # Replace this with your actual dashboard route
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')



@app.route('/index')
def index_page():
    user_name = session.get('user_name')
    return render_template('index.html', user_name=user_name)



@app.route('/explore')
def explore_page():
    return render_template('explore.html')

def store_search_history(user_id, search_term):
    try:
        cursor = mysql.connection.cursor()
        query = "INSERT INTO search_history (user_id, search_term, search_time) VALUES (%s, %s, NOW())"
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        print(f"An error occurred while storing search history: {e}")


# Function to connect to MySQL and fetch search history for a specific user
def fetch_search_history(user_id):
    try:
        # Create a cursor
        cursor = mysql.connection.cursor()

        # Execute the query to fetch search history
        query = "SELECT search_term FROM search_history WHERE user_id = %s ORDER BY search_time DESC"
        cursor.execute(query, (user_id,))

        # Fetch all search terms
        search_terms = [row[0] for row in cursor.fetchall()]

        # Close the cursor
        cursor.close()
        return search_terms

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Function to get vector representation for a recipe
def get_recipe_vector(recipe_name):
    words = recipe_name.lower().split()
    word_vectors = []

    for word in words:
        if word in model.wv:
            word_vectors.append(model.wv[word])

    if len(word_vectors) > 0:
        return np.mean(word_vectors, axis=0)
    else:
        return None


# Function to recommend recipes based on search history
def recommend_recipes(search_terms, all_recipes, top_n=5):
    # Combine all search terms into one vector
    search_vectors = [get_recipe_vector(term) for term in search_terms if get_recipe_vector(term) is not None]

    if len(search_vectors) == 0:
        return "No valid search terms found in the history."

    # Average the vectors for the search terms to create a user search profile
    search_profile = np.mean(search_vectors, axis=0)

    similarities = []
    # Compare the search profile vector with each recipe in the dataset
    for recipe_name in all_recipes:
        recipe_vector = get_recipe_vector(recipe_name)
        if recipe_vector is not None:
            similarity = cosine_similarity([search_profile], [recipe_vector])[0][0]
            similarities.append((recipe_name, similarity))

    # Sort recipes by similarity and return top N recommendations
    similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

    return similarities[:top_n]


# Flask route to handle search and recommendations
@app.route('/search', methods=['POST'])
def search():
    user_id = session['user_id']

    search_term = request.form.get('search_term')

    # Store the search term in the database
    store_search_history(user_id, search_term)

    # Fetch user's search history from the database
    search_history = fetch_search_history(user_id)

    if not search_history:
        return "No search history found for the user."

    # List of all recipe names in your dataset
    all_recipe_names = list(data['name'])  # Assuming 'data' is the DataFrame containing recipes

    # Recommend recipes based on the search history
    recommendations = recommend_recipes(search_history, all_recipe_names)

    # Before rendering the template
    print("Recommendations:", recommendations)

    return render_template('explore.html', recommendations=recommendations)


@app.route('/profile')
def profile():
    return render_template('profile.html')


# Route to start Gradio Chatbot UI
from flask import redirect


@app.route('/chatbot')
def chatbot():
    # Launch the Gradio chatbot UI in a separate thread
    subprocess.Popen(['python', 'gradio_ui.py'])
    return jsonify({"status": "Chatbot is running"}), 200


@app.route('/find_recipe', methods=['POST'])
def find_recipe():
    ingredients = request.json.get('ingredients')

    # Get the top 5 matching recipes
    top_indices = get_top_recipe_indices_from_ingredients(ingredients, top_n=5)

    # Retrieve the recipe data for the top N recipes
    top_recipes = my_data.iloc[top_indices][['name', 'ingredients', 'instructions']].to_dict(orient='records')

    # Return recipe name, ingredients, and instructions in the response
    return jsonify(top_recipes)




if __name__ == '__main__':
    app.run(debug=True)


