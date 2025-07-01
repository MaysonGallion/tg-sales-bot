"""Simple example of functions that ask the user for three numbers
and return their addition or subtraction.
"""

def add_three_numbers():
    """Prompt the user for three numbers and return their sum."""
    n1 = float(input("Enter first number: "))
    n2 = float(input("Enter second number: "))
    n3 = float(input("Enter third number: "))
    return n1 + n2 + n3


def subtract_three_numbers():
    """Prompt the user for three numbers and return the result of
    subtracting the second and third from the first."""
    n1 = float(input("Enter first number: "))
    n2 = float(input("Enter second number: "))
    n3 = float(input("Enter third number: "))
    return n1 - n2 - n3


if __name__ == "__main__":
    print("Sum:", add_three_numbers())
    print("Difference:", subtract_three_numbers())
