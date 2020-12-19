"""
Utility functions
"""

"""
Helper function to remove special characters, capitilzation, and spaces from a string
"""
def clean_string(phrase):
    ret = [char for char in phrase if char.isalnum()]
    return "".join(ret).lower()