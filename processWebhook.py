from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS, cross_origin
import requests
app = Flask(__name__)
CORS(app)

@app.route("/", methods=['POST','GET'])
@cross_origin(supports_credentials=True)

def uploadFile():
    Load_Energy = []
    sent_data = request.get_json()
    print(sent_data[1])
    for row in sent_data[0]:
        Load_Energy.append(row['PV Energy'] + row['Utility Import Energy'] - row['Utility Export Energy'])

    a = 1
    day = 1
    Total_day = []
    each_30 = []
    total_day = []

    for i in Load_Energy:
        each_30.append(i)
        if a == 48:
            total_day.append(each_30)
            each_30 = []
            Total_day.append("Day" + str(day))
            a = 0
            day += 1
        a += 1


    highest_day = []  # Hightest Value in Each 30 minutes in day
    i = 0
    while len(total_day) > i:
        highest_day.append(max(total_day[i]))
        i += 1


    MD_Reduction = int(sent_data[3])

    MD = []
    i = 0
    while len(highest_day) > i:
        MD.append(highest_day[i] * 2)
        i += 1


    Total = 100 - MD_Reduction
    MD_Threshold = []

    i = 0
    while len(MD) > i:
        MD_Threshold.append(MD[i] * Total / 100)
        i += 1
    print("MD Threshold: " + str(MD_Threshold) + "(kW)")

    More_than_Energy = []  # kWh
    i = 0
    while len(MD) > i:
        More_than_Energy.append(MD_Threshold[i] / 2)
        i += 1

    Battery_Discharged_Energy_Each_Day = []
    Battery_Discharged_30 = []
    b = 0
    while len(total_day) > b:
        Battery_Discharged_Energy_Each_30 = []
        for i in total_day[b]:
            if i > More_than_Energy[b]:
                Battery_Discharged_Energy_Each_30.append(i - More_than_Energy[b])
        b += 1
        Battery_Discharged_30.append(Battery_Discharged_Energy_Each_30)
        Battery_Discharged_Energy_Each_Day.append(sum(Battery_Discharged_Energy_Each_30))
    Battery_Discharged_Energy = Battery_Discharged_Energy_Each_Day

    Battery_capacity = []

    i = 0
    while len(Battery_Discharged_Energy) > i:
        Battery_capacity.append(Battery_Discharged_Energy[i] / 0.9)
        i += 1

    perk_period_price = 45.1  # For each kilowatt of maximum demand per month during the peak period
    MD_Charges = []  # RM
    i = 0
    while len(MD) > i:
        MD_Charges.append(MD[i] * perk_period_price)
        i += 1

    Each_Battery_kWh_Cost = int(sent_data[1])  # USD/kWh
    RM = 4.2  # 1USD = RM4.2
    Battery_Cost = []

    i = 0
    while len(MD) > i:
        Battery_Cost.append(Battery_capacity[i] * Each_Battery_kWh_Cost * RM)
        i += 1

    Each_Inverter_kW_Cost = int(sent_data[2])  # USD/kW
    Inverter_Cost = []
    b = 0

    while len(Battery_Discharged_Energy_Each_Day) > b:
        Inverter_Cost_Each_30 = []

        if Battery_Discharged_30[b] == []:
            Inverter_Cost_Each_30.append(0 * 1.5 * Each_Inverter_kW_Cost * RM)
        else:
            Inverter_Cost_Each_30.append(max(Battery_Discharged_30[b]) * 1.5 * Each_Inverter_kW_Cost * RM * 2)
        b += 1
        Inverter_Cost.append(sum(Inverter_Cost_Each_30))

    Investment = []

    i = 0
    while len(Inverter_Cost) > i:
        Investment.append((Battery_Cost[i] + Inverter_Cost[i]))
        i += 1

    MD_Saving_Per_Year = []

    i = 0
    while len(Inverter_Cost) > i:
        MD_Saving_Per_Year.append(MD_Charges[i] * MD_Reduction / 100 * 12)
        i += 1

    Save = 0.141  # 0.141 is the price difference between the peak and off peak tariff, we will basically save 0.141 per kWh
    Day = 365  # 1 Year How many day?
    Energy_Trading_profit_per_year = []

    i = 0
    while len(Battery_Discharged_Energy) > i:
        Energy_Trading_profit_per_year.append(Battery_Discharged_Energy[i] * Save * Day)
        i += 1

    Total_Saving = []

    i = 0
    while len(MD_Saving_Per_Year) > i:
        Total_Saving.append(MD_Saving_Per_Year[i] + Energy_Trading_profit_per_year[i])
        i += 1

    ROI = []
    i = 0
    while len(Investment) > i:
        ROI.append(round(Investment[i] / Total_Saving[i], 2))
        i += 1
    print(ROI)

    MD_Saving_Per_Day = []

    i = 0
    while len(Inverter_Cost) > i:
        MD_Saving_Per_Day.append(MD_Charges[i] * MD_Reduction / 100 /31)
        i += 1

    Energy_Trading_profit_per_day = []
    i = 0
    while len(Battery_Discharged_Energy) > i:
        Energy_Trading_profit_per_day.append(Battery_Discharged_Energy[i] * Save)
        i += 1

    Total_Saving_Day = []
    i = 0
    while len(MD_Saving_Per_Year) > i:
        Total_Saving_Day.append(MD_Saving_Per_Day[i] + Energy_Trading_profit_per_day[i])
        i += 1

    return ({'roi':ROI, 'day': Total_day, 'saving_per_day': Total_Saving_Day})

