from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

class LiveTime:
    """Base class for all transportation services"""
    LastUpdate = datetime.now()
    
    def __init__(self):
        self.ID = "0"
        self.Name = ""
        self.Destination = ""
        self.SchArrival = ""
        self.ExptArrival = ""
        self.Platform = ""
        self.Station = ""
        self.Via = ""
        self.DisplayTime = ""
        self.Operator = ""
        self.Type = ""
        self.Index = " "
        self.LastStaticUpdate = datetime.now()
        self.args = None

    @abstractmethod
    def TimeInMin(self):
        pass
        
    @abstractmethod  
    def GetDisplayTime(self):
        pass

    def TimePassedStatic(self, update_limit):
        """Check if static display needs updating"""
        return ("min" in self.DisplayTime) and \
               (datetime.now() - self.LastStaticUpdate).total_seconds() > update_limit

    @staticmethod
    def TimePassed(request_limit):
        """Check if enough time has passed for new API request"""
        return (datetime.now() - LiveTime.LastUpdate).total_seconds() > request_limit

class LiveTimeStud(LiveTime):
    """Blank service object used when no data is available"""
    def __init__(self):
        super().__init__()
        self.ID = "0"
        self.Name = " "
        self.Destination = " "
        self.DisplayTime = " "
        self.ExptArrival = " "
        self.SchArrival = " "
        self.Via = " "
        self.Platform = " "
        self.Station = " "
        self.Operator = " "
        self.Type = " "
        self.Index = " "
    
    def TimePassedStatic(self, _):
        return False

class BaseService(ABC):
    """Abstract base class for transport services"""
    
    @staticmethod
    @abstractmethod
    def GetData(args) -> list:
        """Retrieve service data from API"""
        pass