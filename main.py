import argparse
from game import Game

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('breadth', type=int, nargs='?', default=3, help='number max number of links to choose from per page')
    parser.add_argument('depth', type=int, nargs='?', default=4, help='number of pages between the starting and finishing topic')
    args = parser.parse_args()
    
    Game(args.breadth, args.depth).run()
