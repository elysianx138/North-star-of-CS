from db import db

rows = db.fetch_all("SELECT * FROM articles")
print("All articles: ", rows)

row = db.fetch_one("SELECT * FROM articles WHERE id = %s", (1,))
print("One article: ", row)

new_id = db.insert("INSERT INTO articles (title,content,author_id) VALUES (%s,%s,%s)", ("New Article", "New Content", 3))
print(f"New id: {new_id}")

affected = db.update("UPDATE articles SET content = %s WHERE id = %s", ("Updated Content", new_id))
print(f"Affected rows: {affected}")

deleted = db.delete("DELETE FROM articles WHERE id = %s", (new_id,))
print(f"Deleted rows: {deleted}")
