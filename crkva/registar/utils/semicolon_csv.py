import csv

import tablib
from django.core.exceptions import ValidationError
from import_export.formats import base_formats


class SCSV(base_formats.CSV):
    def get_title(self):
        return "scsv"

    def create_dataset(self, in_stream, **kwargs):
        delimiter = csv.Sniffer().sniff(in_stream, delimiters=";,").delimiter
        if delimiter != ";":
            raise ValidationError(
                f"CSV format is using `{delimiter}` delimiter,"
                + " but it should be `;` delimiter"
            )
        kwargs["delimiter"] = delimiter
        kwargs["format"] = "csv"
        return tablib.import_set(in_stream, **kwargs)
