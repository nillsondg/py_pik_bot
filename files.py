from datetime import date
from config import UID as USERNAME, PWD, FILE_SERVER_TOKEN as TOKEN
from states import Source

URL = "http://tgbot01pik/PicGroupExcelReportService/GetExcelFile.ashx?token=" + TOKEN + "&repName=pf.xlsx&" \
      "Parameter 1={first_date_of_month}&Parameter 2={current_date}&Parameter 3={source}&Format=pdf"


def get_company_num(state):
    if state.source == Source.pik:
        return 0
    elif state.source == Source.morton:
        return 1
    else:
        raise RuntimeError("this source not supported")


def construct_url(state):
    company_num = get_company_num(state)
    current_date = date.today().strftime("%Y-%m-%d")
    first_date_of_month = date(date.today().year, date.today().month, 1).strftime("%Y-%m-%d")
    return URL.format(first_date_of_month=first_date_of_month, current_date=current_date, source=company_num)


def download_file(state):
    from requests import get  # to make GET request

    from requests_ntlm import HttpNtlmAuth

    def download(url, file_name):
        # open in binary mode
        with open(file_name, "wb") as file:
            # get request
            response = get(url, auth=HttpNtlmAuth('main\\' + USERNAME, PWD))
            # write to file
            file.write(response.content)

    download(construct_url(state), "test.pdf")
