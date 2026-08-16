from openpyxl import load_workbook

from app.exporter import create_excel


def test_english_export_uses_english_labels_and_values(tmp_path):
    output = tmp_path / 'iqama.xlsx'
    create_excel(
        {
            'name': 'MOHAMMAD SALEEM MOHAMMAD NASEEM',
            'iqama_number': '2572312086',
            'nationality': 'India',
            'nationality_ar': 'الهند',
            'dob': '1988/08/08',
            'doe': '2026/10/06',
            'raw_text': 'internal OCR',
        },
        str(output),
        language='en',
    )

    rows = list(load_workbook(output).active.iter_rows(values_only=True))
    assert rows == [
        ('Field', 'Value'),
        ('Name', 'MOHAMMAD SALEEM MOHAMMAD NASEEM'),
        ('Iqama Number', '2572312086'),
        ('Nationality', 'India'),
        ('Date of Birth', '1988/08/08'),
        ('Date of Expiry', '2026/10/06'),
    ]