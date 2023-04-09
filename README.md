# Nuki BT

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

[![Community Forum][forum-shield]][forum]

Nuki lock integration for Home Asistance.
This integration communicates directly with Nuki over Bluetooth. No need for bridge.


## Background
- This is based on [RaspiNukiBridge](https://github.com/regevbr/RaspiNukiBridge) by [dauden1184](https://github.com/dauden1184/) and [regevbr](https://github.com/regevbr)
- This is heavily inspired by [kvj](https://github.com/kvj)'s [hass_nuki_ng](https://github.com/kvj/hass_nuki_ng) and [technyon](https://github.com/technyon)'s [nuki_hub](https://github.com/technyon/nuki_hub)

## Setup

{% if not installed %}

### Installation:
* Go to HACS -> Integrations
* Click the three dots on the top right and select `Custom Repositories`
* Enter `https://github.com/ronengr/hass_nuki_bt` as repository, select the category `Integration` and click Add
* A new custom integration shows up for installation (Nuki BT) - install it
* Restart Home Assistant

{% endif %}

### Configuration:
* Go to Settings -> Devices & Services
* The integration should automatically discover you Nuki lock. You Should see a new Discovered Device, just click on "Configure" to configure it.
  * If no look was discovered, and you know the Nuki's BT address, you can try to add it manually by clicking on "Add Integration"
* Select a Device Name and Client Type
* Enable pairing mode on the Nuki lock by holding down the button on the Nuki Smart Lock for 5 seconds until the LED ring is permanently glowing.
* Select "Pair device automatically"
  * It is possible to configure the device manually, if you have the pairing-information from an already paired device.
    Use this option only if you know what you are doing. This is mostly ment for development.

#### Client Type:
hass_nuki_bt can connect to the Nuki lock in 2 ways:
  * "Bridge" is the recommended way. This will cause the current Bridge to be unregistered when pairing.
  * "App" will allow you to run hass_nuki_bt alongside a Nuki Bridge, but can lead to either device missing updates.


## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[hass_nuki_bt]: https://github.com/ronengr/hass_nuki_bt
[commits-shield]: https://img.shields.io/github/commit-activity/y/ronengr/hass_nuki_bt.svg?style=for-the-badge
[commits]: https://github.com/ronengr/hass_nuki_bt/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/ronengr/hass_nuki_bt.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%20%40ronengr-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/ronengr/hass_nuki_bt.svg?style=for-the-badge
[releases]: https://github.com/ronengr/hass_nuki_bt/releases
