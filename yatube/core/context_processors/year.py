from datetime import datetime


def year(request):
    dt = datetime.today().year
    return {'year': dt}