@app.route("/realtime", methods=['POST','GET'])
@cross_origin(supports_credentials=True)

def realTime():
    Load_Energy = []
    sent_data = request.get_json()
    print(sent_data)

    url = 'http://asplm-cloud.ddns.net:8080/Thingworx/Things/SolarSentryDB/Services/api_DashboardChart_Energy_30Min'
    appKey = str('ee4b6afb-30f5-4b1d-82ea-ceab37ba7620')
    SiteID = str(2)
    FromDT = str(sent_data[3])
    ToDT = str(sent_data[4])
    r = requests.Request(method='POST',
                         url=url + '?appKey=' + appKey + '&SiteID=' + SiteID + '&FromDT=' + FromDT + '&ToDT=' + ToDT,
                         headers={
                             'Content-Type': 'application/json',
                             'Accept': 'application/json',
                             'Token': 'ee4b6afb-30f5-4b1d-82ea-ceab37ba7620'
                         }).prepare()

    s = requests.Session()
    rsp = s.send(r)
    data = rsp.json()

    s.close()

    a = 1
    days = []
    for row in data['rows']:
        Load_Energy.append(row['kWh_Import_PV'] + row['kWh_Import_TNB'] - row['kWh_Export_PV'])
        if a == 48:
            days.append(row['GroupLabel'][:11])
            a = 0
        a += 1
    print(days)
    a = 1
    day = 1
    Total_day = []
    each_30 = []
    total_day = []

    for i in Load_Energy:
        each_30.append(i)
        if a == 48:
            total_day.append(each_30)
            each_30 = []
            Total_day.append("Day" + str(day))
            a = 0
            day += 1
        a += 1


    highest_day = []  # Hightest Value in Each 30 minutes in day
    i = 0
    while len(total_day) > i:
        highest_day.append(max(total_day[i]))
        i += 1


    MD_Reduction = int(sent_data[2])

    MD = []
    i = 0
    while len(highest_day) > i:
        MD.append(highest_day[i] * 2)
        i += 1


    Total = 100 - int(sent_data[2])
    MD_Threshold = []

    i = 0
    while len(MD) > i:
        MD_Threshold.append(MD[i] * Total / 100)
        i += 1
    # print("MD Threshold: " + str(MD_Threshold) + "(kW)")

    More_than_Energy = []  # kWh
    i = 0
    while len(MD) > i:
        More_than_Energy.append(MD_Threshold[i] / 2)
        i += 1
    # print(More_than_Energy)

    Battery_Discharged_Energy_Each_Day = []
    Battery_Discharged_30 = []
    b = 0
    while len(total_day) > b:
        Battery_Discharged_Energy_Each_30 = []
        for i in total_day[b]:
            if i > More_than_Energy[b]:
                Battery_Discharged_Energy_Each_30.append(i - More_than_Energy[b])
        b += 1
        Battery_Discharged_30.append(Battery_Discharged_Energy_Each_30)
        Battery_Discharged_Energy_Each_Day.append(sum(Battery_Discharged_Energy_Each_30))
    Battery_Discharged_Energy = Battery_Discharged_Energy_Each_Day

    Battery_capacity = []

    i = 0
    while len(Battery_Discharged_Energy) > i:
        Battery_capacity.append(Battery_Discharged_Energy[i] / 0.9)
        i += 1

    perk_period_price = 45.1  # For each kilowatt of maximum demand per month during the peak period
    MD_Charges = []  # RM
    i = 0
    while len(MD) > i:
        MD_Charges.append(MD[i] * perk_period_price)
        i += 1

    Each_Battery_kWh_Cost = int(sent_data[0])  # USD/kWh
    RM = 4.2  # 1USD = RM4.2
    Battery_Cost = []

    i = 0
    while len(MD) > i:
        Battery_Cost.append(Battery_capacity[i] * Each_Battery_kWh_Cost * RM)
        i += 1

    Each_Inverter_kW_Cost = int(sent_data[1])  # USD/kW
    Inverter_Cost = []
    b = 0

    while len(Battery_Discharged_Energy_Each_Day) > b:
        Inverter_Cost_Each_30 = []

        if Battery_Discharged_30[b] == []:
            Inverter_Cost_Each_30.append(0 * 1.5 * Each_Inverter_kW_Cost * RM)
        else:
            Inverter_Cost_Each_30.append(max(Battery_Discharged_30[b]) * 1.5 * Each_Inverter_kW_Cost * RM * 2)
        b += 1
        Inverter_Cost.append(sum(Inverter_Cost_Each_30))

    Investment = []

    i = 0
    while len(Inverter_Cost) > i:
        Investment.append((Battery_Cost[i] + Inverter_Cost[i]))
        i += 1

    MD_Saving_Per_Year = []

    i = 0
    while len(Inverter_Cost) > i:
        MD_Saving_Per_Year.append(MD_Charges[i] * MD_Reduction / 100 * 12)
        i += 1

    Save = 0.141  # 0.141 is the price difference between the peak and off peak tariff, we will basically save 0.141 per kWh
    Day = 365  # 1 Year How many day?
    Energy_Trading_profit_per_year = []

    i = 0
    while len(Battery_Discharged_Energy) > i:
        Energy_Trading_profit_per_year.append(Battery_Discharged_Energy[i] * Save * Day)
        i += 1

    Total_Saving = []

    i = 0
    while len(MD_Saving_Per_Year) > i:
        Total_Saving.append(MD_Saving_Per_Year[i] + Energy_Trading_profit_per_year[i])
        i += 1

    ROI = []
    i = 0
    while len(Investment) > i:
        ROI.append(round(Investment[i] / Total_Saving[i], 2))
        i += 1
    print(ROI)

    MD_Saving_Per_Day = []

    i = 0
    while len(Inverter_Cost) > i:
        MD_Saving_Per_Day.append(MD_Charges[i] * MD_Reduction / 100 /31)
        i += 1

    Energy_Trading_profit_per_day = []
    i = 0
    while len(Battery_Discharged_Energy) > i:
        Energy_Trading_profit_per_day.append(Battery_Discharged_Energy[i] * Save)
        i += 1

    Total_Saving_Day = []
    i = 0
    while len(MD_Saving_Per_Year) > i:
        Total_Saving_Day.append(round(MD_Saving_Per_Day[i] + Energy_Trading_profit_per_day[i],2))
        i += 1

    return ({'roi':ROI, 'day': days, 'saving_per_day': Total_Saving_Day, 'battery_capacity': Battery_capacity, 'investment':Investment, 'saving_per_year':MD_Saving_Per_Year })

