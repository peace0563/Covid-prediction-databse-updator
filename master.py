import pandas as pd
from datetime import date,timedelta,datetime
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import json
import psycopg2
import requests

class covid_nineteen_predictor:
    def __init__(self):
        self.lr4 = None
        self.pr4 = None
        self.days = None
        self.conf = None
        self.dataset = None
        self.last_day_date_track = {}
        self.prediction_data_list = []
        
        
        
    def download_dataset(self):
        data_dicti = {}
        response = requests.get("https://api.covid19india.org/data.json")
        json_response = response.json()['cases_time_series']
        for count,data in enumerate(json_response,1):
            d_date = data["date"].split()
            d_date[1] = d_date[1][:3]
            d_date.append('2020')
            data_dicti[count] = [datetime.strptime(" ".join(d_date),'%d %b %Y').date(), data["totalconfirmed"]]
        self.dataset = pd.DataFrame.from_dict(data_dicti,orient='index', columns = ["Date","Cases"])
        
    
    def train_the_model(self):
        
        
        '''
        The dataset only contains total 3 cases from January to March,
        so we are removing the data from January to 1st of March
        '''
        total_days_consider = (date.today() - date(2020, 4, 15)).days

        dataset = self.dataset.iloc[(len(self.dataset)-total_days_consider):len(self.dataset)]

        self.days= pd.DataFrame([i for i in range(1,len(dataset.iloc[:, 0:1].values)+1)])
        self.conf= dataset.iloc[:, 1].values
        self.last_day_date_track = {(len(self.days)):date.fromisoformat(str(dataset.iloc[len(dataset)-1,0]).split()[0])}
        
        # fitting polynomial LR model with degree 4 to the dataset
        self.pr4 = PolynomialFeatures(degree = 4)
        x_poly4 = self.pr4.fit_transform(self.days)
        self.lr4 = LinearRegression()
        self.lr4.fit(x_poly4, self.conf)
        # by fit & transform x we got extra terms in x which are powers of x upto degree specified
        
    def predict(self,days):
        days_pred_desire = days
        last_day = list(self.last_day_date_track.keys())[0]
        p = 0
        for i in range(last_day+1,last_day+days_pred_desire+1):
            p += 1
            total_cases = "{:,}".format(int(round(*self.lr4.predict(self.pr4.fit_transform([[i]])))))
            pred_date = (self.last_day_date_track[last_day]+timedelta(p)).strftime('%d %b %Y')
            self.prediction_data_list.append({"pred_date":pred_date,"total_cases":total_cases,"predicted_on":datetime.now().strftime("%d %b %Y, %H:%M:%S")})
    
    def inserting_predict_data_to_database(self):

        #Loading the credentials file that has host URL, username, password of database server
        with open('./database_credentials.json') as p:
            cred = json.load(p)
        
        #Initiating a connection with database server
        conn = psycopg2.connect("dbname="+cred["dbname"]+" user="+cred["user"]+" host="+cred["host"]+" password="+cred["password"])
        cur = conn.cursor()
        #Removing the old predictions
        cur.execute("truncate new_data")
        
        #Insterting values into the table
        cur.executemany("""INSERT INTO new_data(date,total_cases,predicted_on) VALUES (%(pred_date)s, %(total_cases)s, %(predicted_on)s)""", self.prediction_data_list)
        cur.executemany("""INSERT INTO all_data(date,total_cases,predicted_on) VALUES (%(pred_date)s, %(total_cases)s, %(predicted_on)s)""", self.prediction_data_list)
        conn.commit()
        cur.close()
        conn.close()




def execut():
    cnin = covid_nineteen_predictor()
    cnin.download_dataset()
    cnin.train_the_model()
    n_days = 6 #Number of Days to predict
    cnin.predict(n_days)
    cnin.inserting_predict_data_to_database()

if __name__=="__main__":
    execut()
        




        
