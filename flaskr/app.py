import subprocess

from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import ast
import numpy as np
from config import Config
app = Flask(__name__)

app.config.from_object(Config)

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
    return render_template('index.html')

@app.route('/explore')
def explore_page():
    return render_template('explore.html')

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


