#flask.pocoo.org 

from flask import Flask, render_template, session
from flask import request
import RatingsInput
import recomms
import sqlite3




############################
# set up SQLite DB
############################
db =sqlite3.connect('MoviesData.db')
cur = db.cursor()
db

app = Flask(__name__)
app.secret_key = 'You Will Never Guess'


@app.route('/')
def index():
	return  render_template('main.html', title='My Movies' , page_name='Main Page')

		   
@app.route('/ratings' , methods=['GET','POST']) # <-- decorator
def Ratings():
	getmovie1 = request.args['movie1']
	getmovie2 = request.args['movie2']
	getmovie3 = request.args['movie3']
	matchedmovies = RatingsInput.match_title(getmovie1,getmovie2,getmovie3) 
	session["mov1"]=([(tup[0]) for tup in matchedmovies][0])
	session["mov2"]=([(tup[0]) for tup in matchedmovies][1])
	session["mov3"]=([(tup[0]) for tup in matchedmovies][2])

	return render_template('GetRatings.html',  #Jinja template
							cleanmovie1= session["mov1"],
							cleanmovie2= session["mov2"], 
							cleanmovie3= session["mov3"],
							input = (getmovie1,getmovie2,getmovie3)
						  )
						  
@app.route('/result' , methods=['GET','POST']) # <-- decorator
def Recomms():
	getrating1 = request.args['rating1']
	getrating2 = request.args['rating2']
	getrating3 = request.args['rating3']
	mov1 = session["mov1"]
	mov2 = session["mov2"]
	mov3 = session["mov3"]

	movies = recomms.get_recommendations(mov1,mov2,mov3,getrating1,getrating2,getrating3) 	 
	print(type(movies))

	print(movies)
	print(movies[0])
	return render_template('result.html',  #Jinja template
							comedy= movies[0],
							drama= movies[1], 
							action= movies[2],
						  )