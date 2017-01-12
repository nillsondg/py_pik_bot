import unittest
from datetime import date
from config import FILE_SERVER_TOKEN as TOKEN
from states import State
import files


class TestFiles(unittest.TestCase):
    def test_construct_url(self):
        state = State.pik_today_sold
        url = files.generate_url(state)
        current_date = date.today().strftime("%Y-%m-%d")
        first_date_of_month = date(date.today().year, date.today().month, 1).strftime("%Y-%m-%d")
        print(url)
        self.assertEqual(url,
                         "http://tgbot01pik/PicGroupExcelReportService/GetExcelFile.ashx?token={}&repName=pf.xlsx"
                         "&Parameter 1={}&Parameter 2={}&Parameter 3={}&Format=pdf".format(
                             TOKEN, first_date_of_month, current_date, 0))
