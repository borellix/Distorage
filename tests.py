import os
import unittest
import requests

values = {
    'common_file_key': '',
    'custom_file_key': '',
}


class TestCommon(unittest.TestCase):
    url = "http://localhost:5000/files/"

    def test_1_common_upload(self):
        file = open("tests_upload_files/test.py", "rb")
        r = requests.post(
            self.url,
            files={
                "file": file
            }
        )
        file.close()
        values['common_file_key'] = r.json()["file_key"]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.json().keys()), ['file_key'])

    def test_2_common_download(self):
        url = self.url + values['common_file_key']
        r = requests.get(
            url
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.json().keys()), ['url'])
        self.assertEqual(r.json()['url'].split('/')[4], values['common_file_key'].split(':')[0])

    def test_3_common_edit(self):
        url = self.url + values['common_file_key']
        file = open("tests_upload_files/test2.py", "rb")
        r = requests.patch(
            url,
            files={
                "file": file
            }
        )
        file.close()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.json().keys()), ['file_key'])

    def test_4_common_delete(self):
        url = self.url + values['common_file_key']
        r = requests.delete(
            url
        )
        self.assertEqual(r.status_code, 200)
        self.assertDictEqual(r.json(), {'message': 'DELETED'})


class TestCustom(unittest.TestCase):
    url = "http://localhost:5000/files/"
    authorization = os.getenv('TEST_AUTHORIZATION_CUSTOM')
    guilds_ids = os.getenv('TEST_GUILDS_IDS_CUSTOM')

    def test_5_custom_upload(self):
        file = open("tests_upload_files/test.py", "rb")
        r = requests.post(
            self.url,
            headers={
                "Authorization": self.authorization
            },
            data={
                "guilds_ids": self.guilds_ids,
                "category": "HOSTING",
                "prefix": "host-"
            },
            files={
                "file": file
            }
        )
        file.close()
        values['custom_file_key'] = r.json()["file_key"]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.json().keys()), ['file_key'])

    def test_6_custom_download(self):
        url = self.url + values['custom_file_key']
        r = requests.get(
            url,
            headers={
                "Authorization": self.authorization
            }
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.json().keys()), ['url'])
        self.assertEqual(r.json()['url'].split('/')[4], values['custom_file_key'].split(':')[0])

    def test_7_custom_edit(self):
        url = self.url + values['custom_file_key']
        file = open("tests_upload_files/test2.py", "rb")
        r = requests.patch(
            url,
            headers={
                "Authorization": self.authorization
            },
            files={
                "file": file
            }
        )
        file.close()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.json().keys()), ['file_key'])

    def test_8_custom_delete(self):
        url = self.url + values['custom_file_key']
        r = requests.delete(
            url,
            headers={
                "Authorization": self.authorization
            }
        )
        self.assertEqual(r.status_code, 200)
        self.assertDictEqual(r.json(), {'message': 'DELETED'})


if __name__ == '__main__':
    from pytest_dotenv.plugin import load_dotenv
    load_dotenv()
    unittest.main()
