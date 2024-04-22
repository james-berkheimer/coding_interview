# Project: MET Query (a coding exercise)

## Description

A program to query the MET collection using it's REST API.

## Installation

First, you need to create a virtual environment. Then go to the project directory and do a pip editable install:

```bash
python3 -m venv env
source env/bin/activate

cd path/to/coding_interview
pip install -e .
```

## CLI Options

| Option        | Description           | Default Value  |
| ------------- |:-------------:| -----:|
| --id_input    | Input IDs or range of IDs | None |
| --limit       | Limit the number of results | 80 |
| --search_string | Search string to filter results | None |
| --ascending | Sort results in ascending order | False |
| --use_async | Use asynchronous requests | False |

## Usage

The command name for this project is `met_query`

Examples:
```bash
met_query classifications --id_input '7829, 9367, 13737' --limit 5 --search_string 'Textiles' --ascending False

met_query classifications --id_input '14000-15000' --limit 10 --search_string 'Textiles' --ascending False --use_async
```

