import fred
import requests
import json
import pandas

# local app
from . import settings

class Rates(object):
    def __init__(self, OXE_API=False, FRED_API=False):
        self.df = self.ratesdf()
        if OXE_API:
            settings.OPENEXCHANGE_APP_ID = OXE_API
        if FRED_API:
            settings.FRED_KEY = FRED_API
        self.rebase()
        
    def get_hour_value(self):
        fred.key(settings.FRED_KEY)
        last_observation = fred.observations(
			settings.FRED_SERIES)['observations'][-1]
        h = last_observation['value']
        try:
            return float(h)
        except:
            return settings.DEFAULT_HOUR_VALUE_IN_USD

    def get_currency_rates(self):
        r = requests.get("%s?app_id=%s&base=%s" % (settings.OPENEXCHANGE_URL,
                                                   settings.OPENEXCHANGE_APP_ID,
                                                   settings.OPENEXCHANGE_BASE_CURRENCY))
        return json.loads(r.content)

    def ratesdf(self,base='h'):
        self.currency_rates = self.get_currency_rates()
        df = pandas.DataFrame.from_records([self.currency_rates['rates']])
        df.columns = [col.lower() for col in df.columns]
        return df
    
    def rebase(self,base='h'):
        self.hour_value = self.get_hour_value()
        # We express everything interms of hours
        self.df = self.df*self.hour_value
        self.df['h'] = 1.
