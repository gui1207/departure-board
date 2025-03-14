from datetime import datetime
import json 
from urllib.request import Request, urlopen
from ..common.base_service import LiveTime, LiveTimeStud, BaseService

class TflTime(LiveTime):
    """TfL specific implementation of LiveTime"""
    def __init__(self, Data, args, Index=None):
        super().__init__()
        self.args = args
        
        # Handle index first
        self.Index = f"{Index}"
        
        # Rest of initialization
        self.ID = str(Data['id'])
        self.ExptArrival = self.convertUTCtoLocal(str(Data['expectedArrival']))
        self.SchArrival = self.convertUTCtoLocal(str(Data['expectedArrival']))
        self.Platform = Data.get('platformName', '').strip().replace('null', '')
        self.Name = str(Data['lineName']).strip()
        self.Station = str(Data['stationName']).strip()
        self.Destination = str(Data['towards']).strip()
        self.Operator = str(Data.get('operatorName', 'Transport for London')).strip()
        self.Type = str(Data.get('modeName', '')).strip() #E.g: tube or bus

        destination_name = Data.get('destinationName', Data['towards']).strip()
        if (self.Type == "bus"):           
            self.Destination = str(Data['destinationName']).strip()
            self.Via = f"This is {self.Name}, to {destination_name}"
            if self.Platform and self.Platform is not None:
                self.Station = f"Stop {self.Platform} - {self.Station}"
        else:
            self.Station = self.Station.replace('Underground Station', '')
            self.Via = f"This is a {self.Name} line train, to {destination_name}"       

        self.DisplayTime = self.GetDisplayTime()

    def convertUTCtoLocal(self, dateTimeInput):
        """Convert UTC time from TfL API to local time"""
        try:
            datetimeTemp = datetime.strptime(dateTimeInput, '%Y-%m-%dT%H:%M:%SZ')
            datetimeTemp = datetimeTemp + (datetime.now() - datetime.utcnow())
            return datetimeTemp.strftime('%H:%M')
        except Exception as e:
            print(f"Time conversion error: {e}")
            return dateTimeInput
        

    def TimeInMin(self):
        """Calculate minutes until arrival"""
        try:
            arrival = datetime.strptime(str(datetime.now().date()) + " " + self.ExptArrival, '%Y-%m-%d %H:%M')
            return max(0, (arrival - datetime.now()).total_seconds() / 60)
        except Exception as e:
            print(f"TimeInMin calculation error in TflTime: {e}")
            return 0

    def GetDisplayTime(self):
        self.LastStaticUpdate = datetime.now()
        time_diff = self.TimeInMin()

        result = ""
        if time_diff <= 1:
            result = " Due"
        elif time_diff >= 59:
            result = " " + datetime.strptime(self.ExptArrival, '%H:%M').strftime(
                "%H:%M" if (self.args.TimeFormat==24) else "%I:%M")
        else:
            result = " %d mins" % time_diff
        
        return result

class TflService(BaseService):
    """Service class for TfL API integration"""
    def __init__(self, args):
        self.args = args
        self.last_api_call = datetime.now()

    @staticmethod
    def GetData(args, force=False):
        """Retrieve data from TfL API"""        
        if not force and not LiveTime.TimePassed(args.RequestLimit):
            if not args.NoConsole:
                print(f"{datetime.now().time()} - Not retrieving new data - Force={force} - LiveTime.TimePassed={LiveTime.TimePassed(args.RequestLimit)})")
            return []
            
        LiveTime.LastUpdate = datetime.now()
        services = []
        
        try:
            url = f"https://api.tfl.gov.uk/StopPoint/{args.StationID}/Arrivals"
            if args.APIKey:
                url += f"?app_key={args.APIKey}"

            req = Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Accept', '*/*')
            
            with urlopen(req) as conn:
                tempServices = json.loads(conn.read())
                
                # First sort by arrival time
                sorted_services = sorted(tempServices, 
                    key=lambda x: datetime.strptime(x['expectedArrival'], '%Y-%m-%dT%H:%M:%SZ'))
                
                current_index = 1
                
                for service in sorted_services:
                    # Check NumberOfCards limit
                    if len(services) >= args.NumberOfCards:
                        break
                    
                    if str(service['lineName']) not in args.ExcludeLines:
                        if args.Direction == 'both' or ("direction" in service and args.Direction == str(service["direction"])):
                            time = TflTime(service, args, current_index)
                            services.append(time)
                            current_index += 1

                return services

        except Exception as e:
            print(f"GetData() - Error: {str(e)}")
            return []