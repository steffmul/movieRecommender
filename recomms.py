import sqlite3, csv, re, pickle
import pandas as pd
import numpy as np
from sklearn.decomposition import NMF
from fuzzywuzzy import process

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

def get_recommendations(mov1,mov2,mov3,getrating1,getrating2,getrating3):

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
		
	# add new row to ratings dataframe
	df_out = df_out.append(pd.Series([np.nan]), ignore_index = True)
	#lookup movie id from moview df
	id_returned1 = df_mov.loc[df_mov['title'] == mov1, 'movie_Id']
	id_returned2 = df_mov.loc[df_mov['title'] == mov2, 'movie_Id']
	id_returned3 = df_mov.loc[df_mov['title'] == mov3, 'movie_Id']

	
	# enter users rating
	
	df_out.iloc[-1, df_out.columns.get_loc(int(id_returned1)-1)] = int(getrating1)
	df_out.iloc[-1, df_out.columns.get_loc(int(id_returned2)-1)] = int(getrating2)
	df_out.iloc[-1, df_out.columns.get_loc(int(id_returned3)-1)] = int(getrating3)

	# duplicatethe user line and add average to the prediction data
	df_pred1 = df_out.tail(1)
	df_out = df_out.fillna(df_out.mean())
	df_pred2 = df_out.tail(1)
	df_out.drop(df_out.tail(1).index,inplace=True)

	# merge with movies dataframe
	df_pred = pd.concat([pd.DataFrame(df_pred1.T), pd.DataFrame(df_pred2.T)],
							  axis=1, 
							  ignore_index=True)
	df_pred.columns=['user_rating','calc_rating']
	df_pred = df_pred.join(df_mov)

	# filter movies from users 
	filtered = df_pred.loc[df_pred['user_rating'].isnull()]
	filtered = filtered[filtered.columns[1:8]]
	filtered = filtered.sort_values(by=['calc_rating','rating'], ascending=False)

	#Top 5 per genre
	comedies = filtered.loc[(filtered['genres'].str.contains('Comedy')) & (filtered['rating_cnt']>50)].head(3)
	drama = filtered.loc[(filtered['genres'].str.contains('Drama')) & (filtered['rating_cnt']>50)].head(3)
	action = filtered.loc[(filtered['genres'].str.contains('Action')) & (filtered['rating_cnt']>50)].head(3)
	
	return comedies['title'],drama['title'],action['title']
	
	"""
	comedies[['title','rating','calc_rating']]
	drama[['title','rating','calc_rating']]
	action[['title','rating','calc_rating']]
	"""