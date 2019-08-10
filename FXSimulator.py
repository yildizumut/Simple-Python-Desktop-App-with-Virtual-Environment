# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 20:38:00 2019

@author: Umut YILDIZ
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import quandl
import os
import xlsxwriter
import datetime

# Setting Desktop folder as the working directory
drctry = os.path.join(os.environ['USERPROFILE'], 'Desktop')
os.chdir(drctry)

output_files = []

# Getting input from the user
# 1st Input: Historical Start Date
while True:
    try:
        hist_1_input = input("\nWrite 'exit' to quit!\nFormat for the date: YYYY-MM-DD\nEnter the Historical Start Date: ")
        if hist_1_input == "exit":
            exit()
        else:
            hist_1 = pd.to_datetime(hist_1_input + " 00:00:00", format="%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        break
    except ValueError:
        print("\nENTER A VALID DATE !\n")

# 2nd Input: Forward End Date
while True:
    try:
        fwd_2_input = input("\nWrite 'exit' to quit!\nFormat for the date: YYYY-MM-DD\nEnter the Forward End Date: ")
        if fwd_2_input == "exit":
            exit()
        else:
            fwd_2 = pd.to_datetime(fwd_2_input + " 00:00:00", format="%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        break
    except ValueError:
        print("\nENTER A VALID DATE !\n")
        
# 3rd Input: Number of Scenarios
while True:
    try:
        scen_size = input("\nWrite 'exit' to quit!\nNumber of scenarios should be an integer !\nEnter the Number of Scenarios you want to run: ")
        if scen_size == "exit":
            exit()
        elif float(scen_size) / int(scen_size) == 1:
            scen_size = int(scen_size)
            break
    except ValueError:
        print("\nENTER A INTEGER !\n")
        
# 4th Input: Implied Volatiliy
while True:
    try:
        implied_volatility = input("\nWrite 'exit' to quit!\nFor automatic volatility calculation, write \'omit\' !\n" +
                                "Implied Volatility value should be given as a percentage in decimal format, e.g. 0.01 !\n" + "Enter the Implied Volatility: ")
        if implied_volatility == "exit":
            exit()
        elif implied_volatility == 'omit':
            implied_volatility_check = False
            break
        elif type(implied_volatility) is float:
            implied_volatility_check = True
            implied_volatility = float(implied_volatility)
            break
    except ValueError:
        print("\nENTER A VALID IMPLIED VOLATILITY !\n")
        
hist_start = pd.to_datetime(hist_1, format = "%Y-%m-%d")
hist_end = pd.to_datetime(pd.to_datetime('today').strftime("%Y-%m-%d"), format = "%Y-%m-%d") - pd.Timedelta('1 days')

start =  pd.to_datetime(pd.to_datetime('today').strftime("%Y-%m-%d"), format = "%Y-%m-%d")
end = pd.to_datetime(fwd_2, format = "%Y-%m-%d")

# Retrieving exchange rate data from Quandl
eur_usd = quandl.get("ECB/EURUSD", authtoken="py3UYy43X9dTYJb7X6es", start_date = hist_start.strftime("%Y-%m-%d"))

USDdata = (1 / eur_usd).reset_index()
USDdata.columns = ['Date', 'USD']

USDdata["Date"] = pd.to_datetime(USDdata["Date"], format = "%Y-%m-%d")
print("\nUSD Data Retrieved - Information:\n")
print(USDdata.info())
print("--------------------------------------------------------------------------------")

print(USDdata.head())
print(USDdata.tail())

# Creating simulations using GBM
# Daily returns of the historical exchange rates
returns = (USDdata.loc[1:, 'USD'] - USDdata.shift(1).loc[1:, 'USD']) / USDdata.shift(1).loc[1:, 'USD']

print("\n\no-o-o-o-o-o-o-o-o-o-o-o PROGRAM INITIATED o-o-o-o-o-o-o-o-o-o-o-o\n")
# Geometric Brownian Motion

# Parameter Definitions
# So    :   initial exchange rate (yesterday's exchange rate)
# dt    :   time increment -> a day in our case
# T     :   length of the prediction time horizon(how many time points to predict, same unit with dt(days))
# N     :   number of time points in prediction the time horizon -> T/dt
# t     :   array for time points in the prediction time horizon [1, 2, 3, .. , N]
# mu    :   mean of historical daily returns
# sigma :   standard deviation of historical daily returns
# W     :   array for brownian path
# b     :   array for brownian increments

# Parameter Assignments
So = USDdata["USD"].values[USDdata.shape[0]-1]
dt = 1 # 1 day
T = pd.Series(pd.date_range(start, end)).map(lambda x: # Length of the prediction time horizon, same unit with dt
                                             1 if x.isoweekday() in range(1,6) else 0).sum() # only weekdays
N = T / dt
t = np.arange(1, int(N) + 1)
mu = np.mean(returns)
sigma = [implied_volatility if implied_volatility_check else np.std(returns)][0]
b = {str(scen): np.random.normal(0, 1, int(N)) for scen in range(1, scen_size + 1)}
W = {str(scen): b[str(scen)].cumsum() for scen in range(1, scen_size + 1)}

print("\n-> GBM is progressing !")
# Prediction with GBM
drift = (mu - 0.5 * sigma**2) * t
diffusion = {str(scen): sigma * W[str(scen)] for scen in range(1, scen_size + 1)}
S = np.array([So * np.exp(drift + diffusion[str(scen)]) for scen in range(1, scen_size + 1)]) 
S = np.hstack((np.array([[So] for scen in range(scen_size)]), S))

# Plotting the simulated rates and creating .png
# Plotting the simulations
plt.figure(figsize = (20,10))
for i in range(scen_size):
    plt.title("Daily Volatility: " + str(sigma / np.sqrt(1 / dt)))
    plt.plot(pd.date_range(start = hist_end, end = end, freq = 'D').map(lambda x: 
                                                                    x if x.isoweekday() in range(1,6) else np.nan).dropna()
             ,S[i, :])
    plt.ylabel('USD Rate, (€/$)')

# Saving the plot as .png file into drctry which is Desktop in our case
# Name of the plot is FX_Sim_Graph_(prediction_start_date)_to_(prediction_end_date).png
print("\n-> Simulation results and graph are being created !")
figure_name = "FX_Sim_Graph_" + start.strftime("%d%m%Y") + "_to_" + end.strftime("%d%m%Y") + ".png"
output_files.append(figure_name)
plt.savefig(drctry + "\\" + figure_name)

# Writing the scenarios into .xlsx using xlsxwriter
# Create a sequence of dates between start and end that includes also the weekends
# Weekend FX rates will be equal to the most recent weekday FX rate
S_wknd = np.copy(S)

all_fwd_dates = pd.Series(pd.date_range(start, end))
wknd_check = all_fwd_dates.map(lambda x: 1 if x.isoweekday() in range(6,8) else 0)
wknd_indices = wknd_check[wknd_check == 1].index

for i in wknd_indices:
    S_wknd = np.insert(S_wknd, i, S_wknd[:,i-1], axis = 1)

excel_name = "Daily_FX_Simulations_" + start.strftime("%d%m%Y") + "_to_" + end.strftime("%d%m%Y") + ".xlsx"
output_files.append(excel_name)

# Create the Excel file
workbook = xlsxwriter.Workbook(drctry + "\\" + excel_name) # On the Desktop with the name assigned just above
worksheet = workbook.add_worksheet() # add a worksheet

worksheet.write(0, 0, "Scenario") 
worksheet.write_column(1, 0, np.arange(1, scen_size + 1)) # Scenario numbers
worksheet.write_row(0, 1, pd.Series(pd.date_range(hist_end, end)).map(lambda x: 
                                                                      x.strftime("%Y-%m-%d"))) # prediction time horizon

col = 1
for row, data in enumerate(S_wknd):
    worksheet.write_row(row + 1, col, data) # append each scenario to the related row

workbook.close()

# Collecting the output files into a folder
cur_time = "From_" + start.strftime("%d%m%Y") + "_to_" + end.strftime("%d%m%Y") + "_RunDate_" + \
                                            datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
os.makedirs(drctry + "\\" + cur_time)

for carry in output_files:
    os.rename(drctry + "\\" + carry, drctry + "\\" + cur_time + "\\" + carry)

print("\n\no-o-o-o-o-o-o-o-o-o-o-o CODE RUN COMPLETED o-o-o-o-o-o-o-o-o-o-o-o")

pydir = os.path.dirname(os.path.realpath(__file__))
print(pydir)

while True:
    run_again = input("\nDo you want to run the program again ? (yes / no): ")
    if run_again == "yes":
        os.system(pydir + '\\Scripts\\python.exe ' + pydir + '\\FXSimulator.py')
        break
    elif run_again == "no":
        break