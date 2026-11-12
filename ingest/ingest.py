from pathlib import Path

import chromadb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(ROOT / "chroma_db")


def load(client, csv_name, collection_name, doc_column):
    df = pd.read_csv(ROOT / "data" / csv_name).fillna("")
    collection = client.get_or_create_collection(name=collection_name)

    ids = df["id"].tolist()
    documents = df[doc_column].tolist()
    metadatas = df.drop(columns=["id", doc_column]).to_dict(orient="records")

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(collection_name, collection.count())


def main():
    client = chromadb.PersistentClient(path=DB_PATH)
    load(client, "questions.csv", "questions", "question")
    load(client, "feedback.csv", "feedback", "feedback_text")


if __name__ == "__main__":
    main()
