from datetime import datetime
from PIL import ImageFont, Image, ImageDraw
from luma.core.render import canvas
from luma.core.image_composition import ImageComposition, ComposableImage
import os
import inspect
import time
import signal
import sys
from .base_service import LiveTime, LiveTimeStud
from ..services.tfl import TflService
import asyncio
from enum import Enum, auto
from typing import Optional
from luma.core.image_composition import ComposableImage

# Initialize fonts
base_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
BasicFontHeight = 12
BasicFont = ImageFont.truetype(f"{base_path}/../../resources/fonts/lower.ttf", BasicFontHeight)
TimeFont = ImageFont.truetype(f"{base_path}/../../resources/fonts/time.otf", 14)
StationFont = ImageFont.truetype(f"{base_path}/../../resources/fonts/Bold.ttf", 11)
TitleFont = ImageFont.truetype(f"{base_path}/../../resources/fonts/Bold.ttf", 20)
VersionFont = ImageFont.truetype(f"{base_path}/../../resources/fonts/Skinny.ttf", 15)

#index e.g: 9 = 6 (font 12)
#service e.g: 999 = 19 (font 12)

SCALE_FACTOR = BasicFontHeight / 12
BASE_INDEX_WIDTH = 6
BASE_SERVICE_WIDTH = 19
BASE_SPACING = 6

INDEX_WIDTH = int((BASE_INDEX_WIDTH + BASE_SPACING) * SCALE_FACTOR)
SERVICE_WIDTH = int((BASE_SERVICE_WIDTH + BASE_SPACING) * SCALE_FACTOR)

class DisplayUtils:
    REFRESH_RATE = 0.02  # 50Hz refresh rate for display updates        

    @staticmethod
    def show_splash_screen(device, args):
        if args.SplashScreen:
            with canvas(device) as draw:
                base_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
                

                title = "Departure Board"
                version = "Version: 3.0.0"

                title_width = int(draw.textlength(title, TitleFont))
                version_width = int(draw.textlength(version, VersionFont))

                draw.text((device.width/2 - title_width/2, 10), title, font=TitleFont)
                draw.text((device.width/2 - version_width/2, 35), version, font=VersionFont)
                
            time.sleep(3)

    @staticmethod
    def is_time_between(args):
        check_time = datetime.now().time()
        if args.InactiveHours[0] < args.InactiveHours[1]:
            return check_time >= args.InactiveHours[0] and check_time <= args.InactiveHours[1]
        return check_time >= args.InactiveHours[0] or check_time <= args.InactiveHours[1]

class TextImage:
    def __init__(self, device, text):
        self.image = Image.new(device.mode, (device.width, 16))
        draw = ImageDraw.Draw(self.image)
        draw.text((0, 0), text, font=BasicFont, fill="white")

        self.width = 5 + int(draw.textlength(text, BasicFont))
        self.height = 5 + BasicFontHeight
        del draw

class TextImageComplex:
    def __init__(self, device, service):
        self.image = Image.new(device.mode, (device.width, 16))
        draw = ImageDraw.Draw(self.image)
        
        # Handle index and destination layout
        if service.Type == "bus":
           # Bus format: Index | Line Number | Destination 
           index_width = int(draw.textlength(service.Index, BasicFont))
           line_width = int(draw.textlength(service.Name, BasicFont))
           
           draw.text((0, 0), service.Index, font=BasicFont, fill="white")  # Index
           draw.text((INDEX_WIDTH, 0), service.Name, font=BasicFont, fill="white")  # Bus line
           draw.text((INDEX_WIDTH + SERVICE_WIDTH, 0), service.Destination, font=BasicFont, fill="white")  # Destination
        else:
            # Train format: Index | Destination
            index_width = int(draw.textlength(service.Index, BasicFont))
            draw.text((0, 0), service.Index, font=BasicFont, fill="white")
            draw.text((INDEX_WIDTH, 0), service.Destination, font=BasicFont, fill="white")

        self.width = device.width
        self.height = 16
        del draw

