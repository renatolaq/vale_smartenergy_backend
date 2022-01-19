from django.test import TestCase
from manual_import.models import Ksb1, Fbl34N, UploadFile

# ------------------------------------------------------------------------
# To run
# python manage.py test manula_import -k
# ------------------------------------------------------------------------


class ManualImportTests(TestCase):

    def test_valid_fbl34n_model(self):
        """"Test valid model of FBL34N required fields """
        _id = 1
        fbl = Fbl34N(id_fbl34n=_id)
        self.assertEqual(Fbl34N(id_fbl34n=_id).id_import_source, fbl.id_import_source)
        self.assertEqual(Fbl34N(id_fbl34n=_id).company, fbl.company)
        self.assertEqual(Fbl34N(id_fbl34n=_id).release_date, fbl.release_date)
        self.assertEqual(Fbl34N(id_fbl34n=_id).internal_currency, fbl.internal_currency)
        self.assertEqual(Fbl34N(id_fbl34n=_id).incoming_date, fbl.incoming_date)
        self.assertEqual(Fbl34N(id_fbl34n=_id).incoming_time, fbl.incoming_time)
        self.assertEqual(Fbl34N(id_fbl34n=_id).exercise, fbl.exercise)
        self.assertEqual(Fbl34N(id_fbl34n=_id).accounting_period, fbl.accounting_period)

    def test_valid_ksb1_model(self):
        """"Test valid model of KSB1 required fields """
        _id = 1
        ksb1 = Ksb1(id_ksb1=_id)
        self.assertEqual(Ksb1(id_ksb1=_id).cost_center, ksb1.cost_center)
        self.assertEqual(Ksb1(id_ksb1=_id).cost_element_description, ksb1.cost_element_description)
        self.assertEqual(Ksb1(id_ksb1=_id).incoming_date, ksb1.incoming_date)
        self.assertEqual(Ksb1(id_ksb1=_id).incoming_time, ksb1.incoming_time)
        self.assertEqual(Ksb1(id_ksb1=_id).release_date, ksb1.release_date)
        self.assertEqual(Ksb1(id_ksb1=_id).document_number, ksb1.document_number)
        self.assertEqual(Ksb1(id_ksb1=_id).time_period, ksb1.time_period)
        self.assertEqual(Ksb1(id_ksb1=_id).exercise, ksb1.exercise)
        self.assertEqual(Ksb1(id_ksb1=_id).company, ksb1.company)
        self.assertEqual(Ksb1(id_ksb1=_id).mr_value, ksb1.mr_value)


def test_valid_upload_model(self):
    """"Test valid model of FBL34N required fields """
    _id = 10002
    upload = UploadFile(id=_id)
    self.assertEqual(UploadFile(id=_id).date_upload, upload.date_upload)
    self.assertEqual(UploadFile(id=_id).file_name, upload.file_name)
    self.assertEqual(UploadFile(id=_id).file_path, upload.file_path)
    self.assertEqual(UploadFile(id=_id).file_type, upload.file_type)
