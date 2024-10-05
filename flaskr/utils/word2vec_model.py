from gensim.models import Word2Vec


def load_model():
    model = Word2Vec.load("C:/Users/Radhika/PycharmProjects/RecipeRecommendation/flaskr/models/recipe_word2vec.model")
    return model