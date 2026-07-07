from db import (
    add_movie,
    view_movies,
    mark_watched,
    rate_movie,
    delete_movie
)

while True:

    print("\n=== CineWatch ===")
    print("1. Add Movie")
    print("2. View Movies")
    print("3. Mark Watched")
    print("4. Rate Movie")
    print("5. Delete Movie")
    print("6. Exit")

    choice = input("Choose an option: ")

    if choice == "1":

        title = input("Movie Title: ")
        genre = input("Genre: ")

        add_movie(title, genre)

        print("Movie added successfully!")

    elif choice == "2":

        movies = view_movies()

        for movie in movies:
            print(movie)

    elif choice == "3":

        movie_id = int(input("Movie ID: "))
        mark_watched(movie_id)

        print("Movie marked as watched!")

    elif choice == "4":

        movie_id = int(input("Movie ID: "))
        rating = int(input("Rating (1-10): "))

        rate_movie(movie_id, rating)

        print("Rating updated!")

    elif choice == "5":

        movie_id = int(input("Movie ID: "))

        delete_movie(movie_id)

        print("Movie deleted!")


    elif choice == "6":

        print("Goodbye!")
        break
