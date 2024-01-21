import os
from datetime import date
from urllib.parse import urlparse, parse_qs
import time
import random
import glob
import json
import csv

import requests
from bs4 import BeautifulSoup
import pandas as pd


URL = 'https://www.jamesbeard.org/awards/search'
REQ_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'  # noqa
}

HTML_DIR = 'search-results'

FILEPATH_CSV = 'james-beard-awards.csv'

CSV_HEADERS = [
    'year',
    'recipient_id',
    'recipient_name',
    'category',
    'subcategory',
    'award_status',
    'location',
    'restaurant_name',
    'company',
    'project',
    'publisher',
    'book_title',
    'publication',
    'show'
]

THIS_YEAR = date.today().year


def get_years():
    r = requests.get(
        URL,
        headers=REQ_HEADERS
    )
    r.raise_for_status()
    time.sleep(random.uniform(0.5, 1.5))

    soup = BeautifulSoup(r.text, 'html.parser')
    year_select = soup.find('select', {'name': 'year'})
    years = [int(x.get('value')) for x in year_select.find_all('option') if x.get('value')]  # noqa

    return years


def download_search_results(year):

    params = {
        'year': year
    }

    r = requests.get(
        URL,
        headers=REQ_HEADERS,
        params=params
    )

    r.raise_for_status()

    if 'no results found' in r.text.lower():
        return

    time.sleep(random.uniform(0.5, 1.5))

    soup = BeautifulSoup(r.text, 'html.parser')

    pagination = soup.find_all(
        'li',
        {'class': 'page-item'}
    )

    page_numbers = []

    for li in pagination:
        link = li.find('a')

        if link:
            parsed_url = urlparse(link.get('href'))
            page_num = parse_qs(parsed_url.query).get('page')[0]
            page_numbers.append(int(page_num))

    last_page = max(page_numbers)

    for page in range(1, last_page+1):
        filename = f'{year}-results-{page}.html'
        filepath = os.path.join(
            HTML_DIR,
            filename
        )

        if os.path.exists(filepath) and year != THIS_YEAR:
            continue

        params = {
            'year': year,
            'page': page
        }

        r = requests.get(
            URL,
            headers=REQ_HEADERS,
            params=params
        )

        r.raise_for_status()

        if 'no results found' in r.text.lower():
            continue

        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(r.text)

        print(f'Downloaded {filepath}')

        time.sleep(random.uniform(0.5, 1.5))

    return year


def parse_html_files():

    # load up a lookup dict for fixes
    with open('fixes.json', 'r') as infile:
        fixes = json.load(infile)

    updates = fixes.get('fixes')
    dupes = list(fixes.get('duplicates').keys())

    data = []

    html_files = glob.glob(f'{HTML_DIR}/*.html')

    for html_file in html_files:
        year = int(html_file.split('/')[-1].split('-')[0])

        with open(html_file, 'r') as infile:
            html = infile.read()

            soup = BeautifulSoup(html, 'html.parser')

            results = soup.find(
                'div',
                {'class': 'c-results'}
            ).find_all(
                'div',
                {'class': 'c-award-recipient'}
            )

            for res in results:

                award_data = {}

                # the data returned for each entry is
                # determined by its template
                tmpl = res.get('data-award-template')

                # unique identifier for award recipients
                recipient_id = int(res.get('data-award-recipient-id'))

                # skip duplicates
                if str(recipient_id) in dupes:
                    continue

                # each entry is a pile of grafs
                grafs = res.find_all('p')
                values = [' '.join(x.text.split()) for x in grafs]

                if 'journalism.person' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        title,
                        publication,
                        category,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': category,
                        'subcategory': subcategory,
                        'publication': publication,
                        'award_status': award_status,
                        'year': year
                    }

                if 'journalism.publication' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        category,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': category,
                        'subcategory': subcategory,
                        'award_status': award_status,
                        'year': year
                    }

                if 'broadcast-media' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        show_name,
                        _,
                        company_name,
                        category,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': category,
                        'subcategory': subcategory,
                        'show': show_name,
                        'company': company_name,
                        'award_status': award_status,
                        'year': year
                    }

                if 'book' in tmpl:

                    if len(values) == 8:
                        (
                            name,
                            _,
                            subcategory,
                            book_title,
                            publisher,
                            category,
                            award_status,
                            yeartext
                        ) = values

                    # they left off the publisher for
                    # "Cookbook Hall of Fame" entries
                    elif len(values) == 7:
                        (
                            name,
                            _,
                            subcategory,
                            book_title,
                            category,
                            award_status,
                            yeartext
                        ) = values

                        publisher = ''

                    publisher = publisher.lstrip('()').rstrip(')')

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': category,
                        'subcategory': subcategory,
                        'book_title': book_title,
                        'publisher': publisher,
                        'award_status': award_status,
                        'year': year
                    }

                if 'leadership' in tmpl:

                    (
                        name,
                        _,
                        _,
                        project_name,
                        _,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Leadership',
                        'project': project_name,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.lifetime-achievement' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        restaurant_name,
                        location,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'restaurant_name': restaurant_name,
                        'location': location,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.humanitarian' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.americas-classics' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        location,
                        category,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'location': location,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.design' in tmpl:

                    if len(values) == 8:
                        (
                            name,
                            _,
                            subcategory,
                            restaurant_name,
                            location,
                            category,
                            award_status,
                            yeartext
                        ) = values

                    # "design icon" awards don't have
                    # restaurant names
                    elif len(values) == 7:
                        (
                            name,
                            _,
                            subcategory,
                            location,
                            category,
                            award_status,
                            yeartext
                        ) = values

                        restaurant_name = None

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'restaurant_name': restaurant_name,
                        'location': location,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.restaurant' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        location,
                        category,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'location': location,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.person' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        restaurant_name,
                        location,
                        category,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'restaurant_name': restaurant_name,
                        'location': location,
                        'award_status': award_status,
                        'year': year
                    }

                if 'rnc.whos-who' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        location,
                        award_status,
                        yeartext
                    ) = values

                    award_data = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'category': 'Restaurant & Chef',
                        'subcategory': subcategory,
                        'location': location,
                        'award_status': award_status,
                        'year': year
                    }

                if award_data:
                    data_fixes = updates.get(str(recipient_id))

                    if data_fixes:
                        award_data = {
                            **award_data,
                            **data_fixes.get('updates')
                        }

                    if not award_data.get('recipient_name'):
                        raise Exception(f'Entry No. {recipient_id} is missing a `recipient_name`')  # noqa

                    data.append(award_data)

    df = pd.DataFrame(data)

    df.sort_values(
        ['year', 'category', 'subcategory', 'award_status'],
        ascending=True,
        inplace=True
    )

    df.drop_duplicates(
        subset=[x for x in df.columns if x != 'recipient_id']
    )

    df.to_csv(FILEPATH_CSV, index=False)

    print(f'Wrote {len(df):,} records to `{FILEPATH_CSV}`')

    return data


if __name__ == '__main__':

    years = get_years()

    for year in years:
        page_numbers = download_search_results(year)

    parse_html_files()
