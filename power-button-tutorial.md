# Raspberry Pi Power Button Setup Guide

This guide explains how to set up a latching power button for Raspberry Pi, specifically using a button with LED ring. The button will:
- First press (button down): Power on the Pi
- Button stays down during normal operation
- Second press (button releases): Triggers a safe shutdown

## Hardware Requirements

- Raspberry Pi (tested on Pi Zero W)
- [Rugged Metal On/Off Switch with White LED Ring](https://thepihut.com/products/rugged-metal-on-off-switch-with-white-led-ring?variant=27740538129)
- Jumper wires

## Wiring

| Button Pin | RPi Pin     | Description |
|------------|-------------|-------------|
| CO         | Pin 6 or 9  | Common ground for button |
| NO         | Pin 5       | Required for power on |
| NO         | Pin 13      | Button signal for shutdown |
| LED +      | Pin 1       | Power for LED |
| LED -      | Pin 29      | LED control |

## Software Configuration

### 1. Configure GPIO Shutdown and LED

Add these lines to `/boot/firmware/config.txt` (or `/boot/config.txt` on older systems):
```
# Shutdown configuration
dtoverlay=gpio-shutdown,gpio_pin=27,active_low=0,gpio_pull=up

# LED configuration
gpio=5=op,dl
```

### 2. Reboot to Apply Changes
```bash
sudo reboot
```

## Button Behavior

2. **Power On**:
   - Press button (it latches down)
   - Pi starts booting
   - LED turns on
   - Button remains down during operation

3. **Shutdown**:
   - Press button again (it releases up)
   - System performs safe shutdown
   - LED turns off
   - Pi powers off
