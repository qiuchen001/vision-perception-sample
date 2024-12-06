from sentence_transformers import SentenceTransformer

def embed_fn(text):
    model = SentenceTransformer('models/embedding/bge-small-zh-v1.5')
    return model.encode(text, normalize_embeddings=True)