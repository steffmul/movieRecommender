import sqlite3, csv, re, pickle
import pandas as pd
import numpy as np
from sklearn.decomposition import NMF
from fuzzywuzzy import process

############################
# set up SQLite DB
############################
db =sqlite3.connect('movies2.db')
cur = db.cursor()
db

