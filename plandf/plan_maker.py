import pandas
from . import utils

class PlanMaker(object):

    def __init__(self, 
                 plan_tuples,
                 conversion_rates=pandas.DataFrame({'h': [1.]})):

        """
        Example of plan_tuples:

        >>> breakfast = [
             ('time: 0.003~0.004@24h; loaf of black bread: 1@0.1h; butter grams: 15@0.01h; tomato: 0.5@0.2h',
              'sandwitch: 1@0.12h'),
             ('eggs: 2~5@0.012h; scrambling actions: 50~100; time: 0.003~0.005@24h',
              'scrambled egg servings: 1@0.16h'),
             ('coffee teaspoon: 1~2@0.00012h; liters of water: 0.2~0.3@0.0001h; time: 0.003~0.005@24h',
              'cup of coffee: 1~1.5@0.08h')
        ]
        
        Note: if richer currency conversion_rates is provided, then it can be something like:

        >>> breakfast_with_currencies = [
            ('time: 0.003~0.004@24h; loaf of black bread: 1@2.22eur; butter grams: 15@0.25usd; tomato: 0.5@5usd',
             'sandwitch: 1@3usd'),
            ('eggs: 2~5@0.3usd; scrambling actions: 50~100; time: 0.003~0.005@24h',
             'scrambled egg servings: 1@4usd'),
            ('coffee teaspoon: 1~2@0.003usd; liters of water: 0.2~0.3@0.0025usd; time: 0.003~0.005@24h',
             'cup of coffee: 1~1.5@2usd')
        ]

        """
        self.df = utils.plandf(plan_tuples)
        self.df.columns.names = [None, 'Step #ID']
        if 'h' not in conversion_rates.columns:
            raise Exception("Column 'h' (hour value) must be among columns of conversion_rates. 'h' not found.")
        else:
            try:
                self.rates = conversion_rates/conversion_rates['h'].values[0]
            except:
                raise Exception("Could not normalize by hour value. Check if conversion rates are numeric.")

    def get_price_unit_values(self, default=pandas.np.nan):

        price_units = utils.subdf(self.df, 'price_unit', 'price_unit')    

        price_unit_values = price_units.applymap(
            lambda x: self.rates[x].values[0] if x in self.rates.columns
            else pandas.np.nan).apply(pandas.to_numeric,
                                      errors='coerce')

        return price_unit_values.fillna(default)

    def get_asset_values(self, case='MEAN'):

        if case=='WORST':

            units = utils.subdf(self.df,
                          input_key='max_units',
                          output_key='min_units',
                          to_numeric=True)

            prices = utils.subdf(self.df,
                           input_key='max_price',
                           output_key='min_price',
                           to_numeric=True)

        elif case=='BEST':

            units = utils.subdf(self.df,
                          input_key='min_units',
                          output_key='max_units',
                          to_numeric=True)

            prices = utils.subdf(self.df,
                           input_key='min_price',
                           output_key='max_price',
                           to_numeric=True)

        else: # ('MEAN')

            units = ( utils.subdf(self.df,
                          input_key='min_units',
                          output_key='min_units',
                          to_numeric=True) +
                      utils.subdf(self.df,
                          input_key='max_units',
                          output_key='max_units',
                          to_numeric=True) ) / 2.
			# Add known means, if 'f_units' is a number:
            known_units_means = utils.subdf(self.df, input_key='f_units',
							  output_key='f_units',to_numeric=True)
            # add dataframe with 'f_units', and fillna(.0)
            units = utils.replace_known_numeric_values(units, known_units_means)

            prices = ( utils.subdf(self.df,
                           input_key='min_price',
                           output_key='min_price',
                           to_numeric=True) +
                       utils.subdf(self.df,
                           input_key='max_price',
                           output_key='max_price',
                           to_numeric=True) ) / 2.
			# Add known means, if 'f_price' is a number:
            known_price_means = utils.subdf(self.df, input_key='f_price',
							  output_key='f_price',to_numeric=True)
            # add dataframe with 'f_units', and fillna(.0)
            prices = utils.replace_known_numeric_values(prices, known_price_means)

        return units * prices * self.get_price_unit_values()

    
    def case_value(self, case='WORST'):

        io_df = self.get_asset_values(case=case)
        
        values = utils.set_axis(io_df).fillna(0.)

        value = pandas.concat({'input': values['input'].fillna(0.).sum(axis=1),
                               'output': values['output'].fillna(0.).sum(axis=1)},
                                axis=1)



        v = value.cumsum()

        return (v['output']-v['input'])
    
    
    def get_scenarios(self):
        return pandas.concat([self.case_value('WORST'),
                             self.case_value('MEAN'),
                             self.case_value('BEST')],
                             axis=1,
                             keys=['worst', 'mean','best']
        )