class StaticTextImage:
    def __init__(self, device, service, previous_service):
        self.image = Image.new(device.mode, (device.width, 32))
        
        # Previous service line
        prev_time = TextImage(device, previous_service.DisplayTime)
        prev_complex = TextImageComplex(device, previous_service)
        
        # Current service line  
        curr_time = TextImage(device, service.DisplayTime)
        curr_complex = TextImageComplex(device, service)
        
        # Combine images maintaining layout
        self.image.paste(prev_complex.image, (0, 0))
        self.image.paste(prev_time.image, (device.width - prev_time.width, 0))
        
        self.image.paste(curr_complex.image, (0, 16))
        self.image.paste(curr_time.image, (device.width - curr_time.width, 16))

        self.width = device.width
        self.height = 32

class RectangleCover:
    def __init__(self, device):        
        self.image = Image.new(device.mode, (device.width, 16))
        draw = ImageDraw.Draw(self.image)
        draw.rectangle((0, 0, device.width,16), outline="black", fill="black")
        del draw
        self.width = device.width 
        self.height = 16

class NoService:
    def __init__(self, device):        
        self.image = Image.new(device.mode, (device.width, 16))
        draw = ImageDraw.Draw(self.image)
        draw.text((0, 0), "No Scheduled Services Found", font=BasicFont, fill="white")
        self.width = int(draw.textlength("No Scheduled Services Found", font=BasicFont))
        self.height = 16
        del draw

class Synchroniser:
    def __init__(self): self.synchronised = {}
    def busy(self, task): self.synchronised[id(task)] = False
    def ready(self, task): self.synchronised[id(task)] = True
    def is_synchronised(self): return all(self.synchronised.values())

from enum import Enum, auto
from typing import Optional
from luma.core.image_composition import ComposableImage
from .base_service import LiveTimeStud

class ScrollState(Enum):
    WAIT_OPENING = auto()
    OPENING_SCROLL = auto()
    OPENING_END = auto()
    SCROLL_DECIDER = auto()
    SCROLLING_WAIT = auto()
    SCROLLING = auto()
    WAIT_SYNC = auto()
    WAIT_STUD = auto()
    STUD_SCROLL = auto()
    STUD_END = auto()
    TRAIN_APPROACHING = auto()
    STUD = auto()

class StateHandler:
    def __init__(self, scroll_time):
        self.scroll_time = scroll_time
        self.state = ScrollState.OPENING_SCROLL if scroll_time.CurrentService.ID != "0" else ScrollState.STUD

    def handle_state(self):
        handlers = {
            ScrollState.WAIT_OPENING: self._handle_wait_opening,
            ScrollState.OPENING_SCROLL: self._handle_opening_scroll,
            ScrollState.OPENING_END: self._handle_opening_end,
            ScrollState.SCROLL_DECIDER: self._handle_scroll_decider,
            ScrollState.SCROLLING_WAIT: self._handle_scrolling_wait,
            ScrollState.SCROLLING: self._handle_scrolling,
            ScrollState.WAIT_SYNC: self._handle_wait_sync,
            ScrollState.WAIT_STUD: self._handle_wait_stud,
            ScrollState.STUD_SCROLL: self._handle_stud_scroll,
            ScrollState.STUD_END: self._handle_stud_end,
            ScrollState.TRAIN_APPROACHING: self._handle_train_approaching,
            ScrollState.STUD: self._handle_stud
        }
        handler = handlers.get(self.state)
        if handler:
            handler()

    def transition_to(self, new_state: ScrollState):
        self.state = new_state

    def _handle_wait_opening(self):
        if not self.scroll_time.is_waiting():
            self.transition_to(ScrollState.OPENING_SCROLL)

    def _handle_opening_scroll(self):
        if self.scroll_time.image_y_posA < 16:
            self.scroll_time.render()
            self.scroll_time.image_y_posA += self.scroll_time.speed
        else:
            self.transition_to(ScrollState.OPENING_END)

    def _handle_opening_end(self):
        self.scroll_time._handle_opening_end()
        self.transition_to(ScrollState.SCROLL_DECIDER)

    def _handle_scroll_decider(self):
        if self.scroll_time.synchroniser.is_synchronised():
            if not self.scroll_time.is_waiting():
                self.scroll_time.synchroniser.busy(self.scroll_time)
                if self.scroll_time.CurrentService.ID == "0":
                    self.scroll_time.synchroniser.ready(self.scroll_time)
                    self.transition_to(ScrollState.STUD)
                else:
                    self.transition_to(ScrollState.WAIT_SYNC)

    def _handle_scrolling_wait(self):
        if not self.scroll_time.is_waiting():
            self.scroll_time._start_scrolling()
            self.transition_to(ScrollState.SCROLLING)

    def _handle_scrolling(self):
        if self.scroll_time.image_x_pos < self.scroll_time.max_pos:
            self.scroll_time.render()
            self.scroll_time.image_x_pos += self.scroll_time.speed
        else:
            self.scroll_time._end_scrolling()
            self.transition_to(ScrollState.WAIT_SYNC)

    def _handle_wait_sync(self):
        if self.scroll_time.image_x_pos != 0:
            self.scroll_time.image_x_pos = 0
            self.scroll_time.render()
        else:
            if self.scroll_time.synchroniser.is_synchronised():
                next_row = self.scroll_time.position + 1
                if next_row <= 2:
                    self.scroll_time.Controller.requestCardChange(self.scroll_time, next_row)
                    self.scroll_time.synchroniser.ready(self.scroll_time)
            else:
                self.scroll_time.synchroniser.ready(self.scroll_time)

    def _handle_wait_stud(self):
        if not self.scroll_time.is_waiting():
            self.transition_to(ScrollState.STUD_SCROLL)

    def _handle_stud_scroll(self):
        if self.scroll_time.image_y_posA < 16:
            self.scroll_time.render()
            self.scroll_time.image_y_posA += self.scroll_time.speed
        else:
            self.transition_to(ScrollState.STUD_END)

    def _handle_stud_end(self):
        self.scroll_time._handle_stud_end()
        self.transition_to(ScrollState.STUD)

    def _handle_train_approaching(self):
        self.scroll_time._handle_train_approaching()

    def _handle_stud(self):
        if not self.scroll_time.is_waiting():
            self.scroll_time.Controller.requestCardChange(self.scroll_time, self.scroll_time.position + 1)

