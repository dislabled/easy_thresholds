# Easy Thresholds

A Home Assistant integration for monitoring sensor values against configurable thresholds and triggering alarms when values exceed defined limits.

## Features

- Monitor numeric sensors against four threshold levels (critical low, warning low, warning high, critical high)
- Automatic or manual alarm resolution
- Persistent notifications when alarms are triggered
- Service to manually clear alarms
- Support for multiple sensors per installation
- Configuration via Home Assistant UI

## Installation

### Via HACS

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the menu (three dots) and select "Custom repositories"
4. Add the repository URL with category "Integration"
5. Click Install
6. Restart Home Assistant

### Manual Installation

1. Clone or download this repository
2. Copy the `easy_thresholds` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

Easy Thresholds is configured via the Home Assistant UI.

1. Go to Settings → Devices & Services → Integrations
2. Click Create Integration
3. Search for "Easy Thresholds"
4. Select a numeric sensor to monitor
5. Configure the four threshold values:
   - **s-- (Critical Low)**: Threshold below warning low
   - **s- (Warning Low)**: Safe range starts here
   - **s+ (Warning High)**: Safe range ends here
   - **s++ (Critical High)**: Threshold above warning high
6. Select which thresholds should trigger alarms
7. Choose resolution mode (automatic or manual)

### Resolution Modes

- **Automatic**: Alarms clear automatically when the sensor returns to the safe range
- **Manual**: Alarms require manual acknowledgment via the `clear_alarm` service

## Services

### clear_alarm

Manually clear an alarm by name.

Service: `easy_thresholds.clear_alarm`

Parameters:
- `alarm_name` (string, required): The name of the alarm to clear

Example:
```yaml
service: easy_thresholds.clear_alarm
data:
  alarm_name: sensor.temperature_s-
```

## Entities

The integration creates a sensor entity that tracks active alarms.

**Entity**: `sensor.easy_thresholds`

**State**: Number of active alarms

**Attributes**:
- `active_alarms`: List of currently active alarms with timestamps and threshold information

### Roadmap

- [ ] Binary sensor support for triggering alarms on simple on/off conditions
- [ ] Per-sensor notification control (choose between persistent notifications or integration-only tracking)
- [ ] Custom hysteresis values per sensor to prevent alarm oscillation near thresholds
- [ ] Entity validation to detect and warn about removed sensors
- [ ] Service re-registration on configuration entry updates
