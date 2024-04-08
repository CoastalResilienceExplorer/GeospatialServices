import argparse
from damage_assessment import main as damage_assessment
from population_assessment import main as population_assessment


if __name__ == "__main__": 
# Create an ArgumentParser instance
    parser = argparse.ArgumentParser(description='CLI wrapper for my_function')

    # Add arguments to the parser

    parser.add_argument('--option', choices=["damage", "population"], type=str, help='Path to flooding')
    parser.add_argument('--flooding', type=str, help='Path to flooding')
    parser.add_argument('--output', type=str, help='Path to output')
    parser.add_argument('--threshold', type=float, required=False, help='Path to output')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call your function with provided arguments
    if args.option == "damage":
        result = damage_assessment(args.flooding)
    else:
        result = population_assessment(args.flooding, args.threshold)
    
    result.rio.to_crs(args.output)