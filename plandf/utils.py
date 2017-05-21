from datetime import timedelta
from . import settings
import pandas
import copy

# local app?
import stepio

"""Make one DataFrame from a list of StepIO items."""
make_df = lambda l: pandas.DataFrame.from_records([
        pandas.Series(data=[x[list(x.keys())[0]] for x in stepio.parse(s)],
                      index=zip(*stepio.parse(s))[0])
        for s in l])
"""
Examples:

>>> make_df(
    ['sandwitch: 1@0.12h',
    'scrambled egg servings: 1@0.16h',
    'cup of coffee: 1~1.5@0.08h'])
>>>
    cup of coffee    sandwitch     scrambled egg servings
  0     NaN       {u'max_units': u'1', u'min_units': u'1'
  1     NaN             NaN        {u'max_units': u'1', u
  2  {u'max_units': u'1.5', u'min_units': u'1', u'p...	N

"""

def plandf(plan_tuples):
    """
    Makes two tables with groups of columns ['input', 'output']
    """
    i, o = list(zip(*plan_tuples))
    return pandas.concat({'input': make_df(i), 
                          'output': make_df(o)},
                           axis=1)

"""
Example:

>>> breakfast = [
 ('time: 0.003~0.004@24h; loaf of black bread: 1@0.1h; butter grams: 15@0.01h; tomato: 0.5@0.2h',
      'sandwitch: 1@0.12h'),
 ('eggs: 2~5@0.012h; scrambling actions: 50~100; time: 0.003~0.005@24h',
      'scrambled egg servings: 1@0.16h'),
 ('coffee teaspoon: 1~2@0.00012h; liters of water: 0.2~0.3@0.0001h; time: 0.003~0.005@24h',
      'cup of coffee: 1~1.5@0.08h')
  ]

>>> plandf(breakfast)
"""

def subdf(df, input_key='max_price', output_key='min_price', to_numeric=False):
    """
    Extracts a sub-DataFrame by a chosen key for different 'input' and 'output' group.
    
    Note: to_numeric must be False, because we have units like 'h', 'usd', etc.
    """
    io_df = pandas.concat({'input':
        df['input'].applymap(
            lambda x: x[input_key] if type(x) == dict else pandas.np.nan
        ),
               'output':
        df['output'].applymap(
            lambda x: x[output_key] if type(x) == dict else pandas.np.nan
        )
        },
        axis=1
    )
    if to_numeric:
        return io_df.apply(pandas.to_numeric, errors='coerce')
    else:
        return io_df

"""
Examples:

>>> subdf(
    plandf(breakfast), 'min_units', 'price_unit'
)

>>> subdf(
    plandf(breakfast), 'min_units', 'max_units'
)
"""

def set_axis(io_df,
            axis='time',
            convert_time=False,
            start_time=pandas.datetime.now(),
            time_unit=lambda x: timedelta(hours=x)):
    """
    Sets a chosen column from 'input' column group, and makes it DataFrame index.
    
    Optionally, converts index to DateTime by a chosen unit.
    """

    # add empty row to represent start from zero
    io_df.ix[-1] = 0.
    io_df.sort_index(inplace=True)
    
    ix = pandas.to_numeric(io_df['input'][axis].interpolate(), 
                              errors='coerce').cumsum()
    
    indexed_df = pandas.concat({'input': io_df['input'].set_index(ix),
                               'output': io_df['output'].set_index(ix)},
        axis=1
    )

    if convert_time:
        timeindex = indexed_df.index.map(
            lambda x: start_time+time_unit(x)
        )
        indexed_df.index = timeindex

    indexed_df.drop([('input', axis)], axis=1, inplace=True)

    return indexed_df


"""
Examples:

>>> set_axis(
    subdf(
        plandf(breakfast), 'min_units', 'max_units'
    )
)

>>> set_axis(
    subdf(
        plandf(breakfast), 'min_units', 'max_units'
    ),
    convert_time=True,
)

>>> set_axis(
    subdf(
        plandf(breakfast), 'min_units', 'max_units'
    ),
    axis='eggs'
)

>>> set_axis(
    subdf(
        plandf(breakfast), 'min_units', 'max_units'
    ),
    axis='time',
    convert_time=True,
    time_unit=lambda x: timedelta(days=365.25*x),
    start_time=pandas.datetime(1995,1,1)
)
"""

def humanize(df, 
             hour_value=settings.DEFAULT_HOUR_VALUE_IN_USD,
             start_time=timedelta(0.),
             time=lambda x: timedelta(hours=x)):
    """
    Display value in some currency, and time in days.
    """
    dx = copy.deepcopy(df)
    dx.index = df.index.map(time)
    return (dx*hour_value)


"""Add _numeric_ values from one dataframe to another, d2 is priority.

Note: works only on numeric. Safely call like:

replace_known_numeric_values(df1.apply(pandas.to_numeric, errors='coerce'),
                             df2.apply(pandas.to_numeric, errors='coerce'))

"""
replace_known_numeric_values = lambda df1, df2: df1[df2.isnull()].fillna(0.) + \
                                      df2[~df2.isnull()].fillna(0.) + \
                                      (df1.isnull().applymap(lambda x: pandas.np.nan if x else 0.))
