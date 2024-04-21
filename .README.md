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

## Usage

The command for this project is `met_query`

Example:
```bash
met_query classifications --id_input '7829, 9367, 13737' --limit 5 --search_string 'Textiles' --ascending False
```

