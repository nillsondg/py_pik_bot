import unittest

import files
from config import FILE_SERVER_TOKEN as TOKEN
from states import State


class TestFiles(unittest.TestCase):
    def test_construct_url(self):
        state = State.pik_today_sold
        url = files.generate_url(state)
        print(url)
        pattern = "http:\/\/qgis01pik.main.picompany.ru\/PicGroupExcelReportService/GetExcelFile\.ashx\?token=" + TOKEN + \
                  "&repName=pf\.xlsx&Parameter 1=\d{2}.\d{2}.\d{4}&Parameter 2=\d{2}.\d{2}.\d{4}" \
                  "&Parameter 3=2&Format=pdf"
        self.assertRegex(url, pattern)
