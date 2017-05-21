import unittest

import plandf

class BasicTest(unittest.TestCase):
    def test_hello_world(self):
        p = plandf.Plan()
        p.steps([
                {'input': 'time: 1; carrots: 2; cucumbers: 3',
                'output': 'liters of juice: 0.5; waste material grams: 20'}
        ])
        self.assertEqual(p.info.df['input']['time'][0],
                         {'f_price': '',
                           'f_units': '',
                           'max_price': '',
                           'max_units': '1',
                           'min_price': '',
                           'min_units': '1',
                           'price_unit': ''})

if __name__ == '__main__':
    unittest.main()
