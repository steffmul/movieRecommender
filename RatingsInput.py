# find movies titles
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

# create movies  dataframe for lookup
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

df_mov = pd.DataFrame(data2 ,columns=['movie_Id', 'title', 'genres','rating','rating_cnt','tags','imdb_Id','tmdb_Id'])

def extract_year(title): 
    pattern='\(([0-9]{4})\)'
    try:
        year = re.findall(pattern, title)[0]
    except:
        year=1900
    return int(year)
	
df_mov['year'] = df_mov['title'].apply(extract_year)


def match_title(getmovie1,getmovie2,getmovie3):
	movie1_c = process.extractOne( getmovie1, df_mov['title'])
	movie2_c = process.extractOne( getmovie2, df_mov['title'])
	movie3_c = process.extractOne( getmovie3, df_mov['title'])
	return movie1_c,movie2_c,movie3_c
	 
