import os

import requests


def translate_text(value: str, source: str, target: str) -> str:
    """Translate text when configured; preserve the source value on failure."""
    value = (value or '').strip()
    if not value or source == target:
        return value
    key = os.environ.get('AZURE_TRANSLATOR_KEY', '')
    if not key:
        return value
    endpoint = os.environ.get(
        'AZURE_TRANSLATOR_ENDPOINT',
        'https://api.cognitive.microsofttranslator.com',
    ).rstrip('/')
    url = f'{endpoint}/translate?api-version=3.0&from={source}&to={target}'
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-Type': 'application/json',
    }
    region = os.environ.get('AZURE_TRANSLATOR_REGION', '')
    if region:
        headers['Ocp-Apim-Subscription-Region'] = region
    try:
        response = requests.post(url, headers=headers, json=[{'text': value}], timeout=15)
        response.raise_for_status()
        return response.json()[0]['translations'][0]['text'].strip() or value
    except (OSError, KeyError, IndexError, TypeError, ValueError, requests.RequestException):
        return value


def choose_name(name_ar: str, name_en: str, language: str) -> str:
    """Choose the requested name, translating the other language if needed."""
    if language.lower().startswith('en'):
        return name_en or translate_text(name_ar, 'ar', 'en') or name_ar
    return name_ar or translate_text(name_en, 'en', 'ar') or name_en


def choose_value(value_ar: str, value_en: str, language: str) -> str:
    """Select or translate any bilingual textual field."""
    if language.lower().startswith('en'):
        return value_en or translate_text(value_ar, 'ar', 'en') or value_ar
    return value_ar or translate_text(value_en, 'en', 'ar') or value_en