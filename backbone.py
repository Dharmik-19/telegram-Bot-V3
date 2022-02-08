# from tkinter.tix import CheckList
#The above line was magically added, no clue why
import yfinance as yf
import pandas as pd
import plotly.express as px
from sklearn.linear_model import ridge_regression
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import io


class predict:
    def __init__(self, ticker):
        self.ticker = ticker
        

        stocks_df = yf.download(tickers=self.ticker, period='max', interval='1d')
        
        #Remove this if wantted, it just makes the times in IST which is not really required in out case
        #As we are working on the day to day time frame 
        # try:
        #     data = stocks_df.tz_localize('UTC')
        # except:
        #     pass
        # stocks_df = stocks_df.tz_convert(IST)    

        stocks_df = stocks_df.dropna()
        stocks_df.sort_values(by=['Date'], inplace=True)
        stocks_df.reset_index(inplace=True)

        #stocks_df.to_csv('newdata.csv')
        
        #stocks_df = pd.read_csv('newdata.csv')
        
        # stocks_df.to_csv('data.csv')
        
        
        self.ticker_df = stocks_df



    def get_df(self):
        return self.ticker_df

    
    def normaliseIt(self):
        x = self.ticker_df.copy()

        for i in self.ticker_df.columns[1:]:
            x[i] = x[i]/x[i][0]

        self.normalised_df = x
        return x    


    def interactivePlot(self, df, title):
        fig = px.line(title = title)
        data = df
        for stock in data.columns[1:]:
            fig.add_scatter(x=data['Date'], y=data[stock], name=stock)
        #fig.show()
        return fig
    

    
    # Function to concatenate the date, stock price, and volume in one dataframe

    def updatedTrading_window(self, df, days):
        n = days
        new_df = df.copy()
        new_df['Target'] = new_df['Close'].shift(-n)
        return new_df

    
    
    def updatedScaler(self, df):
        sc = MinMaxScaler(feature_range=(0,1))
        return [sc.fit_transform(df.drop(columns=['Date'])), sc]

    
    
    # def trainTestSplit(self, df):
    #     x = df[0][:, :2]
    #     y = df[0][:, 2:]

    #     split = int(0.65*len(df[0]))
    #     x_train, x_test = x[:split], x[split:]
    #     y_train, y_test = y[:split], y[split:]        

    #     return [x_train, x_test, y_train, y_test]

    
    
    def dataPlot(self, data, title):
        plt.figure(figsize=(15,7))
        plt.plot(data, linewidth=3)
        plt.title(title)
        plt.grid()
        plt.show()



    # def individual_stock(price_df, volume_df, stock):
    #     return (pd.DataFrame({'Date': price_df['Date'], 'Price':price_df[stock], 'Volume':volume_df[stock]}))
   

    def updatedPipelineV1(self, df, days):
        
        #To get the final prediction for a day's price, we need to store the min and max data so that we can scale up the final date 
        # and pass into the function of predict as a numpy array
        # We start from 1, as date is the first column in the dataframe
       
        Xmin = round(df.iloc[:, 1:].min(axis=0), 6)
        Xmax = round(df.iloc[:, 1:].max(axis=0), 6)
        #Min and max are the low and max of the following quantitites, OPEN, HIGH, LOW, CLOSE, ADJ CLOSE, VOLUME


        n = days
        new_df = df.copy()
        new_df['Target'] = new_df['Close'].shift(-n)
        ymin = round(new_df.iloc[:, 7:].min(axis=0),6)
        ymax = round(new_df.iloc[:, 7:].max(axis=0),6)
        #Adding the Target column and then we are finding the min and max associated with it. 
        #Corresponds to the target column. 

        scaler_data = [Xmin, Xmax, ymin, ymax]
        #Packaging these values, will be used for reverse transformation of the final prediction

        
        stock_trading_df = self.updatedTrading_window(df, days)[:-days]
        
        stock_trading_scaled_df_new = self.updatedScaler(stock_trading_df) 

        stock_trading_scaled_df = stock_trading_scaled_df_new[0]

        X = stock_trading_scaled_df[:, :6]
        # print(X)
        # test = (df.iloc[:-days, 1:2]-Xmin[0])/(Xmax[0]-Xmin[0]) 
        #Here, df.iloc[:-days, 1:2] find the values of the OPEN column.  
        # print(test)
        # The values of X and test are same, so we can say everything is fine.
        

        y = stock_trading_scaled_df[:, 6:]
        #print(y)
        #This y is infact same as the close of X (the column for Close, viz 4 from the start). Definitely the shift is taking place. 

        scale = int(0.8*len(stock_trading_scaled_df))
        X_train = X[:scale]
        X_test = X[scale:]
        y_train = y[:scale]
        y_test = y[scale:]
        return [X_train, X_test, y_train, y_test, X, y, stock_trading_scaled_df_new[0], stock_trading_scaled_df_new[1], scaler_data]







    

    def updatedRRModelStandAloneV1(self, df, alpha, days):
        #df is in the form of, {DATE, OPEN, HIGH, LOW, CLOSE, ADJ CLOSE, VOLUME}

       
        data = self.updatedPipelineV1(df, days)
        
        scaler_data = data[8]
        finalPred = df.iloc[-1, 1:]
        Xmin = scaler_data[0]
        Xmax = scaler_data[1]
        ymin = scaler_data[2]
        ymax = scaler_data[3]

        finalPred_x = (finalPred-Xmin)/(Xmax-Xmin)
        #The issue is, finalPred_x is pandas.core.series.Series, so we need to convert it to numpy array.
        
        finalPred_x = np.array(finalPred_x)
        finalPred_x = finalPred_x.reshape(1, -1)
        #https://towardsdatascience.com/get-into-shape-14637fe1cd32#:~:text=reshape(%2D1%2C%201)%20if,it%20contains%20a%20single%20sample.&text=We%20could%20change%20our%20Series,it%20to%20have%20two%20dimensions.
        #Reshape your data either using array.reshape(-1, 1) if your data has a single feature or array.reshape(1, -1) if it contains a single sample.
        #-1 in reshape function is used when you dont know or want to explicitly tell the dimension of that axis. E.g, If you have an array of shape (2,4) then reshaping it with (-1, 1), then the array will get reshaped in such a way that the resulting array has only 1 column and this is only possible by having 8 rows, hence, (8,1).
        # print(type(finalPred_x))
        # print(finalPred_x.shape) 
        last_clossing_price = float(df.iloc[-1, 4])

        
        # finalPred_x = np.reshape(finalPred_x, (6, 1))
        # print(finalPred_x.shape)
      
        #This above part is for the finalPrediction of today's date
        

        X_train = data[0]
        y_train = data[2]
        X_test = data[1]
        y_test = data[3]
        X = data[4]
        y = data[5]
        price_volume_target_scaled_df = data[6]
        scalar_variable = data[7]
        
    
        regression_model = Ridge(alpha=alpha)
        regression_model.fit(X_train, y_train)

        lr_accuracy = regression_model.score(X_test, y_test)
        #print("Linear Regression Score: ", lr_accuracy) 
        
        
        predicted_prices = regression_model.predict(X)

        price_volume_target_scaled_df_inverse = scalar_variable.inverse_transform(price_volume_target_scaled_df)
        #Price volume target was the old trio, new price consists of "OPEN, HIGH, LOW, CLOSE, ADJ CLOSE, VOLUME" and "Target"
        #This data is the inverse of that scaled data. 
       

        #This part is for replacing the target column of numpy array 'price_volume_target_scaled_df' by prediction
        dummy = price_volume_target_scaled_df
        
        Predicted = []
        for i in predicted_prices:
            Predicted.append(i[0])
        
        dummy[:, 6] = Predicted
        dummy = scalar_variable.inverse_transform(dummy)
        
        #print('\n\ndummy')
        #print(dummy)
        
        
        predicted_price_original = []
        close_price_original = []
        close_price_shifted_by_nDays = []

        for i in dummy:
            close_price_original.append(i[3])
            predicted_price_original.append(i[6])
        for i in price_volume_target_scaled_df_inverse:
            close_price_shifted_by_nDays.append(i[6])
       
           
        
        price_volume = df

        df_predicted = pd.DataFrame({'Date':df['Date'][:-days], 'Close': close_price_original, 'Predicted': predicted_price_original, 'Target': close_price_shifted_by_nDays})
        
        
        

        #We will now be making the final prediction for the prices of (+days) days from last price data.
        next_day_price_prediction = regression_model.predict(finalPred_x)
        #print(next_day_price_prediction[0][0])
        next_day_price_prediction = (ymax[0]-ymin[0])*next_day_price_prediction[0][0] + ymin[0]
        #print(next_day_price_prediction), print(last_clossing_price)
        #Above command does the reverse feature scaling and we get original predictedd price for tomorrow. 
        
        sum = 0 
        sum+=np.square(np.array(predicted_price_original)-np.array(close_price_shifted_by_nDays))
        #print('MSE between predicted price and the closeShifted prices: {}'.format(np.sum(sum)/len(sum))) 

        sum = 0 
        sum+=np.square(np.array(predicted_price_original)-np.array(close_price_original))
        #print('MSE between predicted price and the closing price of a particular day prices: {}'.format(np.sum(sum)/len(sum))) 

        
        #accuracy = clf.score(close_price_shifted_by_nDays, predicted_price_original)
        #print("The accuracy is:", accuracy_score)
        return [lr_accuracy, df_predicted, last_clossing_price, next_day_price_prediction]



    def get_metrics(self, predicted_df, date, stock_name, prediction):     
        
        len = predicted_df.shape[0]        
        predicted_df['True Error (with Target)'] = ((predicted_df['Target'] - predicted_df['Predicted'])/predicted_df['Target'])*100
        predicted_df['Day Error (with Close)'] = ((predicted_df['Close'] - predicted_df['Predicted'])/predicted_df['Close'])*100

        trueErrorSum = np.sum(np.abs(predicted_df['True Error (with Target)']))
        dayErrorSum = np.sum(np.abs(predicted_df['Day Error (with Close)']))
        
        trueError = trueErrorSum/len
        dayError = dayErrorSum/len

        #print('True Error Sum: {}'.format(trueError))
        #print('Day Error Sum: {}\n\n'.format(dayError))
        
        trueErrorAverage = np.average(predicted_df['True Error (with Target)'])
        dayErrorAverage = np.average(predicted_df['Day Error (with Close)'])
        trueErrorStdev = np.std(predicted_df['True Error (with Target)'])
        dayErrorStdev = np.std(predicted_df['Day Error (with Close)'])
        #print("True Error Average: {}".format(trueErrorAverage))
        #print("Day Error Average: {}".format(dayErrorAverage))
        #print("True Error Stdev: {}".format(trueErrorStdev))
        #print("Day Error Stdev: {}\n\n".format(dayErrorStdev))
        
        
        predicted_df.at[len, 'Date'] = date
        predicted_df.at[len, 'Predicted'] = prediction    
        
        # predicted_df.at[len+1, 'MAPE'] = 'MAPE'
        # predicted_df.at[len+1, 'True Error (with Target)'] = trueError
        # predicted_df.at[len+1, 'Day Error (with Close)'] = dayError


        minus_sd = trueErrorAverage-trueErrorStdev
        plus_sd = trueErrorAverage+trueErrorStdev

        #print("Range for True Error: {} to {}".format(plus_sd, minus_sd))
        #print("Range for Day Error: {} to {}\n\n".format(dayErrorAverage+dayErrorStdev, dayErrorAverage-dayErrorStdev))

        minus_price = (1+minus_sd/100)*prediction
        plus_price = (1+plus_sd/100)*prediction
        #print("Expected price range: {} - {}".format(minus_price, plus_price))
        #predicted_df['Date'] = predicted_df['Date'].apply(lambda x: x.strftime('%d-%m-%y'))
        #above line workks, trying .dt here
        #Trying to do it manually
        predicted_df['Date'][:-1].dt.strftime('%d-%m-%y')

        #predicted_df.to_csv('prediction_{}_{}.csv'.format(stock_name.upper(), date.strftime("%d/%m/%Y")))
        #Above one not working, below one is changing the date column to string. Need to work on saving the date at the end
        #predicted_df.to_csv('test_prediction.csv', date_format='%d-%m-%Y', index=False)       

        return [trueError, trueErrorAverage, trueErrorStdev, minus_sd, plus_sd, minus_price, plus_price, predicted_df]
        
        
        #predicted_df.to_csv('test_prediction.csv', index=False)
        return predicted_df
        plt.figure(figsize=(10,50))
        #sns.distplot(predicted_df['True Error (with Target)'], hist_kws={'color':'g'}, kde_kws={'color':'b', 'lw':3, 'label':'KDE'})
        #sns is a deprecated function and will be removed in a future version. 
        sns.displot(predicted_df['True Error (with Target)'], kde=True)
        plt.title('Mean absolute percentage error: {} prediction'.format(stock_name.upper()))
        plt.show()

        # try:
        #     predicted_df.to_csv('prediction_{}_{}.csv'.format(stock_name.upper(), date))
        # except:
        #     print('Falised')
        #     pass


    def get_histogram(self, df, stock_name):
        fig = plt.figure(figsize=(12,16))
        #sns.distplot(predicted_df['True Error (with Target)'], hist_kws={'color':'g'}, kde_kws={'color':'b', 'lw':3, 'label':'KDE'})
        #sns is a deprecated function and will be removed in a future version. 
        sns.displot(df['True Error (with Target)'], kde=True)
        plt.title('Mean absolute percentage error: {} prediction'.format(stock_name.upper()))
        #plt.show()
        plt.show()
        return fig


    def save_csv(self, df, stock_name, date):
        try:
            textStream = io.StringIO
            return textStream
            #if(not os.path.isdir('./prediction')): os.mkdir('predictions')
            #df.to_csv('./predictionsprediction_{}_{}.csv'.format(stock_name.upper(), date.strftime('%d%m%Y')), index=False)

        except:
            print("Could not return the csv file")
            