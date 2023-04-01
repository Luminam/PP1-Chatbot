import pickle
from joblib import dump, load
import model.joblib

#model = load('model.joblib') 
vector_bow = load('./bow_transformer.joblib') 


def clasificar_modelo(texto):
    return "skill issue"
