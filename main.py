### Code generator xlsx -> rdf ttl


import os
import datetime
import pandas as pd



def generate_rdf_files():
    """
    Generates RDF TTL files from all XLSX files located in /data and stores them in the same directory.

    Format requirements:
    - Prefixes must be specified in a tab called PREFIXES
    - One tab for each class
    - One row for each instance in a class
    - The first row contains column names. They must denote the predicates in SPO triples.
      Datatypes must be enclosed by [ ], e.g., [rdfs:Class], [string], [int], [float], [date]
    - The first column must contain the subject URI of SPO triple.
    - Cells in other columns contain objects in SPO triples. Multiple objects must be separated by |
    - Tabs containing parentheses in their name, e.g., (Info) are ignored
    """
    print('Starting...')
    filenames = os.listdir('data')
    xlsx_filenames = [filename for filename in filenames if '.xlsx' in filename]
    for xlsx_filename in xlsx_filenames:
        print(f'Generating rdf file for {xlsx_filename} ...')
        data = pd.read_excel(f'data/{xlsx_filename}', sheet_name=None, index_col=0, keep_default_na=False)
        rdf_filename = xlsx_filename.replace('.xlsx', '.ttl')
        with open(f'data/{rdf_filename}', "w", newline="", encoding="utf-8") as file:
            file.write(f'### Ontology file generated from {xlsx_filename}.')
            file.write(f'\n### {datetime.datetime.now()}')
            generate_rdf_file(data, file)
        print(f'Finished generating rdf file for {xlsx_filename}')
    print ('Finished.')


def generate_rdf_file(data, file):
    """
    Generates RDF tiples for data provided and stores them in a file.

    :param data: dict with tab names as keys and pd.DataFrame as values
    :param file: io.TextIOWrapper
    """
    for tab in data.keys(): # for each tab in the spreadsheet representing a  class
        if not '(' in tab:  # Tabs with (Info) in title are ignored
            file.write(f'\n\n\n# {tab}\n')
            df = data[tab]  # pd.DataFrame for each tab
            if tab in ['Prefix', 'Prefixes', 'PREFIX', 'PREFIXES']:
                generate_prefixes(df, file)
            else:
                generate_triples(df, file)



def generate_prefixes(df:pd.DataFrame, file):
    """
    Generates RDF @prefix statements from a DataFrames and stores them in a file.

    :param df: pd.DataFrame
    :param file: io.TextIOWrapper
    """
    for prefix, row in df.iterrows(): # for each row in the sheet representing a prefix declaration
        if prefix:  # row not empty
            file.write(f'\n@prefix {prefix} {row[0]} .') # prefix declaration




def generate_triples(df:pd.DataFrame, file):
    """
    Generates RDF triples from a DataFrame and stores them in a file.

    :param df: pd:DataFrame
    :param file: io.TextIOWrapper
    """
    for subject, row in df.iterrows(): # for each row in the sheet representing an entity
        if subject and pd.notnull(subject):  # URI not empty
            file.write(f'\n{validate_URI(subject)} ') # subject URI
            firstPredicate = True
            for predicate_header, object in row.iteritems(): # for each predicate-object pair
                if object and pd.notnull(object): # object value is not empty
                    if not firstPredicate:
                        file.write(f' ;\n    ')
                    predicate, datatype = extract_property_and_type(predicate_header)
                    file.write(f'{validate_URI(predicate)}')
                    generate_object_values(object, datatype, file)
                    firstPredicate = False
            file.write(' .')



def generate_object_values(object, datatype, file):
    """
    Generates RDF object values and stores them in a file.

    :param object: may be int, float or string. if string containing '|' then it will be treated as several objects
    :param datatype: 'URI', 'string', 'int', 'float' or 'date'
    :param file: io.TextIOWrapper
    """
    if type(object) == str and '|' in object: # several object values split via |
        objects = object.split('|')
        firstObject = True
        for obj in objects:
            if not firstObject:
                file.write(' ,')
            generate_object_value(obj, datatype, file)
            firstObject = False
    else:
        generate_object_value(object, datatype, file)



def generate_object_value(object, datatype, file):
    """
    Generates RDF object value and stores it in a file.

    :param object: may be int, float or string
    :param datatype: 'URI', 'string', 'int', 'float' or 'date'
    :param file: io.TextIOWrapper
    """
    if type(object) == str:
        object = object.strip()
    if datatype == 'URI':
        file.write(f' {validate_URI(object)}')
    elif datatype == 'text':
        if "'" not in object: file.write(f" '''{object}'''")
        elif '"' not in object: file.write(f' """{object}"""')
        else: 
            txt = object.replace('"', '\"')
            file.write(f" '''{txt}'''")
    else:
        suffix = rdf_data_type_suffix(datatype)
        if datatype == 'boolean'  and isinstance(object, bool):
            #sometimes a literal instead of a boolean python instance is returned, this will ensure that both case produce the correct format
            #Case 1: isInstance == boolean (True / False) => "true"/"false"
            #Case 2: literal "true"/"false" => "true"/"false"
            object = str(object).lower()
        file.write(f' "{object}"{suffix}')


def validate_URI(txt: str):
    """
    Checks for validity of an URI string, in particular missing namespace and whitespace within the string.

    :param txt: string to be interpreted as URI in RDF Turtle
    :return: trimmed txt (leading and trailing whitespaces removed)
    """
    txt = txt.strip()
    if ' ' in txt:
        print(f'WARNING: "{txt}" is not a valid URI since it contains whitespace')
    if not ':' in txt and not txt == 'a':   # RDF Turtle abbreviation 'a' for 'rdf:type' allowed
        print(f'WARNING: "{txt}" is not a valid URI since it does not contain a namespace')
    return txt


def extract_property_and_type(property_headline: str):
    """
    Extracts from a column headline property name and datatype according to convention.

    Example: 'rdfs:label [string]' will be split in property 'rdfs:label' and datatype 'string'
    Example: 'a [rdfs:Class]' will be split in property 'a' and datatype 'URI'

    :param property_headline: string representing column headline
    :return: a tuple of 2 strings representing property and datatype. Default value for datatype if none is given: 'URI'
    """
    start = property_headline.find('[')
    end = property_headline.find(']')
    if start != -1 and end != -1:
        property = property_headline[:start].strip()
        datatype = property_headline[start+1:end].strip()
        if ':' in datatype: type = 'URI'
        elif datatype in ['int', 'integer', 'Integer']: type = 'integer'
        elif datatype in ['float', 'Float']: type = 'float'
        elif datatype in ['date', 'Date']: type = 'date'
        elif datatype in ['boolean', 'Boolean']: type = 'boolean'
        elif datatype in ['str', 'string', 'String']: type = 'string'
        elif datatype in ['text', 'Text']: type = 'text'
        return property, type
    else:
        return property_headline.strip(), 'URI'     # if no explit datatype is provided in [ ] then URI is assumed



def rdf_data_type_suffix(datatype: str) -> str:
    """
    Converts datatype strings into XSD datatype specifications

    :param datatype: 'string', 'int', 'float' or 'date'
    :return: XSD datatype specification or '' for strings
    """
    if datatype in ['integer']: return '^^xsd:integer'
    elif datatype in ['float']: return '^^xsd:float'
    elif datatype in ['date']: return '^^xsd:date'
    elif datatype in ['boolean']: return '^^xsd:boolean'
    elif datatype in ['string']: return ''
    else: return ''







# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    generate_rdf_files()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/



