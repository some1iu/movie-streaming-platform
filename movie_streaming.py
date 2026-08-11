import json
import mysql.connector as mc
from mysql.connector import Error
import sys
import os
import pickle


# ---------------------------------------------------------
# CONNECTING MYSQL TO PYTHON
# ---------------------------------------------------------

try:
    con = mc.connect(
        user='root',
        password='root',
        host='localhost',
        database='project'
    )
    cr = con.cursor()

except Error:
    print("Error connecting to server... Please try again later!")
    sys.exit()


# ---------------------------------------------------------
# CREATING A PASSWORD DICTIONARY WITH USERNAMES AS KEYS
# ---------------------------------------------------------

Pdict = {}

cr.execute("SELECT Username, Password FROM user;")
d = cr.fetchall()

for i in d:
    a, b = i
    Pdict[a] = b


# ---------------------------------------------------------
# CREATE NEW ACCOUNT
# ---------------------------------------------------------

def create():
    """
    This function allows new users to create an account by
    entering their username, name, password, and selecting
    3 preferred genres.
    """

    print("Hello Newbie! Let's get your account set up!")
    print()
    print("Enter Your Details:")

    Un = input("Select a unique username: ")

    while Un in Pdict:
        print("Sorry, this username is already taken!")
        Un = input("Try Again >>> ")

    Ln = input("Enter your name: ")

    Pw = input(
        "Enter a password (must be less than 20 characters): "
    )

    while len(Pw) >= 20:
        Pw = input(
            "Password must be less than 20 characters long. "
            "Please enter a valid password: "
        )

    selected = []

    print("Choose 3 genres, you can change them later:")

    pgen = {
        '1': 'Drama',
        '2': 'Sci-Fi',
        '3': 'Crime',
        '4': 'Action',
        '5': 'Romance',
        '6': 'Thriller',
        '7': 'Fantasy',
        '8': 'History',
        '9': 'Adventure',
        '10': 'Mystery',
        '11': 'Biography',
        '12': 'Horror'
    }

    print("(please enter the numbers)")
    print(json.dumps(pgen, indent=0))

    for i in range(1, 4):
        gen = input("Enter Preferred Genre " + str(i) + ": ")
        selected.append(pgen[gen])
        del pgen[gen]

    cr.execute(
        """
        INSERT INTO user
        (Username, Name, Password, PG1, PG2, PG3, Access)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            Un,
            Ln,
            Pw,
            selected[0],
            selected[1],
            selected[2],
            'user'
        )
    )

    con.commit()

    print("Account created successfully!")

    gohome(Un)


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

def login():
    """
    This function allows existing users to log into
    their account using their username and password.
    """

    print("Hello Again! Let's sign you in!")
    print("Please Enter Your Details:")

    Un = input("Enter Your Username: ")

    while Un not in Pdict:
        Un = input("Invalid Username. Try Again >> ")

    Pw = input("Enter your Password: ")

    while Pdict[Un] != Pw:
        Pw = input("Incorrect Password. Try again >> ")

    gohome(Un)


# ---------------------------------------------------------
# SEARCH MOVIES
# ---------------------------------------------------------

def search_movies(genre=None, year=None, name=None):
    """
    Generates a query to search for movies satisfying
    the given parameters and returns the results.
    """

    query = "SELECT * FROM movie WHERE 1=1"
    params = []

    if genre:
        query += " AND Genre = %s"
        params.append(genre)

    if year:
        query += " AND Year = %s"
        params.append(year)

    if name:
        query += " AND Name LIKE %s"
        params.append("%" + name + "%")

    cr.execute(query, params)

    results = cr.fetchall()

    return results


# ---------------------------------------------------------
# USER SEARCH FUNCTION
# ---------------------------------------------------------

def search(U):
    """
    Obtains search parameters from the user and
    displays the search results.
    """

    print("Search for a movie:")
    print("-------------------")

    genre = input("Genre (e.g. Action, Drama, etc.): ")
    year = input("Year Released (e.g. 2020, 2019, etc.): ")
    name = input(
        "Movie Title (e.g. The Shawshank Redemption, etc.): "
    )

    print("-------------------")

    # Call the search function
    results = search_movies(genre, year, name)

    # Creating list of valid movie codes
    cr.execute("SELECT MovieCode FROM movie")

    Mcodes = []
    lot = cr.fetchall()

    for t in lot:
        Mcodes.append(str(t[0]))

    if results:
        print("Search Results:")
        print("-------------------------------")

        for row in results:
            print("Code:", row[0])
            print("Title:", row[1])
            print("Genre:", row[4])
            print("Rating:", row[3])
            print("Year Released:", row[2])
            print("Summary:", row[5])
            print("-------------------------------")

        print(
            "Enter code to select movie",
            " " * 35,
            "back (b)"
        )

        x = input(">>> ")

        if x in Mcodes:
            select(x, U)
        else:
            gohome(U)

    else:
        print("No results found.")
        gohome(U)


# ---------------------------------------------------------
# TRANSACTION FUNCTION
# ---------------------------------------------------------

def transaction(mcode, user, br):
    """
    Carries out a buy/rent transaction and records
    the transaction in the database.

    Also generates a bill text file and retrieves
    binary data from the database.
    """

    print("Processing details...")
    print(".......")

    cr.execute("SELECT * FROM bill")
    bills = cr.fetchall()

    tno = 0

    for row in bills:
        tno += 1

    tno += 1

    import datetime

    dt = datetime.date.today()

    q = (
        "INSERT INTO bill(TNo, TDate, BR, MovieCode, User) "
        "VALUES({}, '{}', '{}', {}, '{}')"
    ).format(
        tno,
        dt,
        br,
        mcode,
        user
    )

    cr.execute(q)
    con.commit()

    print("Transaction completed!")
    print()

    # -----------------------------------------------------
    # CREATING THE BILL FILE
    # -----------------------------------------------------

    bname = "Bill.txt"

    with open(bname, "w") as f:

        H1 = [
            "=" * 75,
            " " * 20 + "BILL for " + br.upper(),
            "=" * 75,
            " " * 40 + str(dt),
            "Transaction No: " + str(tno)
        ]

        if br == "Rent":

            cr.execute(
                "SELECT Name, RentCost FROM movie "
                "WHERE MovieCode={}".format(mcode)
            )

            m, c = cr.fetchone()

            H2 = [
                "Movie: " + m,
                "Rent: " + str(c),
                "Your movie is available to watch for 7 days",
                "=" * 75
            ]

        elif br == "Buy":

            cr.execute(
                "SELECT Name, BuyCost FROM movie "
                "WHERE MovieCode={}".format(mcode)
            )

            m, c = cr.fetchone()

            H2 = [
                "Movie: " + m,
                "Cost: " + str(c),
                "=" * 75
            ]

        # Writing H1 and H2 into file
        L = []

        for i in H1 + H2:
            L.append(i + "\n")

        f.writelines(L)
        f.flush()

    print("Receipt saved as 'Bill'")

    # -----------------------------------------------------
    # FETCHING BINARY DATA FROM DATABASE
    # -----------------------------------------------------

    query = (
        "SELECT Binary_Data FROM movie "
        "WHERE MovieCode = %s"
    )

    cr.execute(query, (mcode,))

    result = cr.fetchone()

    if result is None:
        print("No data found")
        return

    x = result[0]

    if x is None:
        print("No data found")
        return

    # Write binary data to a file
    fname = "Stream.png"

    with open(fname, "wb") as fv:
        fv.write(x)

    print("Movie saved as", fname)

    # -----------------------------------------------------
    # TRANSACTION PAGE
    # -----------------------------------------------------

    z = input(
        "Would you like to view your bill "
        "(press T) or see your movie (press F) ? >> "
    )

    if z == "T":
        os.startfile(bname)

    elif z == "F":
        os.startfile(fname)

    input(">> Click enter to go back to home")

    gohome(user)


# ---------------------------------------------------------
# GO HOME FUNCTION
# ---------------------------------------------------------

def gohome(U):
    """
    Displays the recommended movies for a user based
    on their preferred genres.
    """

    cr.execute(
        "SELECT * FROM user WHERE Username='{}'".format(U)
    )

    User = cr.fetchone()

    N = User[1]

    GTuple = (
        User[4],
        User[5],
        User[6]
    )

    G = str(GTuple)

    print("_" * 75)

    print(" " * 25, "Welcome", N + "!")

    print("-" * 75)

    print()

    print("Edit Profile (e)", " " * 48, "Search (s)")

    print("_" * 75)

    print(" " * 25, "Recommended for you...")
    print()

    # -----------------------------------------------------
    # PRINTING RECOMMENDED MOVIES
    # -----------------------------------------------------

    query = "SELECT * FROM movie WHERE Genre IN" + G

    cr.execute(query)

    page = cr.fetchall()

    for m in page:

        print(
            m[0],
            " " * 15,
            m[1].upper()
        )

        print(
            " " * 10,
            m[4],
            " " * 25,
            "Rating:",
            m[3]
        )

        print("-" * 75)

    print(" " * 60, "exit (x)")

    a1 = input(">>> ")

    # Creating list of valid movie codes
    cr.execute("SELECT MovieCode FROM movie")

    Mcodes = []

    lot = cr.fetchall()

    for t in lot:
        Mcodes.append(str(t[0]))

    if a1 in Mcodes:
        select(a1, U)

    elif a1 == "e":
        edit(U)

    elif a1 == "s":
        search(U)

    elif a1 == "x":
        exitf()

    else:
        print("Invalid Action")
        gohome(U)


# ---------------------------------------------------------
# EXIT FUNCTION
# ---------------------------------------------------------

def exitf():
    """
    Used to exit the program.
    """

    print("_" * 75)

    print(" " * 25, "Goodbye!")

    print(
        " " * 10,
        "We hope you enjoyed your time here."
    )

    print(
        " " * 25,
        "See you soon!"
    )

    print("_" * 75)

    sys.exit()


# ---------------------------------------------------------
# SELECT MOVIE FUNCTION
# ---------------------------------------------------------

def select(M, U):
    """
    Displays the details of the selected movie.
    """

    cr.execute(
        "SELECT * FROM movie "
        "WHERE MovieCode={}".format(M)
    )

    mov = cr.fetchone()

    print("_" * 75)

    print("    ", mov[0])

    print(
        " " * 20,
        mov[1].upper()
    )

    print(
        "   ",
        mov[2],
        " " * 10,
        mov[4],
        " " * 20,
        "Rating:",
        mov[3]
    )

    print(mov[5])

    print()

    print(
        " " * 20,
        "Buy Now at Rs.",
        mov[6],
        "(B)"
    )

    print(
        " " * 19,
        "Rent Now for Rs.",
        mov[7],
        "(R)"
    )

    print(
        " " * 65,
        "back Home (b)"
    )

    print("_" * 75)

    action = input(">> ")

    if action == "B":
        transaction(M, U, "Buy")

    elif action == "R":
        transaction(M, U, "Rent")

    else:
        gohome(U)


# ---------------------------------------------------------
# EDIT USER PROFILE FUNCTION
# ---------------------------------------------------------

def edit(U):
    """
    Edits the profile of a user.
    Username cannot be changed.
    """

    cr.execute(
        "SELECT * FROM user "
        "WHERE Username='{}'".format(U)
    )

    User = cr.fetchone()

    print(
        "Username:",
        User[0],
        " " * 10,
        "(username cannot be changed)"
    )

    print("Name (N):", User[1])
    print("Password (P):", User[2])

    print("Your preferred Genres:")

    print(" " * 4 + "(PG1)", User[4])
    print(" " * 4 + "(PG2)", User[5])
    print(" " * 4 + "(PG3)", User[6])

    print(
        "   edit (e)",
        " " * 30,
        "back (b)"
    )

    x = input(">>> ")

    if x == "e":

        pgen = {
            '1': 'Drama',
            '2': 'Sci-Fi',
            '3': 'Crime',
            '4': 'Action',
            '5': 'Romance',
            '6': 'Thriller',
            '7': 'Fantasy',
            '8': 'History',
            '9': 'Adventure',
            '10': 'Mystery',
            '11': 'Biography',
            '12': 'Horror'
        }

        y = input("What would you like to change? ")

        query = "UPDATE user "

        if y == "N":

            N = input("Enter new name: ")

            query += "SET Name = '" + N + "'"

        elif y == "P":

            P = input(
                "Enter new password (max length 10 chrs): "
            )

            query += "SET Password = '" + P + "'"

        elif y == "PG1" or y == "PG2" or y == "PG3":

            print("Choose a new genre:")

            print(json.dumps(pgen, indent=0))

            x = input(">>> ")

            G = pgen[x]

            query += "SET " + y + " = '" + G + "'"

        else:

            print("Invalid Input")

            edit(U)
            return

        query += " WHERE Username = '" + U + "'"

        cr.execute(query)

        con.commit()

        print("Your profile has been edited!")

        input()

        gohome(U)

    elif x == "b":
        gohome(U)

    else:
        print("Invalid Input")
        edit(U)


# ---------------------------------------------------------
# WELCOME FUNCTION
# ---------------------------------------------------------

def welcome():
    """
    Displays the welcome message and calls the
    required functions.
    """

    print("_" * 75)

    print()

    print(
        " " * 20,
        "WELCOME to STREAM"
    )

    print()

    print(" " * 25, "_______")
    print(" " * 25, "| ___  |")
    print(" " * 25, "| |__| |")
    print(" " * 25, "|______|")

    print()

    print("_" * 75)

    print()

    print(
        "To get started, you can either create an account "
        "or log in if you're a returning user."
    )

    print(
        "New here? Type 'y' to create a new account "
        "or 'n' to log in."
    )

    choice = input(">>> ")

    print("-" * 75)

    if choice == "y":
        create()

    elif choice == "n":
        login()

    else:
        print("Invalid Input")
        welcome()


# ---------------------------------------------------------
# GENERIC ERROR HANDLING FUNCTION
# ---------------------------------------------------------

def handle_errors(func, *args, **kwargs):
    """
    Handles common errors occurring during execution.
    """

    try:
        return func(*args, **kwargs)

    except EOFError:
        print("Input interrupted. Please try again.")

    except ValueError:
        print(
            "Invalid input! Please enter valid details."
        )

    except KeyError:
        print(
            "Oops! There seems to be an issue with "
            "the data you're trying to access."
        )

    except TypeError:
        print(
            "There seems to be a mismatch with the data types."
        )

    except Error as e:
        print(f"Database error: {e}")

    except Exception as e:
        print(
            f"An unexpected error occurred: {e}"
        )

    finally:
        print("Operation complete.")


# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------

if __name__ == "__main__":
    handle_errors(welcome)