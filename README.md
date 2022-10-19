# RDFGenerator

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
