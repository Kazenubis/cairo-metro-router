# Cairo Metro Router

A command-line tool that finds the best route between two Cairo Metro stations, including where to change lines, which direction to ride and roughly what the ticket costs.

## Why I built this

I live in Cairo and use the metro a lot. What I actually need to know is where to change lines and whether a change is worth it, because changing at Sadat or Attaba at rush hour takes real time. So I built a router that counts a transfer as a cost you can set yourself, rather than treating it as free.

## Features

- Shortest route across Lines 1, 2 and 3, with interchanges at Sadat, Al-Shohadaa, Nasser, Attaba, Kit Kat and Cairo University
- Output grouped by line, with the direction to ride ("towards New El-Marg"), stops per leg, total transfers and fare
- Configurable transfer penalty (`--transfer-penalty`, default 3 stops per change)
- Forgiving station names: case-insensitive, ignores punctuation and "El-"/"Al-", knows a few common aliases (Tahrir, Ramses, Zamalek, ...) and suggests close matches when you make a typo
- `stations` command to list a line with its interchanges marked
- Network and fares live in editable JSON files, and only the Python standard library is used

### About the data

`data/stations.json` is the network **as I knew it** when I wrote this. It is not an official map and may be out of date: new stations open, names get respelled. It's plain JSON, so edit it if something is wrong or missing.

The Line 3 branch to Cairo University is a simplification. I modelled it as its own line, `3B` (Kit Kat to Cairo University), so a trip that goes from the main Line 3 onto the branch counts as a change at Kit Kat. If that doesn't match how the trains run when you ride, edit the JSON.

`data/fares.json` holds **sample** fare tiers (up to 9 stations, up to 16, up to 23, more). They are not official prices. Edit them to match current ticket prices before relying on the fare shown.

## Run it

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m metro_router route "Helwan" "Attaba"
```

Other commands:

```bat
python -m metro_router stations --line 2
python -m metro_router route "Giza" "Zamalek" --transfer-penalty 0
python -m metro_router route "Dokki" "Heliopolis" --show-stations
```

Example output:

```text
> python -m metro_router route "Helwan" "Attaba"
Helwan  ->  Attaba
==================

  [Line 1] Helwan -> Nasser
           towards New El-Marg, 19 stops

  ~ change at Nasser ~

  [Line 3] Nasser -> Attaba
           towards Adly Mansour, 1 stop

------------------
Stops: 20   Transfers: 1   Fare: 15 EGP
```

With the transfer penalty set to 0, the router only counts stops, so it will change lines more often:

```text
> python -m metro_router route "Giza" "Zamalek" --transfer-penalty 0
Giza  ->  Safaa Hegazy
======================

  [Line 2] Giza -> Cairo University
           towards Shubra El-Kheima, 2 stops

  ~ change at Cairo University ~

  [Line 3B] Cairo University -> Kit Kat
            towards Kit Kat, 5 stops

  ~ change at Kit Kat ~

  [Line 3] Kit Kat -> Safaa Hegazy
           towards Adly Mansour, 1 stop

----------------------
Stops: 8   Transfers: 2   Fare: 8 EGP
```

(With the default penalty of 3, the same trip goes Giza to Attaba on Line 2 and then Line 3: 11 stops, 1 transfer.)

Typos get suggestions:

```text
> python -m metro_router route "helwn" "attaba"
error: Unknown station 'helwn'. Did you mean: Helwan, Ain Helwan?
```

## Run the tests

```bat
python -m pytest -q
```

## Project structure

```text
cairo-metro-router/
├── data/
│   ├── fares.json        sample fare tiers
│   └── stations.json     lines, stations and aliases
├── metro_router/
│   ├── __main__.py       python -m metro_router
│   ├── cli.py            argparse sub-commands
│   ├── fares.py          fare tiers
│   ├── formatting.py     plain-text output
│   ├── matching.py       name normalisation + difflib suggestions
│   ├── network.py        loading and validating the JSON
│   └── router.py         graph building and Dijkstra
├── tests/
├── pyproject.toml        pytest settings
├── requirements.txt
└── LICENSE
```

## What I practiced

- Modelling a transit map as a graph of `(station, line)` nodes, so that a change of line is just another edge with a cost
- Dijkstra with a transfer penalty, written by hand with `heapq`, breaking ties on fewer transfers
- Fuzzy string matching with normalisation and `difflib.get_close_matches`
- Validating JSON data files and turning them into frozen dataclasses
- Keeping the logic separate from the CLI so it can be tested on a tiny made-up network
