from db import db


# === CRUD demo ===
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


# === transaction demo ===
with db.transaction() as cursor:
    cursor.execute("UPDATE articles SET title = %s WHERE id = %s",("New title",2))
    cursor.execute("UPDATE articles SET title = %s WHERE id = %s",("FUCK MYSQL",1))

print("All articles: ", db.fetch_all("SELECT * FROM articles"))\

# === compare insert with non-insert ===
sql = "INSERT INTO articles (title,content,author_id) VALUES (%s,%s,%s)"
data = [
    ("TEXT1","FUCK brain",1),
    ("TEXT2","SHIT",3,),
    ("TEXT3","FUCKER",4,)
]
db.insert_many(sql, data)
db.fetch_all("SELECT * FROM articles")