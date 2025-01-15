import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 

from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV, KFold, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Regression Models
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor

# Gradient Boosting Libraries
from xgboost import XGBRegressor
from catboost import CatBoostRegressor # type: ignore
from sklearn.preprocessing import StandardScaler
import yfinance as yf # type: ignore

import datetime
import sys
import warnings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s- %(message)s',
    handlers=[
        logging.FileHandler("Stock_Prediction.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
def get_data(company_symbol,period='1mo',interval='1d'):
    try: 
    
        logging.info(f"Fetching data for company {company_symbol}")
        data=yf.download(company_symbol,period=period,interval=interval)
        if data.empty:
            logging.error(f"Error While downloading the data")
            return None
        data.columns=['_'.join(col).strip() for col in data.columns.to_flat_index()]
        data.reset_index(inplace=True)
        data.columns=['Date','Close','High','Low','Open','Volume']
        logging.info(f"Successfully Retrived data for company {company_symbol} for {len(data)}")
        if data is None or len(data) < 2:
            logging.error("Insufficient data for training.")
            return
        return data
    except :
        logging.error(f"Error occured while retrieving the data for company {company_symbol}")
        return None


def train(data):
    data=data.dropna(subset=['prev_open','prev_high','prev_low','prev_vol','Lag1','Lag2','ma_10','RSI','MACD','BB_middle','OBV','Pivot','Close'])
    if data.shape[0] < 2:
        logging.error("Insufficient data for training. Need at least 2 samples.")
        return None
    x=data[['prev_open','prev_high','prev_low','prev_vol','Lag1','Lag2','ma_10','RSI','MACD','BB_middle','OBV','Pivot']]
    y=data['Close']
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
 
    model=model_selection(x_scaled,y)
    print("Best found model is ",model)
    model.fit(x_scaled,y)
    return model
def model_selection(x,y):
    models={
        'linear_regression': LinearRegression(),
        'ridge': Ridge(),
        'lasso': Lasso(),
        # 'elasticnet': ElasticNet(),
        'random_forest': RandomForestRegressor(),
        'gradient_boosting': GradientBoostingRegressor(),
        'svr': SVR(),
        # 'knn': KNeighborsRegressor(),
        'xgboost': XGBRegressor(),
        'catboost': CatBoostRegressor(verbose=0)
    }

    param_grids={
        'linear_regression': {} ,
        'ridge': {'alpha': [0.1,1,10]},
        'lasso': {'alpha': [0.1,1,10]} ,
        # 'elasticnet':{'alpha': [0.1,1,10],'l1_ratio':[0.1,0.5,0.9]} ,
        'random_forest': {'n_estimators': [50,100,200],'max_depth': [5,10,None]},
        'gradient_boosting':{'n_estimators': [50,100,200],'learning_rate':[0.01,0.1,0.5]},
        'svr':{'C': [0.1,1,10],'gamma': ['scale','auto'],'kernel': ['linear','rbf','poly']} ,
        # 'knn':{'n_neighbors': [3,5,7]} ,
        'xgboost':{'n_estimators': [50, 100, 200], 'learning_rate': [0.01, 0.1, 0.5]} ,
        'catboost':{'n_estimators': [50, 100, 200], 'learning_rate': [0.01, 0.1, 0.5]}
    
    }

    best_model=None
    best_score=float('-inf')

    for model_name, model in models.items():
        try:

            logging.info(f"Training {model_name}")
            gridsearch=GridSearchCV(estimator=model,param_grid=param_grids.get(model_name),cv=TimeSeriesSplit(n_splits=5),scoring='neg_mean_squared_error',n_jobs=-1)
            gridsearch.fit(x,y)
            logging.info(f"model: {model_name} with score: {gridsearch.best_score_}")

            if(gridsearch.best_score_>best_score):
                best_score=gridsearch.best_score_
                best_model=gridsearch.best_estimator_
                logging.info(f"New best model found: {model} with score :{best_score}")
                
        except Exception as e:
            logging.info(f"Failed to fit this data due to unexpected error {e}")

    return best_model
def get_next_day_data(data):
    try:

        latest_data=data.iloc[-1].copy()
        next_day = pd.DataFrame(columns=['prev_open','prev_high','prev_low','prev_vol','Lag1','Lag2','ma_10','RSI','MACD','BB_middle','OBV','Pivot'])
        next_day.loc[0,'Lag1']=latest_data['Close']
        next_day.loc[0,'Lag2']=latest_data['Lag1']
        next_day.loc[0,'prev_high']=latest_data['High']
        next_day.loc[0,'prev_low']=latest_data['Low']
        next_day.loc[0,'prev_open']=latest_data['Open']
        next_day.loc[0,'prev_vol']=latest_data['Volume']
        next_day.loc[0,'ma_10']=data['Close'].tail(10).mean()
        next_day.loc[0,'RSI']=latest_data['RSI']
        next_day.loc[0,'MACD'] = latest_data['MACD']
        next_day.loc[0,'BB_middle'] = latest_data['BB_middle']
        next_day.loc[0,'OBV'] = latest_data['OBV']
        next_day.loc[0,'Pivot'] = latest_data['Pivot']
        return next_day
    except:
        logging.warnings("Failed to claculate features for current Prediction")
def predict(model,next_data):
    try:
        # Ensure the scaler has been fitted earlier with training data
        scaler=StandardScaler()
        next_data_scaled = scaler.fit_transform(next_data)
        pred = model.predict(next_data_scaled)
        return pred[0]
    except Exception as e:
        logging.warning(f"Error occurred while predicting: {str(e)}")
        return None

def plot_price_analysis(data):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data['Date'], data['Close'], label='Close Price')
    ax.set_title('Closing Price Trend')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price ($)')
    return fig

def plot_vol_analysis(data):
    fig,ax=plt.subplots(figsize=(10,6))
    ax.plot(data['Date'],data['Volume'],label="Vol")
    ax.set_title("Volume Trend")
    ax.set_xlabel('Date')
    ax.set_ylabel('Volume')
    return fig

def plot_close_vs_ma(data):
    fig,ax=plt.subplots(figsize=(10,6))
    ax.plot(data['Date'], data['ma_5'], label='5-day MA')
    ax.plot(data['Date'], data['ma_10'], label='10-day MA')
    ax.plot(data['Date'], data['Close'], label='Close Price', alpha=0.5)
    ax.set_title('Moving Averages')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def plot_rsi(data):
    fig,ax=plt.subplots(figsize=(10,6))
    ax.plot(data['Date'],data['RSI'],label="RSI")
    ax.set_title("Rsi Trend")
    ax.set_xlabel('Date')
    ax.set_ylabel('RSI')
    return fig
def get_current_price(stock_symbol):
    try:
        ticker = yf.Ticker(stock_symbol)
        # Get the last traded price or close price
        current_data = ticker.history(period="1d", interval="1m")  # Fetch minute-level data
        current_price = current_data['Close'].iloc[-1]  # Get the most recent close price
        return current_price
    except Exception as e:
        print(f"Error fetching current price for {stock_symbol}: {e}")
        return None
    
from alpha_vantage.timeseries import TimeSeries#type:ignore
API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"
def fetch_current_price(company_symbol, api_key=API_KEY):
    try:
        # Logging the start of data retrieval
        logging.info(f"Fetching real-time data for company {company_symbol}")

        # Initialize Alpha Vantage TimeSeries API
        ts = TimeSeries(key=api_key, output_format="pandas")

        # Fetch real-time stock data
        data, meta_data = ts.get_quote_endpoint(symbol=company_symbol)

        # Check if data is empty
        if data.empty:
            logging.error("Error while downloading the data.")
            return None

        # Flatten and format the data
        data.reset_index(inplace=True)  # Ensure it's a tabular structure
        data = data.iloc[0]  # Extract the single row of quote data

        # Create a formatted DataFrame
        formatted_data = pd.DataFrame([{
            "Date": pd.Timestamp.now(),  # Current timestamp
            "Open": float(data['02. open']),
            "High": float(data['03. high']),
            "Low": float(data['04. low']),
            "Close": float(data['05. price']),
            "Volume": int(data['06. volume']),
        }])

        # Log success
        logging.info(f"Successfully retrieved real-time data for {company_symbol}")

        return formatted_data['Close'].iloc[0]
    except Exception as e:
        # Log any errors
        logging.error(f"Error occurred while retrieving the data for {company_symbol}: {str(e)}")
        return None
