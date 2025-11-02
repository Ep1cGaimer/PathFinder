# postgres database libraries in python
from psycopg2 import pool 
from psycopg2.extras import RealDictCursor

# for environment variable 'DB_PASSWORD'
import os

# data models 
from database.models import User, Location
# to convert dataclass objects to python dictionary
from dataclasses import asdict

# for specifying List return type in functions
from typing import List
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "localhost"
DB_NAME = "pathfinder_db"
DB_USER = "postgres"

try:
    DB_PASSWORD = os.getenv("DB_PASSWORD") #Using project env rather than system env.
    print("Databse authenticated successfully.")
except KeyError:
    raise RuntimeError("Required environment variable DB_PASSWORD not found on your system. Set it.")

# defining the connection pool (its just like the thread pool ;)
conn_pool = pool.SimpleConnectionPool(
    1, 20,
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

def createUser(user: User) -> bool:
    cur = conn = None # initialize these values first, in case try block fails immediately, finally should be valid so cur and conn need to be 
    # present in finally block

    success = False
    try:
        conn = conn_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO users (id, name, reputation, created_at) VALUES (%s, %s, %s, %s);",
                    (user.id, user.name, user.reputation, user.created_at))
        conn.commit()
        success = True
        # conn_pool.putconn(conn)
    except Exception as e:
        print("Error: ", e)   
        success = False 
    finally:
        if cur: 
            cur.close()
        if conn:
            conn_pool.putconn(conn)
        return success

# function to get a user from the database from its id
def getUser(id: str) -> User:
    # user dataclass where we store all the attributes (columns from the table 'users') of the user
    user: User = User(id=None) # check if id=None to know if the user was found or the req was successful

    cur = conn = None
    try:
        conn = conn_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor) # RealDictCursor is just to get the results from the db in python dictionary
        cur.execute("SELECT * FROM users WHERE id = %s;",
                    (id,))
        rows = cur.fetchall() # only single row will be fetched 

        for row in rows:
            user.id = row['id']
            user.name = row['name']
            user.reputation = row['reputation']
            user.created_at = row['created_at']
    except Exception as e: # in case any error occurs
        print("Error: ", e)    
    finally:
        # return the 'user', if any error happened, id=None will be the flag.
        return asdict(user)
    
