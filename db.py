import psycopg2

connection = psycopg2.connect(
    host="localhost",
    database="cineWatch",
    user="postgres",
    password="2602",
    port="5432"
)

cursor = connection.cursor()


def view_movies():
    cursor.execute("SELECT * FROM movies")
    return cursor.fetchall()


def add_movie(title, genre):
    cursor.execute(
        """
        INSERT INTO movies(title, genre, status)
        VALUES (%s, %s, %s)
        """,
        (title, genre, "Watchlist")
    )
    connection.commit()


def mark_watched(movie_id):
    cursor.execute(
        "UPDATE movies SET status = 'Watched' WHERE id = %s",
        (movie_id,)
    )
    connection.commit()


def rate_movie(movie_id, rating):
    cursor.execute(
        "UPDATE movies SET rating = %s WHERE id = %s",
        (rating, movie_id)
    )
    connection.commit()


def delete_movie(movie_id):
    cursor.execute(
        "DELETE FROM movies WHERE id = %s",
        (movie_id,)
    )
    connection.commit()