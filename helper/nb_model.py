from joblib import dump, load

model = load('./helper/model.joblib')   
CV = load('./helper/bow_transformer.joblib')

def clasificar(texto:str):
    return normalize(predecir(texto))

def predecir(texto:str):
    consulta = [texto]
    title_bow = CV.transform(consulta)
    resultado = model.predict(title_bow)
    return resultado[0]

def normalize(s:str):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
    )
    for a, b in replacements:
        s = s.replace(a, b).replace(a.upper(), b.upper())
    return s