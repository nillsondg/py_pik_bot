from datetime import date
from config import UID as USERNAME, PWD, FILE_SERVER_TOKEN as TOKEN
from states import Source
from requests import get
from requests_ntlm import HttpNtlmAuth

URL_PATTERN = "http://qgis01pik.main.picompany.ru/PicGroupExcelReportService/GetExcelFile.ashx?token={token}" \
              "&repName=pf.xlsx&Parameter 1={first_date_of_month}&Parameter 2={current_date}" \
              "&Parameter 3={source}&Format=pdf"
FILE_FOLDER = "files_cache"


def get_company_name(state):
    if state.source == Source.pik:
        return "Pik"
    elif state.source == Source.morton:
        return "Morton"
    else:
        raise RuntimeError("this source not supported")


def generate_url(state):
    current_date = date.today().strftime("%d.%m.%Y")
    first_date_of_month = date(date.today().year, date.today().month, 1).strftime("%d.%m.%Y")
    return URL_PATTERN.format(token=TOKEN, first_date_of_month=first_date_of_month, current_date=current_date, source=2)


def generate_name(state):
    today = date.today()
    name_pattern = "pf{date}.pdf"
    return FILE_FOLDER + "/" + name_pattern.format(date=today.strftime("%m.%Y"))


def download(url, file_name):
    with open(file_name, "wb") as file:
        response = get(url, auth=HttpNtlmAuth('main\\' + USERNAME, PWD))
        file.write(response.content)


def download_file_and_return_name(state):
    file_name = generate_name(state)
    download(generate_url(state), file_name)
    return file_name
