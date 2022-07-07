"""Отредактирует creds.json"""
def prettify_json(string):
    string = string.replace('", "', '",\n\t"').replace('{', '{\n\t').replace('}', '\n}')
    return string
