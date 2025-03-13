# UPS HAT Setup Guide

This guide explains how to set up a UPS (Uninterruptible Power Supply) HAT for Raspberry Pi Zero, providing battery backup and safe shutdown capabilities.

## Hardware Requirements

- [UPS HAT for Raspberry Pi Zero](https://thepihut.com/products/uninterruptible-power-supply-ups-hat-for-raspberry-pi-zero)

## Installation

### Physical Setup

1. **IMPORTANT**: Ensure power switch is OFF before connecting battery
2. Connect the Li-po battery to the battery header (PH2.0-2P connector)
3. Mount the HAT onto Raspberry Pi Zero using pogo pins
4. Secure with mounting screws
5. Connect Micro USB for initial charging

### Software Configuration

1. Enable I2C interface:
```bash
sudo raspi-config
# Navigate to: Interfacing Options > I2C > Enable
sudo reboot
```

2. Install i2c-tools to verify UPS HAT connection:
```bash
sudo apt-get update
sudo apt-get install -y python3-smbus i2c-tools
```

3. Download and run INA219.py to monitor battery status:
```bash
wget https://files.waveshare.com/upload/4/40/UPS_HAT_C.7z
7zr x UPS_HAT_C.7z -r -o./
cd UPS_HAT_C
python3 INA219.py
```

## Usage

- Power switch controls battery power to Pi
- Charging LED: ON while charging, OFF when fully charged
- Use INA219.py to check battery status:
  - Negative current: Battery powering Pi
  - Positive current: Battery charging

## Safety Notes

- Only use compatible 3.7V Li-po batteries
- Turn OFF before connecting/disconnecting battery
- Initial charging required to activate protection circuit
- Replace battery after 2 years or max cycle life
- Keep away from heat and flammable materials
- Maximum output current: 1.8A (when fully charged)

## Troubleshooting

### No Power After Battery Connection
1. Charge battery for 10-15 minutes to activate protection circuit
2. Ensure switch is in ON position
3. Check pogo pin connections

### I2C Communication Issues
Verify I2C connection:
```bash
sudo i2cdetect -y 1
# Should show device at address 0x43
```

### System Rebooting
- Ensure battery is sufficiently charged
- Check for excessive power draw from additional devices
- Current limit is 1.8A when fully charged, decreases with battery level

For more detailed information, refer to the [official UPS HAT documentation](https://www.waveshare.com/wiki/UPS_HAT_(C))