class ScrollTime:
    def __init__(self, image_composition, service, scroll_delay, synchroniser, device, position, controller):
        self.speed = controller.args.Speed
        self.position = position
        self.Controller = controller
        self.device = device
        self.args = controller.args
        self.image_composition = image_composition
        self.CurrentService = service
        self.delay = int((scroll_delay / 2) / 0.02)
        self.synchroniser = synchroniser
        
        self.rectangle = ComposableImage(RectangleCover(device).image, position=(0,16 * position + 16))
        self.generateCard(service)
        self.IStaticOld = ComposableImage(StaticTextImage(device, service, LiveTimeStud()).image, 
                                        position=(0, (16 * position)))
        
        self.max_pos = self.IDestination.width if hasattr(self, 'IDestination') else 0
        self.image_y_posA = 0
        self.image_x_pos = 0
        self.ticks = 0
        self.Alternator = 0
        
        self.state_handler = StateHandler(self)
        
        self.image_composition.add_image(self.IStaticOld)
        self.image_composition.add_image(self.rectangle)
        if hasattr(self.args, 'warning'):
            self.TrainApproaching = ComposableImage(TextImage(device, "* STAND BACK TRAIN APPROACHING *").image, 
                                                  position=(0, 16 * self.position))
        self.render()
        self.synchroniser.ready(self)

    def generateCard(self, service):
        displayTimeTemp = TextImage(self.device, service.DisplayTime)        
        time_position = self.device.width - displayTimeTemp.width

        IDestinationTemp = TextImageComplex(self.device, service)
        self.IDestination = ComposableImage(
            IDestinationTemp.image,
            position=(0, 16 * self.position)
        )
        
        self.IDisplayTime = ComposableImage(
            displayTimeTemp.image,
            position=(time_position, 16 * self.position)
        )

        self.max_pos = IDestinationTemp.width

    def changeCard(self, newService, device):
        self.synchroniser.busy(self)
        self.IStaticOld = ComposableImage(
            StaticTextImage(device, newService, self.CurrentService).image,
            position=(0, (16 * self.position))
        )
        
        self.image_composition.add_image(self.IStaticOld)
        self.image_composition.add_image(self.rectangle)

        if self.CurrentService.ID != "0":
            if hasattr(self, 'IDestination'):
                self.image_composition.remove_image(self.IDestination)
            if hasattr(self, 'IDisplayTime'):
                self.image_composition.remove_image(self.IDisplayTime)
            
        self.image_composition.refresh()
        self.generateCard(newService)
        self.CurrentService = newService
        self.max_pos = self.IDestination.width
        self.state_handler.transition_to(ScrollState.WAIT_STUD if newService.ID == "0" else ScrollState.WAIT_OPENING)

    def updateCard(self, newService, device):
        self.state_handler.transition_to(ScrollState.SCROLL_DECIDER)
        self.synchroniser.ready(self)
        self.image_composition.remove_image(self.IDisplayTime)
        
        displayTimeTemp = TextImage(device, newService.DisplayTime)
        self.IDisplayTime = ComposableImage(displayTimeTemp.image, 
                                          position=(device.width - displayTimeTemp.width, 16 * self.position))
        
        self.image_composition.add_image(self.IDisplayTime)
        self.image_composition.refresh()

    def tick(self):
        if self.CurrentService.TimePassedStatic(self.Controller.args.StaticUpdateLimit) and \
           self.state_handler.state in [ScrollState.SCROLL_DECIDER, ScrollState.SCROLLING_WAIT, 
                                      ScrollState.SCROLLING, ScrollState.WAIT_SYNC]:
            self.updateTime()
        
        self.state_handler.handle_state()

    def _handle_opening_end(self):
        self.image_x_pos = 0
        self.image_y_posA = 0
        self.image_composition.remove_image(self.IStaticOld)
        self.image_composition.remove_image(self.rectangle)
        del self.IStaticOld

        self.image_composition.add_image(self.IDestination)
        self.image_composition.add_image(self.IDisplayTime)        
        self.render()
        self.synchroniser.ready(self)

    def _start_scrolling(self):
        self.image_composition.remove_image(self.IDestination)
        self.image_composition.remove_image(self.IDisplayTime)

    def _end_scrolling(self):
        self.image_composition.add_image(self.IDestination)
        self.image_composition.add_image(self.IDisplayTime)

    def _handle_stud_end(self):
        self.image_x_pos = 0
        self.image_y_posA = 0
        self.image_composition.remove_image(self.IStaticOld)
        self.image_composition.remove_image(self.rectangle)
        del self.IStaticOld
        self.render()
        self.synchroniser.ready(self)

    def _handle_train_approaching(self):
        if self.Alternator == 0:
            self.image_composition.add_image(self.TrainApproaching)
            
        self.Alternator += 1
        if self.Alternator % 9 == 0:            
            if self.Alternator % 18 == 0:
                self.image_composition.remove_image(self.rectangle)
                self.image_composition.add_image(self.TrainApproaching)
            else:
                self.image_composition.remove_image(self.TrainApproaching)
                self.image_composition.add_image(self.rectangle)
            self.image_composition.refresh()

    def updateTime(self):
        if hasattr(self, 'IDisplayTime'):
            if self.IDisplayTime in self.image_composition.composed_images:
                self.image_composition.remove_image(self.IDisplayTime)
            self.CurrentService.DisplayTime = self.CurrentService.GetDisplayTime()
            displayTimeTemp = TextImage(self.device, self.CurrentService.DisplayTime)            
            self.IDisplayTime = ComposableImage(displayTimeTemp.image, 
                                            position=(self.device.width - displayTimeTemp.width, 16 * self.position))
            self.image_composition.add_image(self.IDisplayTime)
            self.image_composition.refresh()

            self.image_composition.remove_image(self.IDisplayTime)
            self.CurrentService.DisplayTime = self.CurrentService.GetDisplayTime()
            displayTimeTemp = TextImage(self.device, self.CurrentService.DisplayTime)            
            self.IDisplayTime = ComposableImage(displayTimeTemp.image, 
                                            position=(self.device.width - displayTimeTemp.width, 16 * self.position))
            self.image_composition.add_image(self.IDisplayTime)
            self.image_composition.refresh()

    def SetTrainApproaching(self):
        self.delete()
        self.state_handler.transition_to(ScrollState.TRAIN_APPROACHING)
        self.Alternator = 0

    def SetNotTrainApproaching(self):
        if self.state_handler.state == ScrollState.TRAIN_APPROACHING:
            if self.Alternator % 18 < 9:
                self.image_composition.remove_image(self.TrainApproaching)
            else:
                self.image_composition.remove_image(self.rectangle)
            self.image_composition.add_image(self.IDestination)
            self.image_composition.add_image(self.IDisplayTime)        
            self.state_handler.transition_to(ScrollState.SCROLL_DECIDER)
            self.Alternator = 0

    def render(self):
        if self.state_handler.state in [ScrollState.SCROLLING, ScrollState.WAIT_SYNC]:
            self.IDestination.offset = (self.image_x_pos, 0)            
        if self.state_handler.state in [ScrollState.OPENING_SCROLL, ScrollState.STUD_SCROLL]:            
            self.IStaticOld.offset = (0, self.image_y_posA)

    def delete(self):
        try:
            self.image_composition.remove_image(self.IStaticOld)
            self.image_composition.remove_image(self.rectangle)
        except: pass
        try:
            self.image_composition.remove_image(self.IDestination)
            self.image_composition.remove_image(self.IDisplayTime)
        except: pass
        self.image_composition.refresh()

    def is_waiting(self):
        self.ticks += 1
        if self.ticks > self.delay:
            self.ticks = 0
            return False
        return True
    
