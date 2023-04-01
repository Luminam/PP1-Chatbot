from joblib import dump, load

model = load('./helper/model.joblib')   
CV = load('./helper/bow_transformer.joblib')

def clasificar_modelo(texto):
    return predecir(texto)

def predecir(texto):
    consulta = [texto]
    title_bow = CV.transform(consulta)
    resultado = model.predict(title_bow)
    return resultado[0]
