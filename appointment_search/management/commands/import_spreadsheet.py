import tempfile

import requests
import xlrd
from django.core.management.base import BaseCommand

from appointment_search import models
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports data for the appointment database'

    def add_arguments(self, parser):
        parser.add_argument('url', nargs=1, type=str)

    def handle(self, *args, **options):
        url, = options['url']
        res = requests.get(url)
        with tempfile.NamedTemporaryFile(suffix='.xlsx') as temp:
            temp.delete = True
            with open(temp.name, 'w+') as fp:
                fp.write(res.content)

            w = xlrd.open_workbook(temp.name)

        sheet = w.sheet_by_index(0)

        header = [sheet.cell_value(0, i) for i in range(0, sheet.ncols)]
        rows = [dict(zip(header, [sheet.cell_value(j, i) for i in range(0, sheet.ncols)])) for j in
                range(1, sheet.nrows)]

        sample = rows[0] if rows else None
        if sample:
            if 'registration_number' in sample and 'date' in sample:
                for r in rows:
                    appointment, created = models.AppointmentSchedule.objects.get_or_create(
                        registration_number=str(int(r['registration_number'])))

                    date = r['date']
                    if type(date) is float:
                        date = datetime(*xlrd.xldate_as_tuple(date, w.datemode))

                    asylum_office, c = models.AsylumOffice.objects.get_or_create(name=r['asylum_office'])

                    appointment.date = date
                    appointment.office = asylum_office
                    appointment.save()

                    print('Imported appointment for case number {}'.format(r['registration_number']))