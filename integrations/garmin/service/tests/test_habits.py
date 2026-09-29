import unittest
from habits import validate


class TestHabits(unittest.TestCase):
    def test_zero_false_and_explicit_clear_preserved(self):
        answers={'energy':0,'water_over_3l':False,'highlight':None}
        self.assertEqual(validate('2000-01-01',answers),answers)

    def test_rejects_invalid_fields_and_types(self):
        for answers in ({'energy':True},{'focus':11},{'energy':-1},{'energy':'5'},
                        {'water_over_3l':'não'},{'wake_time':'25:00'},
                        {'sleep_at':'2000-01-01T23:00:00'}, {'unknown':'x'},
                        {'highlight':''}, {'highlight':'x'*4001}, {}):
            with self.subTest(answers=list(answers)):
                with self.assertRaises(ValueError): validate('2000-01-01',answers)

    def test_accepts_confirmed_bedtime_after_midnight(self):
        self.assertEqual(validate('2000-01-01',{'sleep_at':'2000-01-02T00:30:00+01:00'}),
                         {'sleep_at':'2000-01-02T00:30:00+01:00'})