def searchForUser(username: str) -> List[User]:
    cur = conn = None
    users = []
    try:
        conn = conn_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # return all the users having their username ilike (case-insensitive) given username 
        cur.execute("""SELECT * FROM users WHERE name ILIKE %s""", ('%'+username+'%',))

        rows = cur.fetchall()

        for row in rows:
            user = User(id=row['id'],
                        name=row['name'],
                        reputation=row['reputation'],
                        created_at=row['created_at'])
            users.append(asdict(user))
        
    except Exception as e:
        print("Error: ", e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn_pool.putconn(conn)
        return users
    
# maybe we dont need this database method

# def getUsers() -> List[User]:
#     users: List[User] = []
#     cur = conn = None
#     try:
#         conn = conn_pool.getconn()
#         cur = conn.cursor(cursor_factory=RealDictCursor)

#         cur.execute("SELECT * FROM users;")
#         rows = cur.fetchall()

#         for row in rows:
#             user = User(id=row['id'],
#                         name=row['name'],
#                         reputation=row['reputation'],
#                         created_at=row['created_at'])
            
#             users.append(user)
#     except Exception as e:
#         print("Error: ", e)
#     finally:
#         if cur:
#             cur.close()
#         if conn:
#             conn_pool.putconn(conn)
#         return users
    
def addPost(location: Location) -> bool:
    cur = conn = None 
    success = False
    try:
        id = location.location_id

        conn = conn_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT 1 FROM location WHERE id = %s;", (id,))
        exists = cur.fetchone() is not None
        if not exists:
                cur.execute("INSERT INTO location (id, posts) VALUES (%s, 0);", (location.location_id,))
                conn.commit()

        # insert the new post into the post table.
        cur.execute("""INSERT INTO posts (posted_by, location_id, images_dir, images, text_descr, surface_damage,
        traffic_safety_risk, ride_discomfort, waterlogging, urgency_for_repair, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""", 
        (location.posted_by, location.location_id, location.images_dir, location.images, location.text_descr, location.surface_damage,
        location.traffic_safety_risk, location.ride_discomfort, location.waterlogging, location.urgency_for_repair, location.created_at))

        conn.commit()


        # Upsert (Insert/Update(if already present))
        cur.execute("""INSERT INTO location_scores (location_id, surface_damage, traffic_safety_risk, ride_discomfort, waterlogging,
                    urgency_for_repair) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (location_id) DO UPDATE
                    SET surface_damage = location_scores.surface_damage + EXCLUDED.surface_damage,
                    traffic_safety_risk = location_scores.traffic_safety_risk + EXCLUDED.traffic_safety_risk,
                    ride_discomfort = location_scores.ride_discomfort + EXCLUDED.ride_discomfort,
                    waterlogging = location_scores.waterlogging + EXCLUDED.waterlogging,
                    urgency_for_repair = location_scores.urgency_for_repair + EXCLUDED.urgency_for_repair;""", (location.location_id, location.surface_damage, location.traffic_safety_risk,
                                                                        location.ride_discomfort, location.waterlogging, 
                                                                        location.urgency_for_repair))
        
        conn.commit()

        cur.execute("UPDATE location SET posts = posts + 1 WHERE id = %s;", (location.location_id,))
        conn.commit()

        success = True
    except Exception as e:
        print("Error: ", e)
        success = False

    finally:
        if cur:
            cur.close()
        if conn:
            conn_pool.putconn(conn)

        return success

def getLocation(id: str) -> Location:
    # if req fails or any untoward situation, location_id set to 'None' will be returned 'finally' which 
    # can be checked for to know if the request went successful.
    location: Location = Location(location_id=None)
    cur = conn = None

    try:
        conn = conn_pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM location_scores WHERE location_id = %s;", (id,))
        row = cur.fetchone()

        exists = row is not None

        if exists:
            cur.execute("SELECT posts FROM location WHERE id = %s;", (id,))

            n = cur.fetchone()['posts']

            if (n != 0):
                location = Location(location_id=row['location_id'], surface_damage=row['surface_damage']/n, traffic_safety_risk=
                                    row['traffic_safety_risk']/n, ride_discomfort=row['ride_discomfort']/n, waterlogging=row['waterlogging']/n,
                                    urgency_for_repair=row['urgency_for_repair']/n)
    except Exception as e:
        print("Error: ", e)

    finally:
        if cur:
            cur.close()

        if conn:
            conn_pool.putconn(conn)
        return asdict(location)

def getLocations(id: List[str]) -> List[dict]:
    locations_list = []
    cur = conn = None
    for loc_id in id:
        location: Location = Location(location_id=None)
        try:
            conn = conn_pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT * FROM location_scores WHERE location_id = %s;", (loc_id,))
            row = cur.fetchone() 

            if row is not None:
                cur.execute("SELECT posts FROM location WHERE id = %s;", (loc_id,))
                n = cur.fetchone()['posts']

                if n != 0:
                    location = Location(location_id=row['location_id'], surface_damage=row['surface_damage']/n, traffic_safety_risk=
                                        row['traffic_safety_risk']/n, ride_discomfort=row['ride_discomfort']/n, waterlogging=row['waterlogging']/n,
                                        urgency_for_repair=row['urgency_for_repair']/n)
                                    
        except Exception as e:
            print("Error: ", e)

        finally:
            if cur:
                cur.close()

            if conn:
                conn_pool.putconn(conn)

            if location.location_id is not None:
                locations_list.append(asdict(location))
            
    return locations_list