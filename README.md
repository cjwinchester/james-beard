# James Beard Awards data
[A CSV file](james-beard-awards.csv) with data on James Beard Awards winners, nominees and finalists from 1991 to present -- [everything from the search page](https://www.jamesbeard.org/awards/search) -- and [the Python scraper](fetch.py) that builds it.

Each awards category involves slightly different data values, so each type of record populates a slightly different subset of the fields in the CSV:
- `year`
- `recipient_id`
- `recipient_name`
- `category`
- `subcategory`
- `award_status`
- `location`
- `restaurant_name`
- `company`
- `project`
- `publisher`
- `book_title`
- `publication`
- `show`
