import os
from urllib.parse import urlparse, parse_qs
import time
import random
import glob
import json

import requests
from bs4 import BeautifulSoup


URL = 'https://www.jamesbeard.org/awards/search'
JSON_FILEPATH = 'james-beard-awards.json'
HTML_DIR = 'search-results'


def get_years():
    r = requests.get(URL)
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

        if os.path.exists(filepath):
            continue

        params = {
            'year': year,
            'page': page
        }

        r = requests.get(
            URL,
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

    data = {}

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

                # the data returned for each entry is
                # determined by its template
                tmpl = res.get('data-award-template')

                # unique identifier for award recipients
                recipient_id = int(res.get('data-award-recipient-id'))

                # each entry is a pile of grafs
                grafs = res.find_all('p')
                values = [' '.join(x.text.split()) for x in grafs]

                data_out = {}
                category = None

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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'publication': publication,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'journalism.person'
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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'journalism.publication'
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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'show': show_name,
                        'company': company_name,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'broadcast-media'
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

                        publisher = None

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'book_title': book_title,
                        'publisher': publisher,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'book'
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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'project': project_name,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'leadership'
                    }

                    category = 'Leadership'

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

                    category = 'Restaurant & Chef'

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'restaurant': restaurant_name,
                        'location': location,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.lifetime-achievement'
                    }

                if 'rnc.humanitarian' in tmpl:

                    (
                        name,
                        _,
                        subcategory,
                        award_status,
                        yeartext
                    ) = values

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.humanitarian'
                    }

                    category = 'Restaurant & Chef'

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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'location': location,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.americas-classics'
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

                    data_out = {
                        'recipient_name': name,
                        'recipient_id': recipient_id,
                        'subcategory': subcategory,
                        'restaurant_name': restaurant_name,
                        'location': location,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.design'
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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'location': location,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.restaurant'
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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'restaurant_name': restaurant_name,
                        'location': location,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.person'
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

                    data_out = {
                        'recipient_id': recipient_id,
                        'recipient_name': name,
                        'subcategory': subcategory,
                        'location': location,
                        'award_status': award_status,
                        'year': year,
                        'record_template': 'rnc.whos-who'
                    }

                    category = 'Restaurant & Chef'

                assert(int(yeartext) == year)

                if data_out:
                    if category not in data:
                        data[category] = []
                    data[category].append(data_out)

    return data


if __name__ == '__main__':

    years = get_years()

    for year in years:
        page_numbers = download_search_results(year)

    data = parse_html_files()

    with open(JSON_FILEPATH, 'w') as outfile:
        json.dump(
            data,
            outfile,
            sort_keys=True
        )

    print(f'Wrote file: {JSON_FILEPATH}')