class BoardController:
    def __init__(self, image_composition, scroll_delay, device, args):
        self.image_composition = image_composition
        self.scroll_delay = scroll_delay
        self.device = device
        self.args = args
        self.ticks = 0
        self.State = "alive"
        self.energy_mode = "normal"
        self.service = TflService(args)
        self.rotation_index = 2
        self._warning_state = {
            "shown": set(),
            "start": None,
            "duration": args.WarningDuration
        }
        self._station_change_lock = asyncio.Lock()
        
        # Initialize services
        self.Services = self.service.GetData(args, True)
        if not args.NoConsole:
            self._log_service_update()
            
        # Setup display elements    
        self._setup_display()
        self.setInitialCards()

    def _setup_display(self):
        NoServiceTemp = NoService(self.device)
        self.NoServices = ComposableImage(
            NoServiceTemp.image, 
            position=(
                int(self.device.width/2 - NoServiceTemp.width/2),
                int(self.device.height/2 - NoServiceTemp.height/2)
            )
        )

    def setInitialCards(self):
        self.synchroniser = Synchroniser()
        self.top = ScrollTime(
            self.image_composition,
            self.Services[0] if len(self.Services) >= 1 else LiveTimeStud(),
            self.scroll_delay,
            self.synchroniser,
            self.device,
            0,
            self
        )
        
        self.middle = ScrollTime(
            self.image_composition,
            self.Services[1] if len(self.Services) >= 2 else LiveTimeStud(),
            self.scroll_delay,
            self.synchroniser,
            self.device,
            1,
            self
        )
        
        self.bottom = ScrollTime(
            self.image_composition,
            self.Services[2] if len(self.Services) >= 3 else LiveTimeStud(),
            self.scroll_delay,
            self.synchroniser,
            self.device,
            2,
            self
        )

    def start(self):
        try:
            while True:
                time.sleep(DisplayUtils.REFRESH_RATE)
                
                if self.State == "dead":
                    self._handle_dead_state()
                    continue

                self._handle_energy_saving()
                
                if self.State == "alive":
                    self.render_display_frame(self.device)

        except KeyboardInterrupt:
            pass

    def _handle_dead_state(self):
        for image in self.image_composition.composed_images[:]:
            self.image_composition.remove_image(image)
        self.image_composition.add_image(self.NoServices)
        self.image_composition.refresh()
        with canvas(self.device, background=self.image_composition()) as draw:
            pass

    def _handle_energy_saving(self):
        if self.args.EnergySaverMode != "none" and DisplayUtils.is_time_between(self.args):
            if self.args.EnergySaverMode == "dim" and self.energy_mode == "normal":
                self.device.contrast(15)
                self.energy_mode = "dim"
                self.render_display_frame(self.device)
            elif self.args.EnergySaverMode == "off" and self.energy_mode == "normal":
                self.device.clear()
                self.device.hide()
                self.energy_mode = "off"
        else:
            if self.energy_mode != "normal":
                self.device.contrast(255)
                if self.energy_mode == "off":
                    self.device.show()
                    DisplayUtils.show_splash_screen(self.device, self.args)
                self.energy_mode = "normal"

    def render_display_frame(self, device):
        self.tick()
        station = self.Services[0].Station if len(self.Services) > 0 else ""
        msg_time = datetime.now().strftime("%H:%M:%S" if (self.args.TimeFormat==24) else "%I:%M:%S")
        
        with canvas(device, background=self.image_composition()) as draw:
            self.image_composition.refresh()
            
            draw.text((BASE_SPACING, device.height-16), station, font=StationFont, align="left")
            time_width = int(draw.textlength(msg_time, TimeFont))
            draw.text((device.width - time_width - BASE_SPACING, device.height-16), 
                     msg_time, font=TimeFont, align="right")

    def tick(self):
        if len(self.Services) == 0:
            if self.ticks == 0:
                self.image_composition.add_image(self.NoServices)
            if not self.is_waiting():
                self._clear_display()
                self.State = "dead"
        else:
            self.top.tick()
            self.middle.tick()
            self.bottom.tick()

    def is_waiting(self):
        self.ticks += 1
        if self.ticks > self.args.RecoveryTime:
            self.ticks = 0
            return False
        return True

    def _log_service_update(self):
        print(f"{datetime.now().time()} - Data Retrieved: {len(self.Services)} services")

    def _handle_warning_state(self, service):
        current_time = time.time()
        
        if service.TimeInMin() <= self.args.WarningTime and service.ID not in self._warning_state["shown"]:
            self._warning_state["start"] = current_time
            self._warning_state["shown"].add(service.ID)
            self.bottom.SetTrainApproaching()
            return True

        if self._warning_state["start"]:
            elapsed = current_time - self._warning_state["start"]
            if elapsed < self._warning_state["duration"]:
                return True
            if elapsed >= self._warning_state["duration"]:
                self._warning_state["start"] = None
                self.bottom.SetNotTrainApproaching()
        return False

    def _update_services(self):
        if LiveTime.TimePassed(self.args.RequestLimit):
            new_services = self.service.GetData(self.args)
            if new_services:
                self.Services = new_services
                if not self.args.NoConsole:
                    self._log_service_update()

    def requestCardChange(self, card, row):
        if len(self.Services) == 0:
            card.changeCard(LiveTimeStud(), self.device)
            return

        if self.args.warning and len(self.Services) > 0:
            if self._handle_warning_state(self.Services[0]):
                return

        if self.rotation_index >= len(self.Services):
            self.rotation_index = 1
            self._update_services()

        if row == 1:
            self._handle_top_row(card)
        elif row == 2:
            self._handle_middle_rows()
        
    def _handle_top_row(self, card):
        service = self.Services[0]
        if service.ID == card.CurrentService.ID:
            card.updateCard(service, self.device)
        else:
            card.changeCard(service, self.device)

    def _handle_middle_rows(self):
        current_idx = self.rotation_index

        if current_idx < len(self.Services):
            service = self.Services[current_idx]
            
            # Reset animation timings
            self.middle.ticks = 0
            self.bottom.ticks = 0
            
            # Update middle row
            self.middle.changeCard(service, self.device)
            
            # Update bottom row
            next_idx = current_idx + 1
            next_service = (self.Services[next_idx] 
                          if next_idx < len(self.Services) 
                          else LiveTimeStud())
            
            self.bottom.state_handler.transition_to(ScrollState.WAIT_OPENING)
            self.bottom.changeCard(next_service, self.device)
        
        self.rotation_index += 2

    async def change_station(self, new_station_id: str):
        async with self._station_change_lock:
            self.State = "changing"
            self._clear_display()
            
            self.args.StationID = new_station_id           
            new_services = self.service.GetData(self.args, force=True)
            
            if not new_services:
                self.Services = []
                self.ticks = 0
                self.State = "dead"
                raise Exception("No services available")
                
            self.Services = new_services
            self.rotation_index = 2
            self.synchroniser = Synchroniser()
            self.State = "alive"
            self.setInitialCards()

    def _clear_display(self):
        self.top.delete()
        self.middle.delete() 
        self.bottom.delete()