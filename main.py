import pandas as pd
import numpy as np

def geo_mean(iterable):
    """
    A function that calculates the geometric mean out of a series of numbers.
    """
    
    a = np.array(iterable)
    return a.prod()**(1.0/len(a))

def calc_ifr(ifr, population, old_defence_low = 65, old_defence_high = 120, old_defence_factor = 1):
    """
    A function that calculates Age Adjusted Infected Fatality Rate from various papers according to the Israeli population age pyramid, 
    and according to a defined min/max age of people which are successfully defended from infection.
    """
    
    population.loc[old_defence_low:old_defence_high,'Population'] *= old_defence_factor
    #Multipling the population number by the old people defence factor
    
    for i in ifr.index:    
        ifr.loc[i, 'Population'] = population.loc[ifr.loc[i, 'Age min']:ifr.loc[i, 'Age max'],'Population'].sum()
    
    ifr = np.sum(ifr['Population'] * ifr['IFR']/ifr['Population'].sum())
    return np.round(ifr, 3)  

def calc_hale():
    """
    A function that extrapolates 2019 Health Adjusted Life Expectancy (HALE) from 2007 and 2016 HALE data and Life Expectancy 2016 and 2019 data.
    """
    
    hale_2007_data = pd.read_csv(r'\HALE.csv')
    hale_2016 = {
                 'Males age 0 2016': 71.7, 
                 'Females age 0 2016': 74.1,
                 'Males age 60 2016': 18.5,
                 'Females age 60 2016': 20.5
                 }
    le = {
          'Males 2016': 80.7,
          'Females 2016': 84.2,
          'Males 2019': 81,
          'Females 2019': 84.7
          }
    """
    Sources:
       LE: 
       https://www.cbs.gov.il/he/publications/doclib/2020/3.shnatonhealth/st03_05.pdf
       HALE 2016:
       https://apps.who.int/gho/data/node.main.HALE?lang=en
       HALE 2007:
       https://www.health.gov.il/hozer/mk02_2007.pdf

    """
    
    hale_2019 = pd.DataFrame(columns = ['Age min', 'Age max', 'Males', 'Females'])
    hale_2019['Age min'] = hale_2007_data['Age min'] 
    hale_2019['Age max'] = hale_2007_data['Age max'] 
    #Prepring the DataFrame.
    
    hale_2019.loc[:12,'Males'] = hale_2007_data.loc[:12,'Males 2007'] * (hale_2016['Males age 0 2016']/hale_2007_data.loc[0 ,'Males 2007'])
    hale_2019.loc[13:,'Males'] = hale_2007_data.loc[13:,'Males 2007'] * (hale_2016['Males age 60 2016']/hale_2007_data.loc[13 ,'Males 2007'])
    hale_2019.loc[:12,'Females'] = hale_2007_data.loc[:12,'Females 2007'] * (hale_2016['Females age 0 2016']/hale_2007_data.loc[0 ,'Females 2007'])
    hale_2019.loc[13:,'Females'] = hale_2007_data.loc[13:,'Females 2007'] * (hale_2016['Females age 60 2016']/hale_2007_data.loc[13 ,'Females 2007'])
    #Extrapotaling from 2007 to 2016.
    
    hale_2019['Males'] *= le['Males 2019']/le['Males 2016']
    hale_2019['Females'] *= le['Females 2019']/le['Females 2016']
    #Extrapotaling from 2016 to 2019.
   
    return hale_2019
    
