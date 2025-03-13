# Raspberry Pi OLED Display Setup Guide

This guide explains how to set up a 3.2-inch OLED display with a Raspberry Pi Zero 2W.

## Hardware Requirements

- Raspberry Pi Zero 2W
- [3.2-inch Yellow OLED Display Module (256x64)](https://www.buydisplay.com/yellow-3-2-inch-arduino-raspberry-pi-oled-display-module-256x64-spi)

### Display Connection Options
- **4-Wire SPI (Requires Soldering)**
- **Pin Header Connection-4-Wired SPI (No Soldering Required, Use Jumper Wires)**

## Wiring

### Detailed Pin Connection

| Pi Zero Pin Number | OLED Display Pin Number | Description |
|-------------------|------------------------|-------------|
| 2                 | 2                      | VCC Power   |
| 6, 9, 14, 20, 25, 30, 34, 39 | 1, 7, 8, 9, 10, 11, 12, 13 | Ground Connections |
| 18                | 14                     | Additional Pin |
| 19                | 5                      | SPI MOSI    |
| 22                | 15                     | Additional Pin |
| 23                | 4                      | SPI SCK     |
| 24                | 16                     | Additional Pin |

**IMPORTANT:** Take extra care to ensure correct wiring orientation to prevent permanent damage to the display or Pi.

## Software Configuration

### 1. Operating System Preparation
First, install Raspberry Pi OS Lite (64-bit) using Raspberry Pi Imager:
- Select Raspberry Pi Zero 2W
- Choose Raspberry Pi OS Lite (64-bit)
- Configure settings:
  - Set hostname to "raspberrypi"
  - Enable SSH
  - Set username to "display"
  - Configure Wi-Fi
  - Set locale to Europe/London

### 2. Enable SPI Interface

After booting and logging in via SSH, open configuration:
```bash
sudo raspi-config
```

Navigate to:
- Interfacing Options
- Enable SPI (I3 SPI or P4 SPI or I4 SPIR)

### 3. Update System

Update and upgrade your system:
```bash
sudo apt update -y
sudo apt full-upgrade -y
```

### 4. Safe Shutdown
To safely shutdown before wiring:
```bash
sudo shutdown -h now
```

## Additional Notes
- Do not wire the display while the Pi is powered on
- Double-check all connections before powering up
- If using a headerless display/Pi, soldering may be required

## Troubleshooting
- Verify all pin connections match the provided diagram
- Ensure correct orientation of display and Pi
- Check for any loose connections
