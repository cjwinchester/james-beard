# James Beard Awards data
[A JSON file](james-beard-awards.json) with data on James Beard Awards winners, nominees and finalists -- [everything from the search page](https://www.jamesbeard.org/awards/search) -- and [the Python scraper](fetch.py) that created it.

Each type of award record has different fields, so the JSON file is arranged like the search page: Top-level keys are the categories (`Restaurant & Chef`, `Book`, `Broadcast Media`, `Journalism`, `Leadership`), and the array of records attached to each key can be grouped by the `record_template` key to analyze like records.