def calc_hospitalized():
    """
    A function that extrapolates the number of patients in internal medicine ward by age and gender from 2015 to 2020. 
    """   
    
    discharges = [1297233,
                  1299606,
                  1307854,
                  1330331]
    """
    Source:
        https://stats.oecd.org/index.aspx?queryid=30163
    """
    
    l = [0, 0, 0]
    i = 0
    while i < len(discharges)-1:
        l[i] = discharges[i+1]/discharges[i]
        i += 1
    
    growth_factor = geo_mean(l)
    #The Growth factor equals to the geometric mean of 2015-2018 growth rate in discharges from curative care, according to the OECD.
    
    hos = pd.read_csv(r'\Hospitalized 2015 (Thousands).csv')
    hos_2020 = pd.DataFrame(columns = ['Age min', 'Age max', 'Males', 'Females', 'Deaths Males', 'Deaths Females'])
    hos_2020['Age min'] = hos['Age min']
    hos_2020['Age max'] = hos['Age max']
    hos_2020['Deaths Males'] = hos['Deaths Males']
    hos_2020['Deaths Females'] = hos['Deaths Females']
    #Copying the relevant data to the new DataFrame.
    
    hos_2020['Males'] = hos['Male'] * growth_factor**5 * 1000
    hos_2020['Females'] = hos['Female'] * growth_factor**5 * 1000
    #Extrapolating from 2015 to 2020 by multiplying the 2015 values by the growth factor 5 times.   
        
    return hos_2020

def calc_hospitalized_qaly(hos, hale, co_morbidity_factor = 1):
    """
    A function that calculates the total Quality Adjusted Life Years (QALY) lost of hospitalized persons in a year.
    """
    
    hos.loc[0, 'Males QALY'] = hale.loc[4:9,'Males'].mean()
    hos.loc[0, 'Females QALY'] = hale.loc[4:9,'Females'].mean()
    hos.loc[5, 'Males QALY'] = hale.loc[18,'Males']
    hos.loc[5, 'Females QALY'] = hale.loc[18,'Females']
    i = 10
    c = 1
    while i < 18:
        hos.loc[c, 'Males QALY'] = hale.loc[i:i+1,'Males'].mean()
        hos.loc[c, 'Females QALY'] = hale.loc[i:i+1,'Females'].mean()
        i += 2
        c += 1
    #Calculating the HALE remaining for each age group of hospitalized persons.    
    
    males_total = hos['Males'] * hos['Males QALY'] * hos['Deaths Males']
    females_total = hos['Females'] * hos['Females QALY'] * hos["Deaths Females"]
    return np.sum(males_total + females_total) * co_morbidity_factor
    
def calc_corona_qaly(co_morbidity_factor = 1):
    """
    A function that calculates the average Quality Adjusted Life Years (QALY) lost of a COVID 19 death.
    """
    
    deaths = pd.read_csv(r'\Corona Deaths.csv')
    corona_hale = calc_hale() 
    #Reading the deaths report and calculating Health Adjusted Life Expectancy (HALE) to use later. 
    
    for i in deaths.index:
        if deaths.loc[i,'Gender'] == 'Female':
           a = corona_hale[(deaths.loc[i, 'Age'] >= corona_hale['Age min'] ) & (deaths.loc[i, 'Age'] <= corona_hale['Age max'])]['Females']
           deaths.loc[i,'QALY lost'] = a.iloc[0]
        if deaths.loc[i,'Gender'] == 'Male':
           a = corona_hale[(deaths.loc[i, 'Age'] >= corona_hale['Age min'] ) & (deaths.loc[i, 'Age'] <= corona_hale['Age max'])]['Males']
           deaths.loc[i,'QALY lost'] = a.iloc[0]
    """
    Looping through the deaths and calculating for each death report the Quality Adjusted Life Years (QALY) lost 
    according to the age of the reported death and according to the remaining Health Adjusted Life Expectancy (HALE) the dead potentialy had.
    """
      
    return deaths['QALY lost'].mean() * co_morbidity_factor    

def calc_dead(pop, ifr, hit):
    """
    A stupid function that calculates the number of victims due to COVID 19 infection.
    """
    
    return np.sum(pop) * ifr * hit

