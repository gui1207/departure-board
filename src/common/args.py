import argparse
from datetime import datetime

def check_positive(value):
    """Checks value is greater than Zero"""
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError("%s is invalid, value must be an integer value greater than 0." % value)
        return ivalue
    except:
        raise argparse.ArgumentTypeError("%s is invalid, value must be an integer value greater than 0." % value)

def check_time(value):
    """Checks string is a valid time range"""
    try:
        datetime.strptime(value.split("-")[0], '%H:%M').time()
        datetime.strptime(value.split("-")[1], '%H:%M').time()
    except:
        raise argparse.ArgumentTypeError("%s is invalid, value must be in the form of XX:XX-YY:YY, where the values are in 24hr format." % value)
    return [datetime.strptime(value.split("-")[0], '%H:%M').time(), datetime.strptime(value.split("-")[1], '%H:%M').time()]

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='London Underground Live Departure Board')
    
    # Optional parameters
    parser.add_argument("-t","--TimeFormat", help="Do you wish to use 24hr or 12hr time format; default is 24hr.", type=int,choices=[12,24],default=24)
    parser.add_argument("-v","--Speed", help="What speed do you want the text to scroll at on the display; default is 3.", type=check_positive,default=3)
    parser.add_argument("-d","--Delay", help="How long to pause between service rotations in seconds; default is 5", type=float,default=5)
    parser.add_argument("-r","--RecoveryTime", help="How long the display will wait before attempting to get new data again; default is 100.", type=check_positive,default=100)
    parser.add_argument("-n","--NumberOfCards", help="The maximum number of cards you will see before forcing a new data retrieval; default is 9.", type=check_positive,default=9)
    parser.add_argument("-y","--Rotation", help="Defines which way up the screen is rendered; default is 0", type=int,default=0,choices=[0,2])
    parser.add_argument("-l","--RequestLimit", help="Defines the minium amount of time between data requests; default is 15(seconds)", type=check_positive,default=15)
    parser.add_argument("-z","--StaticUpdateLimit", help="Defines the amount of time between static updates; default is 10(seconds)", type=check_positive,default=10)
    parser.add_argument("-e","--EnergySaverMode", help="Energy saving mode setting.", type=str,choices=["none","dim","off"],default="off")
    parser.add_argument("-i","--InactiveHours", help="The period for energy saving mode; default is '23:00-07:00'", type=check_time,default="23:00-07:00")
    parser.add_argument("-x","--ExcludeLines", default="", help="List any Lines you do not wish to view.", nargs='*')
    parser.add_argument("-p","--Direction", help="Direction filter for services.", choices=['inbound','outbound','both'],default='both')
    parser.add_argument("-w", "--WarningTime", help="How soon to show train approaching warning.", type=float, default=0.2)
    parser.add_argument("-wd", "--WarningDuration", help="Duration in seconds to show warning message", type=int, default=5)
    parser.add_argument('--no-splashscreen', dest='SplashScreen', action='store_false',help="Hide splash screen at startup.")
    parser.add_argument('--Warning', dest='warning', action='store_true', help="Enable approaching train warnings", default=False)
    parser.add_argument("--Display", default="ssd1322", choices=['ssd1322','pygame','capture','gifanim'], help="Display type selection")
    parser.add_argument("--max-frames", default=60,dest='maxframes', type=check_positive, help="Maximum frames for gifanim")
    parser.add_argument("--no-console-output",dest='NoConsole', action='store_true', help="Disable console output")
    parser.add_argument("--filename",dest='filename', default="output.gif", help="Output filename for gifanim")

    # Required parameters
    required = parser.add_argument_group('required named arguments')
    required.add_argument("-k","--APIKey", help="Your Transport for London API Key", type=str, required=True)
    required.add_argument("-s","--StationID", help="The London Underground station code", type=str, required=True)

    return parser.parse_args()