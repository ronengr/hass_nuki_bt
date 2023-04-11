import asyncio
import datetime
import hashlib
import logging
import hmac
import time
from asyncio import CancelledError, TimeoutError
from typing import Callable

import async_timeout

# from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS

from fastcrc import crc16
import nacl.utils
import nacl.secret
from nacl.bindings.crypto_box import crypto_box_beforenm
from bleak import BleakScanner, BleakClient, BleakError
from bleak.exc import BleakDBusError

from .const import NukiErrorException, NukiLockConst, NukiOpenerConst, NukiConst

logger = logging.getLogger(__name__)


class NukiDevice:
    def __init__(
        self,
        address,
        auth_id,
        nuki_public_key,
        bridge_public_key,
        bridge_private_key,
        ble_device,
        app_id=None,
        model=None,
        name="RaspiNukiBridge",
    ):
        self.address = address
        self.auth_id = auth_id
        self.nuki_public_key = nuki_public_key
        self.bridge_public_key = bridge_public_key
        self.bridge_private_key = bridge_private_key
        self.app_id = app_id
        self.id = None
        self.name = None
        self.username = None
        self.rssi = None
        self.last_state = None
        self.config = {}
        self._poll_needed = False
        self.last_action_status = None

        self.name = name
        self._device_type = None
        self._pairing_handle = None
        self._client = None
        self._expected_response: NukiConst.NukiCommand = None
        self._pairing_callback = None
        self.retry = 5
        self.connection_timeout = 30
        self.command_timeout = 30
        self.command_response_timeout = 10

        self._send_cmd_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        self._operation_lock = asyncio.Lock()
        self._update_state_lock = asyncio.Lock()
        self._update_config_lock = asyncio.Lock()

        self._callbacks = []

        if nuki_public_key and bridge_private_key:
            self._create_shared_key()

        self._last_ibeacon = None
        if model:
            self.device_type = model

        self.set_ble_device(ble_device)

    def parse_advertisement_data(self, device, advertisement_data):
        if device.address == self.address:
            manufacturer_data = advertisement_data.manufacturer_data.get(76, None)
            if manufacturer_data is None:
                logger.info(
                    f"No manufacturer_data (76) in advertisement_data: {advertisement_data}"
                )
                return
            if manufacturer_data[0] != 0x02:
                # Ignore HomeKit advertisement
                return
            logger.info(f"Nuki: {device.address}, RSSI: {advertisement_data.rssi}")
            tx_p = manufacturer_data[-1]
            if self.just_got_beacon:
                logger.info(f"Ignoring duplicate beacon from Nuki {device.address}")
                return
            self.set_ble_device(device)
            self.rssi = advertisement_data.rssi
            if not self.last_state or tx_p & 0x1:
                self._poll_needed = True
            return

    def poll_needed(self, seconds_since_last_poll):
        return self._poll_needed

    @property
    def just_got_beacon(self):
        if self._last_ibeacon is None:
            self._last_ibeacon = time.time()
            return False
        seen_recently = time.time() - self._last_ibeacon <= 1
        if not seen_recently:
            self._last_ibeacon = time.time()
        return seen_recently

    @property
    def device_type(self):
        return self._device_type

    @device_type.setter
    def device_type(self, device_type: NukiConst.NukiDeviceType):
        if device_type == NukiConst.NukiDeviceType.OPENER:
            self._const = NukiOpenerConst
        else:
            self._const = NukiLockConst
        self._device_type = device_type
        logger.info(f"Device type: {self.device_type}")

    def _create_shared_key(self):
        self._shared_key = crypto_box_beforenm(
            self.nuki_public_key, self.bridge_private_key
        )
        self._box = nacl.secret.SecretBox(self._shared_key)

    @property
    def is_battery_critical(self):
        return bool(self.last_state["critical_battery_state"] & 1)

    @property
    def is_battery_charging(self):
        return bool(self.last_state["critical_battery_state"] & 2)

    @property
    def battery_percentage(self):
        return ((self.last_state["critical_battery_state"] & 252) >> 2) * 2

    @property
    def keyturner_state(self):
        return self.last_state

    def get_keyturner_state(self):
        return self.last_state

    def get_config(self):
        return self.config

    @staticmethod
    def _prepare_command(cmd: NukiConst.NukiCommand, payload=bytes()):
        message = NukiConst.NukiCommand.build(cmd) + payload
        crc = crc16.xmodem(message, 0xFFFF).to_bytes(2, "little")
        message += crc
        return message

    def _encrypt_command(self, cmd: NukiConst.NukiCommand, payload=bytes()):
        unencrypted = self.auth_id + self._prepare_command(cmd, payload)[:-2]
        crc = crc16.xmodem(unencrypted, 0xFFFF).to_bytes(2, "little")
        unencrypted += crc
        nonce = nacl.utils.random(24)
        encrypted = self._box.encrypt(unencrypted, nonce)[24:]
        length = len(encrypted).to_bytes(2, "little")
        message = nonce + self.auth_id + length + encrypted
        return message

    def _decrypt_message(self, data):
        msg = self._const.NukiEncryptedMessage.parse(data)
        decrypted = self._box.decrypt(msg.nonce + msg.encrypted)
        return decrypted

    def _parse_message(self, data):
        return self._const.NukiMessage.parse(data)

    def _fire_callbacks(self) -> None:
        """Fire callbacks."""
        logger.debug("%s: Fire callbacks", self.name)
        for callback in self._callbacks:
            callback()

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Subscribe to device notifications."""
        self._callbacks.append(callback)

        def _unsub() -> None:
            """Unsubscribe from device notifications."""
            self._callbacks.remove(callback)

        return _unsub

    def set_ble_device(self, ble_device, advertisement_data=None):
        if not self._client:
            self._client = BleakClient(ble_device, timeout=self.connection_timeout)
            if not self.device_type and advertisement_data:
                if NukiOpenerConst.BLE_PAIRING_CHAR in advertisement_data.service_uuids:
                    self.device_type = NukiConst.NukiDeviceType.OPENER
                else:
                    self.device_type = NukiConst.NukiDeviceType.SMARTLOCK_1_2

        return self._client

    async def _notification_handler(self, sender, data):
        logger.debug(f"Notification handler: {sender}, data: {data}")
        if (
            self._client.services[self._const.BLE_PAIRING_CHAR]
            and sender == self._client.services[self._const.BLE_PAIRING_CHAR].handle
        ):
            # The pairing handler is not encrypted
            msg = self._parse_message(bytes(data))
        else:
            msg = self._parse_message(self._decrypt_message(bytes(data)))

        if msg.command == self._const.NukiCommand.ERROR_REPORT:
            if msg.payload.error_code == self._const.ErrorCode.P_ERROR_NOT_PAIRING:
                logger.error(
                    f"********************************************************************"
                )
                logger.error(
                    f"*                                                                  *"
                )
                logger.error(
                    f"*                            UNPAIRED!                             *"
                )
                logger.error(
                    f"*    Put Nuki in pairing mode by pressing the button 6 seconds     *"
                )
                logger.error(
                    f"*                         Then try again                           *"
                )
                logger.error(
                    f"*                                                                  *"
                )
                logger.error(
                    f"********************************************************************"
                )
                exit(0)
            else:
                logger.error(
                    f"Error {msg.payload.error_code}, command {msg.payload.command_identifier}"
                )
            ex = NukiErrorException(
                error_code=msg.payload.error_code,
                command=msg.payload.command_identifier,
            )
            if self._notify_future and not self._notify_future.done():
                self._notify_future.set_exception(ex)
                return
            else:
                raise ex

        elif msg.command == self._const.NukiCommand.STATUS:
            logger.info(f"Last action: {msg.payload.status}")
            self.last_action_status = msg.payload.status

        if self._notify_future and not self._notify_future.done():
            if msg.command == self._expected_response:
                self._notify_future.set_result(msg)
                return

        if msg.command == self._const.NukiCommand.KEYTURNER_STATES:
            update_config = not self.config or (
                self.last_state["config_update_count"]
                != msg.payload["config_update_count"]
            )
            if update_config:
                # todo: update config directly?
                self.poll_needed = True
        elif msg.command != self._const.NukiCommand.STATUS:
            logger.error("%s: Received unsolicited notification: %s", self.name, msg)
            logger.error("was expecting %s", self._expected_response)

    async def _send_command(
        self, characteristic, command, expected_response: NukiConst.NukiCommand = None
    ):
        async with self._send_cmd_lock:
            self._notify_future = asyncio.Future()
            self._expected_response = expected_response
            msg = None

            # Sometimes the connection to the smartlock fails, retry 3 times
            _characteristic = characteristic
            for i in range(1, self.retry + 1):
                logger.info(f"Trying to send data. Attempt {i}")
                try:
                    await self.connect()
                    if _characteristic is None:
                        _characteristic = self._const.BLE_CHAR
                    logger.info(f"Sending data to Nuki")
                    await self._client.write_gatt_char(_characteristic, command)
                except (TimeoutError, CancelledError):
                    logger.error(f"Timeout while sending data on attempt {i}")
                    await asyncio.sleep(0.2)
                except BleakDBusError as ex:
                    logger.error(f"DBus Error {ex}")
                    await asyncio.sleep(0.2)
                # except BLEAK_RETRY_EXCEPTIONS as ex:
                #     logger.error(f'Bleak retry error {ex}')
                #     await asyncio.sleep(0.2)
                except BleakError as exc:
                    logger.error(f"Bleak Error while sending data on attempt {i}")
                    logger.exception(exc)
                    await asyncio.sleep(0.7)
                except Exception as exc:
                    logger.error(f"Error while sending data on attempt {i}")
                    logger.exception(exc)
                    await asyncio.sleep(0.2)
                else:
                    logger.info(f"Data sent on attempt {i}")
                    break
        if expected_response:
            async with async_timeout.timeout(self.command_response_timeout):
                msg = await self._notify_future
        self._notify_future = None
        self._expected_response = None
        return msg

    async def _safe_start_notify(self, *args):
        try:
            await self._client.start_notify(*args)
        # This exception might occur due to Bluez downgrade required for Pi 3B+ and Pi 4. See this comment:
        # https://github.com/dauden1184/RaspiNukiBridge/issues/1#issuecomment-1103969957
        # Haven't researched further the reason and consequences of this exception
        except EOFError:
            logger.info("EOFError during notification")

    async def connect(self):
        async with self._connect_lock:
            if not self._client:
                self._client = BleakClient(
                    self.address, timeout=self.connection_timeout
                )
            if self._client.is_connected:
                logger.info("Connected")
                return
            await self._client.connect()
            logger.debug(f"Services {[str(s) for s in self._client.services]}")
            logger.debug(
                f"Characteristics {[str(v) for v in self._client.services.characteristics.values()]}"
            )
            if not self.device_type:
                services = self._client.services
                if services.get_characteristic(NukiOpenerConst.BLE_PAIRING_CHAR):
                    self.device_type = NukiConst.NukiDeviceType.OPENER
                else:
                    self.device_type = NukiConst.SMARTLOCK_1_2
            await self._safe_start_notify(
                self._const.BLE_PAIRING_CHAR, self._notification_handler
            )
            await self._safe_start_notify(
                self._const.BLE_CHAR, self._notification_handler
            )
            logger.info("Connected")

    async def disconnect(self):
        if self._client and self._client.is_connected:
            logger.info(f"Nuki disconnecting...")
            try:
                await self._client.disconnect()
                logger.info("Nuki disconnected")
            except Exception as e:
                logger.error(f"Error while disconnecting")
                logger.exception(e)

    async def update_state(self):
        logger.info("Querying Nuki state")
        if self._update_state_lock.locked():
            logger.info("update state already in progress. ignoring")
            return
        async with self._update_state_lock, self._operation_lock:
            payload = self._const.NukiCommand.build(
                self._const.NukiCommand.KEYTURNER_STATES
            )
            cmd = self._encrypt_command(self._const.NukiCommand.REQUEST_DATA, payload)
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.KEYTURNER_STATES
            )
            update_config = not self.config or (
                self.last_state["config_update_count"]
                != msg.payload["config_update_count"]
            )
            self.last_state = msg.payload
            logger.debug(f"State: {self.last_state}")
            self._poll_needed = False
        if update_config:
            await self.update_config()
        self._fire_callbacks()

    async def lock(self):
        return await self.lock_action(
            self._const.LockAction.LOCK, self._const.LockState.LOCKING
        )

    async def unlock(self):
        return await self.lock_action(
            self._const.LockAction.UNLOCK, self._const.LockState.UNLOCKING
        )

    async def unlatch(self):
        return await self.lock_action(
            self._const.LockAction.UNLATCH, self._const.LockState.UNLATCHING
        )

    async def lock_action(
        self, action: NukiConst.LockAction, new_lock_state: NukiConst.LockState = None
    ):
        logger.info(f"Lock action {action}")
        async with self._operation_lock:
            payload = self._const.NukiCommand.build(self._const.NukiCommand.CHALLENGE)
            cmd = self._encrypt_command(self._const.NukiCommand.REQUEST_DATA, payload)
            if new_lock_state:
                self.last_state["lock_state"] = new_lock_state
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.CHALLENGE
            )
            payload = self._const.NukiLockActionMsg.build(
                {
                    "lock_action": action,
                    "app_id": self.app_id,
                    "flags": 0,
                    "name_suffix": self.username,
                    "nonce": msg.payload.nonce,
                }
            )
            cmd = self._encrypt_command(self._const.NukiCommand.LOCK_ACTION, payload)
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.STATUS
            )
            logger.info(f"{msg.payload.status}")
        return msg.payload

    async def update_config(self):
        logger.info("Retrieve nuki configuration")
        if self._update_config_lock.locked():
            logger.info("get config already in progress")
            return
        async with self._operation_lock, self._update_config_lock:
            payload = self._const.NukiCommand.build(self._const.NukiCommand.CHALLENGE)
            cmd = self._encrypt_command(self._const.NukiCommand.REQUEST_DATA, payload)
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.CHALLENGE
            )
            cmd = self._encrypt_command(
                self._const.NukiCommand.REQUEST_CONFIG, msg.payload["nonce"]
            )
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.CONFIG
            )
            self.config = msg.payload
            logger.debug(f"Config: {self.config}")

    async def pair(self, callback):
        async with self._operation_lock:
            self._pairing_callback = callback
            payload = self._const.NukiCommand.build(self._const.NukiCommand.PUBLIC_KEY)
            cmd = self._prepare_command(self._const.NukiCommand.REQUEST_DATA, payload)
            msg = await self._send_command(
                self._const.BLE_PAIRING_CHAR, cmd, self._const.NukiCommand.PUBLIC_KEY
            )
            self.nuki_public_key = msg.payload["public_key"]
            self._create_shared_key()
            logger.info(f"Nuki {self.address} public key: {self.nuki_public_key.hex()}")
            cmd = self._prepare_command(
                self._const.NukiCommand.PUBLIC_KEY, self.bridge_public_key
            )
            msg = await self._send_command(
                self._const.BLE_PAIRING_CHAR, cmd, self._const.NukiCommand.CHALLENGE
            )
            value_r = (
                self.bridge_public_key + self.nuki_public_key + msg.payload["nonce"]
            )
            payload = hmac.new(
                self._shared_key, msg=value_r, digestmod=hashlib.sha256
            ).digest()
            cmd = self._prepare_command(
                self._const.NukiCommand.AUTH_AUTHENTICATOR, payload
            )
            msg = await self._send_command(
                self._const.BLE_PAIRING_CHAR, cmd, self._const.NukiCommand.CHALLENGE
            )
            app_id = self.app_id.to_bytes(4, "little")
            # todo: use type variable
            type_id = self._const.NukiClientType.build(
                self._const.NukiClientType.BRIDGE
            )
            name = self.name.encode("utf-8").ljust(32, b"\0")
            nonce = nacl.utils.random(32)
            value_r = type_id + app_id + name + nonce + msg.payload["nonce"]
            payload = hmac.new(
                self._shared_key, msg=value_r, digestmod=hashlib.sha256
            ).digest()
            payload += type_id + app_id + name + nonce
            cmd = self._prepare_command(self._const.NukiCommand.AUTH_DATA, payload)
            msg = await self._send_command(
                self._const.BLE_PAIRING_CHAR,
                cmd,
                self._const.NukiCommand.AUTHORIZATION_ID,
            )
            self.auth_id = msg.payload["auth_id"]
            value_r = self.auth_id + msg.payload["nonce"]
            payload = hmac.new(
                self._shared_key, msg=value_r, digestmod=hashlib.sha256
            ).digest()
            payload += self.auth_id
            cmd = self._prepare_command(
                self._const.NukiCommand.AUTH_ID_CONFIRM, payload
            )
            msg = await self._send_command(
                self._const.BLE_PAIRING_CHAR, cmd, self._const.NukiCommand.STATUS
            )
            if self._pairing_callback:
                self._pairing_callback(self)
                self._pairing_callback = None

    async def verify_pin(self, pin):
        logger.info(f"verify PIN {pin}")
        async with self._operation_lock:
            payload = self._const.NukiCommand.build(self._const.NukiCommand.CHALLENGE)
            cmd = self._encrypt_command(self._const.NukiCommand.REQUEST_DATA, payload)
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.CHALLENGE
            )
            payload = self._const.VerifySecurityPin.build(
                {"nonce": msg.payload["nonce"], "security_pin": pin}
            )
            cmd = self._encrypt_command(
                self._const.NukiCommand.VERIFY_SECURITY_PIN, payload
            )
            try:
                msg = await self._send_command(
                    self._const.BLE_CHAR, cmd, self._const.NukiCommand.STATUS
                )
            except NukiErrorException as ex:
                if ex.error_code == self._const.ErrorCode.K_ERROR_BAD_PIN:
                    return False
                else:
                    raise
            return (
                msg.command == self._const.NukiCommand.STATUS
                and msg.payload.status == self._const.StatusCode.COMPLETED
            )

    async def request_last_log_entry(self, pin):
        logger.info(f"request last log entry")
        async with self._operation_lock:
            payload = self._const.NukiCommand.build(self._const.NukiCommand.CHALLENGE)
            cmd = self._encrypt_command(self._const.NukiCommand.REQUEST_DATA, payload)
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.CHALLENGE
            )
            payload = self._const.RequestLogEntries.build(
                {
                    "start_index": 0,
                    "count": 1,
                    "sort_order": 0x01,
                    "total_count": 0,
                    "nonce": msg.payload.nonce,
                    "security_pin": pin,
                }
            )
            cmd = self._encrypt_command(
                self._const.NukiCommand.REQUEST_LOG_ENTRIES, payload
            )
            msg = await self._send_command(
                self._const.BLE_CHAR, cmd, self._const.NukiCommand.LOG_ENTRY
            )
            logger.debug(msg.payload)
        return msg.payload