@app.route("/Information", methods=['POST','GET'])
@cross_origin(supports_credentials=True)

def Information():
    sent_data = request.get_json()
    url = 'http://asplm-cloud.ddns.net:8080/Thingworx/Things/SolarSentryDB/Services/api_DashboardChart_Energy'
    appKey = str('ee4b6afb-30f5-4b1d-82ea-ceab37ba7620')
    SiteID = str(2)
    InDate = sent_data[0]
    GroupBy = sent_data[1]

    print(sent_data)
    r = requests.Request(method='POST',
                         url=url + '?appKey=' + appKey + '&SiteID=' + SiteID + '&InDate=' + InDate + '&GroupBy=' + GroupBy,
                         headers={
                             'Content-Type': 'application/json',
                             'Accept': 'application/json',
                             'Token': 'ee4b6afb-30f5-4b1d-82ea-ceab37ba7620'
                         }).prepare()

    s = requests.Session()
    rsp = s.send(r)
    data = rsp.json()
    s.close()

    day = []
    time = []
    kWh_Export_PV = []
    kWh_Import_TNB = []
    kWh_Import_PV = []
    kW_Import_TNB = []
    kW_Import_PV = []
    load = []
    for row in data['rows']:
        # print(row)
        kWh_Export_PV.append(row['kWh_Export_PV'])
        kWh_Import_TNB.append(row['kWh_Import_TNB'])
        kWh_Import_PV.append(row['kWh_Import_PV'])
        kW_Import_TNB.append(row['kWh_Import_TNB'] * 2)
        kW_Import_PV.append(row['kWh_Import_PV'] * 2)
        if(sent_data[1] == 'Month'):
            time.append(row['GroupLabel'])
        elif(sent_data[1] == 'Year'):
            time.append(row['GroupLabel'][5:7])
        else:
            time.append(row['GroupLabel'][11:16])
        day.append(row['GroupLabel'][:11])
        load.append((row['kWh_Import_PV'] * 2) + (row['kWh_Import_TNB'] * 2))

    return({"kWh_Export_PV": kWh_Export_PV, "kWh_Import_TNB": kWh_Import_TNB, "kWh_Import_PV": kWh_Import_PV,"kW_Import_PV": kW_Import_PV, "kW_Import_TNB": kW_Import_TNB,"load": load, 'day': day, 'time': time})

if __name__ == '__main__':
    app.run(debug=True)


