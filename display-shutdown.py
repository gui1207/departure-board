from luma.core import cmdline
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

parser = cmdline.create_parser(description='Display Shutdown')
args = parser.parse_args(['--display', 'ssd1322', '--interface', 'spi', '--width', '256'])

device = cmdline.create_device(args)
device.clear()
device.hide()