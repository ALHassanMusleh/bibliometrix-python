from www.services import *


def get_database(input):
    """
    Determine the database based on the user's selection.
    
    Args:
        input: An object that provides user input methods.
        
    Returns:
        A string representing the name of the database.
    """
    if input.select() == "1A":  # Bibliographic databases
        
        database = input.database()
        
        if database == "wos":
            database = "Web of Science"
        elif database == "scopus":
            database = "Scopus"
        elif database == "dimensions":
            database = "Dimensions"
        elif database == "lens":
            database = "Lens.org"
        elif database == "pubmed":
            database = "PubMed"
        elif database == "cochrane":
            database = "Cochrane Library"
    
    elif input.select() == "1B":  # Bibliometrix database
        database = "Bibliometrix"
    
    elif input.select() == "1C":  # Sample database
        database = "Sample"

    elif input.select() == "1D":  # API retrieval (Advanced Level)
        platform = input.api_platform() if hasattr(input, 'api_platform') else "pubmed"
        database = f"API ({platform.upper()})"

    else:
        database = "Unknown"
    
    return database