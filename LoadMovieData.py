import sqlite3, csv, re, pickle
import pandas as pd
import numpy as np
from sklearn.decomposition import NMF
from fuzzywuzzy import process

############################
# set up SQLite DB
############################
db =sqlite3.connect('MoviesData.db')
cur = db.cursor()
db

############################
# import csv file and insert into db
############################
db.execute("CREATE TABLE IF NOT EXISTS movies (movieId INTEGER NOT NULL PRIMARY KEY, title TEXT,genres TEXT);") 
with open('ml-latest-small/movies.csv', encoding="utf8") as csv_file:
    #uses first line in file for column headings by default
    reader = csv.DictReader(csv_file) # comma is default delimiter
    to_db = [(row['movieId'], row['title'], row['genres']) for row in reader]    
cur.executemany("INSERT INTO movies (movieId, title,genres) VALUES (?, ?, ?);", to_db)
db.commit()

db.execute("CREATE TABLE IF NOT EXISTS ratings (userId INTEGER,movieId INTEGER,rating FLOAT,timestamp TIMESTAMP);") 
with open('ml-latest-small/ratings.csv', encoding="utf8") as csv_file:
    #uses first line in file for column headings by default
    reader = csv.DictReader(csv_file) # comma is default delimiter
    to_db = [(row['userId'], row['movieId'], row['rating'],row['timestamp']) for row in reader]
cur.executemany("INSERT INTO ratings (userId,movieId,rating,timestamp) VALUES (?, ?, ?, ?);", to_db)
db.commit()


db.execute("CREATE TABLE tags (userId INTEGER,movieId INT,tag TEXT,timestamp TIMESTAMP);") 
with open('ml-latest-small/tags.csv', encoding="utf8") as csv_file:
    #uses first line in file for column headings by default
    reader = csv.DictReader(csv_file) # comma is default delimiter
    to_db = [(row['userId'], row['movieId'], row['tag'],row['timestamp']) for row in reader]   
cur.executemany("INSERT INTO tags (userId,movieId,tag,timestamp) VALUES (?, ?, ?, ?);", to_db)
db.commit()

db.execute("CREATE TABLE links (movieId INTEGER,imdbId INTEGER,tmdbId INTEGER);") 
with open('ml-latest-small/links.csv', encoding="utf8") as csv_file:
    #uses first line in file for column headings by default
    reader = csv.DictReader(csv_file) # comma is default delimiter
    to_db = [ (row['movieId'], row['imdbId'],row['tmdbId']) for row in reader]  
cur.executemany("INSERT INTO links (movieId,imdbId,tmdbId) VALUES (?, ?, ?);", to_db)
db.commit()

############################
# load rating data 
############################
sql = """SELECT userId,movieId,rating
         FROM ratings
      """
cur.execute(sql)
data = cur.fetchall()

############################
# load movie data with some aggregations
############################
sql2 = """with rating_sum as 
                (SELECT  movieId,round(avg(rating),1) as rating, count(rating) as rating_cnt 
                 FROM ratings 
                 GROUP BY movieId),
                tags_combi as 
                (SELECT t1.movieId, GROUP_CONCAT(t2.tag) as all_tags
                 FROM tags t1 LEFT JOIN  tags t2
                 ON t1.movieId = t2.movieId 
                 GROUP BY t1.movieId)
         SELECT 
              m.movieId, 
              m.title,
              m.genres,
              r.rating as rating,
              r.rating_cnt as rating_cnt,
              t.all_tags,
              l.imdbId,
              l.tmdbId

         
         FROM movies m
         LEFT JOIN rating_sum r ON (m.movieId=r.movieId)
         LEFT JOIN tags_combi t ON (m.movieId=t.movieId)
         LEFT JOIN links l ON (m.movieId=l.movieId)

"""
cur.execute(sql2)
data2 = cur.fetchall()

############################
# making a panda dataframe
############################
df_mov = pd.DataFrame(data2 ,columns=['movie_Id', 'title', 'genres','rating','rating_cnt','tags','imdb_Id','tmdb_Id'])


def extract_year(title): 
    pattern='\(([0-9]{4})\)'
    try:
        year = re.findall(pattern, title)[0]
    except:
        year=1900
    return int(year)

df_mov['year'] = df_mov['title'].apply(extract_year)

############################
# NMF model for ratings data
############################
df_rat = pd.DataFrame(data ,columns=['user_Id','movie_Id','rating'])
df_rat = df_rat.set_index(['user_Id','movie_Id'])
df_rat = df_rat.unstack(1)
df_rat = df_rat.fillna(df_rat.mean())

# working copy
df_org = df_rat.copy()
nmf = NMF(n_components=3)
nmf.fit(df_rat)

# Pickle
binary = pickle.dumps(nmf)
open('nmf_model.bin', 'wb').write(binary)
binary = open('nmf_model.bin', 'rb').read()
nmf = pickle.loads(binary)

# P & Q values 
P = nmf.transform(df_rat)
Q = nmf.components_
nR = np.dot(P, Q)
df_out = pd.DataFrame(nR)