def main(ifr_scenario = 0, qaly_value_multiplier = 3, herd_immunity_threshold = 0.5,
         old_defence_factor = 0.75, old_defence_low = 65, old_defence_high = 120, corona_co_mo_fa = 0.7,
         hospitalized_co_mo_fa = 0.7, healthcare_collapse_factor = 0.4, lockdown_prevention_factor = 0.7):
    """
    The bloody main function.
    
    ifr_scenario is the main parameter which controls the ifr chosen from the different research papers. 
    Currently 3 values: 0 (default), 1 and 2.
    
    qaly_value_multiplier is the multiplier which the code use to calculate the monetary value of a single QALY,
    in NIS, which is 3 times the Israeli GDP per capita by default.
    
    herd_immunity_threshold Is the herd immunity threshold factor. 
    0.5 means that to reach a herd immunity in a given population, 50% of the population needs to be infected.
    
    old_defence_factor, old_defence_low and old_defence_high are three parameters that simulates the spread of the SARS-COV-2 virus in the older population.  
    The factor parameter controls the percentage of the old population that get infected, for instance, 0.75 means that 75% of the old population gets infected.
    The low and high parameters control how old the old population is, for example between 65 and 120 by default.
    
    corona_co_mo_fa is a arameter representing the background diseases of COVID-19 victims.
    0.7 means that a COVID 19 victim hasjust a 70% Health Adjusted Life Expectancy (HALE) compare to an average person in the Israeli population.
    
    hospitalized_co_mo_fa is a parameter representing the background diseases of hospitaliztion in internal medicine ward victims.
    0.7 means that such a victim has just a 70% Health Adjusted Life Expectancy (HALE) compare to an average person in the Israeli population.
    
    healthcare_collapse_factor is a parameter representing the collapse of the healthcare system caused by COVID 19. 
    0.4 means a 40% increase in the yearly deathtoll of internal medicine ward patients.
    
    lockdown_prevention_factor is a parameter representing the ability of a lockdown to prevent death until a vaccine will be developed. 
    0.7 means that a lockdown prevents 70% of the deaths during the infection period.
    """
    
    df_population = pd.read_csv(r'\Israel Population 2018.csv', thousands = ',', index_col = 'Age')
    """
    Source:
    https://www.cbs.gov.il/he/publications/LochutTlushim/2020/%D7%90%D7%95%D7%9B%D7%9C%D7%95%D7%A1%D7%99%D7%99%D7%942019-2011.xlsx
        Note: Ages 91-95+ are extrapolated from the 90+ data. 
    """

    gdp_per_capita = 155666
    """
    Source:
        https://www.cbs.gov.il/he/publications/doclib/2020
        /macro_q202001/t01_07.pdf
    """
    
    qaly_value =  gdp_per_capita * qaly_value_multiplier
    
    papers = ['ODriscoll', 'Verity', 'Levin']
    df_ifr = pd.read_csv(r'\IFR ' + papers[ifr_scenario] + ' et al.csv')
    ifr = calc_ifr(df_ifr, df_population, old_defence_low = old_defence_low, old_defence_high = old_defence_high, old_defence_factor = old_defence_factor)/100
    #Calculating Age Adjusted Infected Fatality Rate according to Levin et al, Verity et al and O'Driscoll et al.
    
    dead = calc_dead(df_population["Population"], ifr, herd_immunity_threshold) * lockdown_prevention_factor
    #Calculating COVID 19 casualties.
    
    qaly_lost_covid = calc_corona_qaly(co_morbidity_factor = corona_co_mo_fa) * dead
    #Calculating QALY lost due COVID 19 Deaths.
    
    qaly_lost_hospitalized = calc_hospitalized_qaly(calc_hospitalized(), calc_hale(), hospitalized_co_mo_fa) * healthcare_collapse_factor
    #Calculating QALY lost due to healthcare system collapse.
    
    qaly_value_lost = int(np.round((qaly_lost_covid + qaly_lost_hospitalized) * qaly_value,0))
    #Calculating the value of lost QALY due COVID 19 deaths and healthcare system collapse
    
    print(f"{qaly_value_lost:,}" + " NIS")

if __name__ == '__main__':
    main()
