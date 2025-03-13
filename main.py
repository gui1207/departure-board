from datetime import datetime
import time
from luma.core import cmdline
from luma.core.image_composition import ImageComposition
from src.common.args import parse_args
from src.common.display import BoardController, DisplayUtils
from src.services.tfl import TflService
from src.api import DepartureBoardAPI

def initialize_display(args):
   device = cmdline.create_device(
       cmdline.create_parser(description='Live Departure Board').parse_args(
           ['--display', str(args.Display), 
            '--interface', 'spi',
            '--width', '256', 
            '--rotate', str(args.Rotation)]
       )
   )

   device.contrast(255)
   
   if args.Display == 'gifanim':
       device._filename = str(args.filename)
       device._max_frames = int(args.maxframes)
   
   return device

def main():
    args = parse_args()
    device = initialize_display(args)

    api = DepartureBoardAPI()
    api.start()
    
    DisplayUtils.show_splash_screen(device, args)
    
    image_composition = ImageComposition(device)
    board = BoardController(image_composition, args.Delay, device, args)
    api.set_board(board)

    board.start()
    

if __name__ == "__main__":
   main()