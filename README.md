# James Beard Awards data
[A CSV file](james-beard-awards.csv) with data on James Beard Awards winners, nominees and finalists from 1991 to present -- [everything from the search page](https://www.jamesbeard.org/awards/search), [minus a few duplicates, plus some missing data](#Data-fixes) -- and [the Python scraper](scrape.py) that builds it.

### Field layouts
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

### Data fixes
The scraped data includes some incomplete and duplicate records. Most frequently, the `recipient_name` was missing from the HTML, though as it turns out, if you do a little research to figure out the awardee's name, searching that name on the James Beard website returns the (incomplete) record, which then allows you to match it up to its unique `recipient_id`.

At any rate, see [`fixes.json`](fixes.json) for:
- `.fixes`: An object with data updates (and sources) keyed to `recipient_id`
- `.duplicates`: An object that keys the `recipient_id` of a duplicate record to discard (typically missing the `recipient_name`) to the `recipient_id` of the original record

Records are also deduplicated on the basis of all fields except `recipient_id`.