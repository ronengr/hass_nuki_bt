"""Constants for hass_nuki_bt."""
from logging import Logger, getLogger

from construct import Bit, BitStruct, Optional, Padding, Struct, Byte, Enum, Int8ul, Int16ul, Int32ul, Int8sl, Int16sl, Float32l, PaddedString, Bytes, Switch, this
import functools

LOGGER: Logger = getLogger(__package__)

NAME = "Nuki BT"
DOMAIN = "hass_nuki_bt"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

# config
CONF_DEVICE_ADDRESS = "device_address"
CONF_AUTH_ID = "auth_id"
CONF_PRIVATE_KEY = "private_key"
CONF_PUBLIC_KEY = "public_key"
CONF_DEVICE_PUBLIC_KEY = "device_public_key"
CONF_APP_ID = "app_id"

class NukiConst:
    ErrorCode = Enum(Int8ul,
        #General error codes
        ERROR_BAD_CRC = 0xFD, #CRC of received command is invalid
        ERROR_BAD_LENGTH = 0xFE, #Length of retrieved command payload does not match expected length
        ERROR_UNKNOWN = 0xFF, #Used if no other error code matche

        #Pairing service error codes
        P_ERROR_NOT_PAIRING = 0x10, #Returned if public key is being requested via request data command, but the Smart Lock is not in pairing mode
        P_ERROR_BAD_AUTHENTICATOR = 0x11, #Returned if the received authenticator does not match the own calculated authenticator
        P_ERROR_BAD_PARAMETER = 0x12, #Returned if a provided parameter is outside of its valid range
        P_ERROR_MAX_USER = 0x13, #Returned if the maximum number of users has been reached

        #Keyturner service error codes
        K_ERROR_NOT_AUTHORIZED = 0x20, #Returned if the provided authorization id is invalid or the payload could not be decrypted using the shared key for this authorization id
        K_ERROR_BAD_PIN = 0x21, #Returned if the provided pin does not match the stored one.
        K_ERROR_BAD_NONCE = 0x22, #Returned if the provided nonce does not match the last stored one of this authorization id or has already been used before.
        K_ERROR_BAD_PARAMETER = 0x23, #Returned if a provided parameter is outside of its valid range.
        K_ERROR_INVALID_AUTH_ID = 0x24, #Returned if the desired authorization id could not be deleted because it does not exist.
        K_ERROR_DISABLED = 0x25, #Returned if the provided authorization id is currently disabled.
        K_ERROR_REMOTE_NOT_ALLOWED = 0x26, #Returned if the request has been forwarded by the Nuki Bridge and the provided authorization id has not been granted remote access.
        K_ERROR_TIME_NOT_ALLOWED = 0x27, #Returned if the provided authorization id has not been granted access at the current time.
        K_ERROR_TOO_MANY_PIN_ATTEMPTS = 0x28, #Returned if an invalid pin has been provided too often
        K_ERROR_TOO_MANY_ENTRIES = 0x29, #Returned if no more entries can be stored
        K_ERROR_CODE_ALREADY_EXISTS = 0x2A, #Returned if a Keypad Code should be added but the given code already exists.
        K_ERROR_CODE_INVALID = 0x2B, #Returned if a Keypad Code that has been entered is invalid.
        K_ERROR_CODE_INVALID_TIMEOUT_1 = 0x2C, #Returned if an invalid pin has been provided multiple times.
        K_ERROR_CODE_INVALID_TIMEOUT_2 = 0x2D, #Returned if an invalid pin has been provided multiple times.
        K_ERROR_CODE_INVALID_TIMEOUT_3 = 0x2E, #Returned if an invalid pin has been provided multiple times.
        K_ERROR_AUTO_UNLOCK_TOO_RECENT = 0x40, #Returned on an incoming auto unlock request and if a lock action has already been executed within short time.
        K_ERROR_POSITION_UNKNOWN = 0x41, #Returned on an incoming unlock request if the request has been forwarded by the Nuki Bridge and the Smart Lock is unsure about its actual lock position.
        K_ERROR_MOTOR_BLOCKED = 0x42, #Returned if the motor blocks.
        K_ERROR_CLUTCH_FAILURE = 0x43, #Returned if there is a problem with the clutch during motor movement.
        K_ERROR_MOTOR_TIMEOUT = 0x44, #Returned if the motor moves for a given period of time but did not block.
        K_ERROR_BUSY = 0x45, #Returned on any lock action via bluetooth if there is already a lock action processing.
        K_ERROR_CANCELED = 0x46, #Returned on any lock action or during calibration if the user canceled the motor movement by pressing the button
        K_ERROR_NOT_CALIBRATED = 0x47, #Returned on any lock action if the Smart Lock has not yet been calibrated
        K_ERROR_MOTOR_POSITION_LIMIT = 0x48, #Returned during calibration if the internal position database is not able to store any more values
        K_ERROR_MOTOR_LOW_VOLTAGE = 0x49, #Returned if the motor blocks because of low voltage.
        K_ERROR_MOTOR_POWER_FAILURE = 0x4A, #Returned if the power drain during motor movement is zero
        K_ERROR_CLUTCH_POWER_FAILURE = 0x4B, #Returned if the power drain during clutch movement is zero
        K_ERROR_VOLTAGE_TOO_LOW = 0x4C, #Returned on a calibration request if the battery voltage is too low and a calibration will therefore not be started
        K_ERROR_FIRMWARE_UPDATE_NEEDED = 0x4D, #Returned during any motor action if a firmware update is mandatory
    )

    BridgeType = Enum(Byte,
        HW = 1,
        SW = 2,
    )

    NukiDeviceType = Enum(Byte,
        SMARTLOCK_1_2 = 0,
        OPENER = 2,
        SMARTDOOR = 3,
        SMARTLOCK_3 = 4,
    )

    StatusCode = Enum(Int8ul,
        COMPLETED = 0x0,
        ACCEPTED = 0x1,
    )

    DoorsensorState = Enum(Int8ul,
        UNAVAILABLE = 0x00,
        DEACTIVATED = 0x01,
        DOOR_CLOSED = 0x02,
        DOOR_OPENED = 0x03,
        DOOR_STATE_UNKOWN = 0x04,
        CALIBRATING = 0x05,
        UNCALIBRATED = 0x16,
        REMOVED = 0x240,
        UNKOWN = 0x255,
    )

    LockActionCompletionStatus = Enum(Int8ul,
        SUCCESS = 0x00,
        MOTOR_BLOCKED = 0x01,
        CANCELED = 0x02,
        TOO_RECENT = 0x03,
        BUSY = 0x04,
        LOW_MOTOR_VOLTAGE = 0x05,
        CLUTCH_FAILURE = 0x06,
        MOTOR_POWER_FAILURE = 0x07,
        INCOMPLETE = 0x08,
        OTHER_ERROR = 0xFE,
        UNKNOWN = 0xFF,
    )

    NukiCommand = Enum(Int16ul,
        EMPTY                         = 0x0000,
        REQUEST_DATA                  = 0x0001,
        PUBLIC_KEY                    = 0x0003,
        CHALLENGE                     = 0x0004,
        AUTHORIZATION_AUTHENTICATOR   = 0x0005,
        AUTHORIZATION_DATA            = 0x0006,
        AUTHORIZATION_ID              = 0x0007,
        REMOVE_USER_AUTHORIZATION     = 0x0008,
        REQUEST_AUTHORIZATION_ENTRIES = 0x0009,
        AUTHORIZATION_ENTRY           = 0x000A,
        AUTHORIZATION_DAT_INVITE      = 0x000B,
        KEYTURNER_STATES              = 0x000C,
        LOCK_ACTION                   = 0x000D,
        STATUS                        = 0x000E,
        MOST_RECENT_COMMAND           = 0x000F,
        OPENINGS_CLOSINGS_SUMMARY     = 0x0010,  # Lock only (+ NUKI v1 only)
        BATTERY_REPORT                = 0x0011,
        ERROR_REPORT                  = 0x0012,
        SET_CONFIG                    = 0x0013,
        REQUEST_CONFIG                = 0x0014,
        CONFIG                        = 0x0015,
        SET_SECURITY_PIN              = 0x0019,
        REQUEST_CALIBRATION           = 0x001A, # SetCalibrated for Opener
        REQUEST_REBOOT                = 0x001D,
        AUTHORIZATION_ID_CONFIRMATION = 0x001E,
        AUTHORIZATION_ID_INVITE       = 0x001F,
        VERIFY_SECURITY_PIN           = 0x0020,
        UPDATE_TIME                   = 0x0021,
        UPDATE_AUTHORIZATION          = 0x0025,
        AUTHORIZATION_ENTRY_COUNT     = 0x0027,
        START_BUS_SIGNAL_RECORDING    = 0x002F, # Opener only
        REQUEST_LOG_ENTRIES           = 0x0031,
        LOG_ENTRY                     = 0x0032,
        LOG_ENTRY_COUNT               = 0x0033,
        ENABLE_LOGGING                = 0x0034,
        SET_ADVANCED_CONFIG           = 0x0035,
        REQUEST_ADVANCED_CONFIG       = 0x0036,
        ADVANCED_CONFIG               = 0x0037,
        ADD_TIME_CONTROL_ENTRY        = 0x0039,
        TIME_CONTROL_ENTRY_ID         = 0x003A,
        REMOVE_TIME_CONTROL_ENTRY     = 0x003B,
        REQUEST_TIME_CONTROL_ENTRIES  = 0x003C,
        TIME_CONTROL_ENTRY_COUNT      = 0x003D,
        TIME_CONTROL_ENTRY            = 0x003E,
        UPDATE_TIME_CONTROL_ENTRY     = 0x003F,
        ADD_KEYPAD_CODE               = 0x0041,
        KEYPAD_CODE_ID                = 0x0042,
        REQUEST_KEYPAD_CODES          = 0x0043,
        KEYPAD_CODE_COUNT             = 0x0044,
        KEYPAD_CODE                   = 0x0045,
        UPDATE_KEYPAD_CODE            = 0x0046,
        REMOVE_KEYPAD_CODE            = 0x0047,
        KEYPAD_ACTION                 = 0x0048,
        CONTINUOUS_MODE_ACTION        = 0x0057, # Opener only
        SIMPLE_LOCK_ACTION            = 0x0100,
    )

    TimeZoneId = Enum(Int16ul,
        AFRICA_CAIRO = 0,                     # UTC+2 EET dst: no
        AFRICA_LAGOS = 1,                     # UTC+1 WAT dst: no
        AFRICA_MAPUTO = 2,                    # UTC+2 CAT, SAST dst: no
        AFRICA_NAIROBI = 3,                   # UTC+3 EAT dst: no
        AMERICA_ANCHORAGE = 4,                # UTC-9/-8 AKDT dst: yes
        AMERICA_ARGENTINA_BUENOS_AIRES = 5,   # UTC-3 ART, UYT dst: no
        AMERICA_CHICAGO = 6,                  # UTC-6/-5 CDT dst: yes
        AMERICA_DENVER = 7,                   # UTC-7/-6 MDT dst: yes
        AMERICA_HALIFAX = 8,                  # UTC-4/-3 ADT dst: yes
        AMERICA_LOS_ANGELES = 9,              # UTC-8/-7 PDT dst: yes
        AMERICA_MANAUS = 10,                  # UTC-4 AMT, BOT, VET, AST, GYT dst: no
        AMERICA_MEXICO_CITY = 11,             # UTC-6/-5 CDT dst: yes
        AMERICA_NEW_YORK = 12,                # UTC-5/-4 EDT dst: yes
        AMERICA_PHOENIX = 13,                 # UTC-7 MST dst: no
        AMERICA_REGINA = 14,                  # UTC-6 CST dst: no
        AMERICA_SANTIAGO = 15,                # UTC-4/-3 CLST, AMST, WARST, PYST dst: yes
        AMERICA_SAO_PAULO = 16,               # UTC-3 BRT dst: no
        AMERICA_ST_JOHNS = 17,                # UTC-3½/ -2½ NDT dst: yes
        ASIA_BANGKOK = 18,                    # UTC+7 ICT, WIB dst: no
        ASIA_DUBAI = 19,                      # UTC+4 SAMT, GET, AZT, GST, MUT, RET, SCT, AMT-Arm dst: no
        ASIA_HONG_KONG = 20,                  # UTC+8 HKT dst: no
        ASIA_JERUSALEM = 21,                  # UTC+2/+3 IDT dst: yes
        ASIA_KARACHI = 22,                    # UTC+5 PKT, YEKT, TMT, UZT, TJT, ORAT dst: no
        ASIA_KATHMANDU = 23,                  # UTC+5¾ NPT dst: no
        ASIA_KOLKATA = 24,                    # UTC+5½ IST dst: no
        ASIA_RIYADH = 25,                     # UTC+3 AST-Arabia dst: no
        ASIA_SEOUL = 26,                      # UTC+9 KST dst: no
        ASIA_SHANGHAI = 27,                   # UTC+8 CST, ULAT, IRKT, PHT, BND, WITA dst: no
        ASIA_TEHRAN = 28,                     # UTC+3½ ARST dst: no
        ASIA_TOKYO = 29,                      # UTC+9 JST, WIT, PWT, YAKT dst: no
        ASIA_YANGON = 30,                     # UTC+6½ MMT dst: no
        AUSTRALIA_ADELAIDE = 31,              # UTC+9½/10½ ACDT dst: yes
        AUSTRALIA_BRISBANE = 32,              # UTC+10 AEST, PGT, VLAT dst: no
        AUSTRALIA_DARWIN = 33,                # UTC+9½ ACST dst: no
        AUSTRALIA_HOBART = 34,                # UTC+10/+11 AEDT dst: yes
        AUSTRALIA_PERTH = 35,                 # UTC+8 AWST dst: no
        AUSTRALIA_SYDNEY = 36,                # UTC+10/+11 AEDT dst: yes
        EUROPE_BERLIN = 37,                   # UTC+1/+2 CEST dst: yes
        EUROPE_HELSINKI = 38,                 # UTC+2/+3 EEST dst: yes
        EUROPE_ISTANBUL = 39,                 # UTC+3 TRT dst: no
        EUROPE_LONDON = 40,                   # UTC+0/+1 BST, IST dst: yes
        EUROPE_MOSCOW = 41,                   # UTC+3 MSK dst: no
        PACIFIC_AUCKLAND = 42,                # UTC+12/+13 NZDT dst: yes
        PACIFIC_GUAM = 43,                    # UTC+10 ChST dst: no
        PACIFIC_HONOLULU = 44,                # UTC-10 H(A)ST dst: no
        PACIFIC_PAGO_PAGO = 45,               # UTC-11 SST dst: no
        NONE = 65535,                         #
    )

    State = Enum(Int8ul,
        UNINITIALIZED = 0x00,
        PAIRING_MODE = 0x01,
        DOOR_MODE = 0x02,
        CONTINUOUS_MODE = 0x03,
        MAINTENANCE_MODE = 0x04,
    )

    ActionTrigger = Enum(Int8ul,
        SYSTEM = 0x00,
        MANUAL = 0x01,
        BUTTON = 0x02,
        AUTOMATIC = 0x03,
        AUTO_LOCK = 0x06,
    )

    NukiClientType = Enum(Int8ul,
        APP = 0x00,
        BRIDGE = 0x01,
        FOB = 0x02,
        KEYPAD = 0x03,
    )

    LogEntryType = Enum(Int8ul,
        LOGGING_ENABLED_DISABLED = 0x01,
        LOCK_ACTION = 0x02,
        CALIBRATION = 0x03,
        INITIALIZATION_RUN = 0x04,
        KEYPAD_ACTION = 0x05,
        DOOR_SENSOR = 0x06, # DOORBELL_RECOGNITION for opener
        DOOR_SENSOR_LOGGING_ENABLED_DISABLED = 0x07,
    )

    BatteryType = Enum(Int8ul,
        ALKALI       = 0X00,
        ACCUMULATORS = 0X01,
        LITHIUM      = 0X02,
    )

    AdvertisingMode = Enum(Int8ul,
        AUTOMATIC = 0X00,
        NORMAL    = 0X01,
        SLOW      = 0X02,
        SLOWEST   = 0X03,
    )

    NukiDateTime = Struct(
        "year" / Int16ul,
        "month" / Int8ul,
        "day" / Int8ul,
        "hour" / Int8ul,
        "minute" / Int8ul,
        "second" / Int8ul,
    )

    NukiTime = Struct(
        "hour" / Int8ul,
        "minute" / Int8ul,
    )

    NukiWeekdaysBits = BitStruct(
        # bit 7  6  5  4  3  2  1  0
        #     -  M  T  W  T  F  S  S
        "pad" / Padding(1),
        "monday" / Bit,
        "tuesday" / Bit,
        "wednesday" / Bit,
        "thursday" / Bit,
        "friday" / Bit,
        "saturday" / Bit,
        "sunday" / Bit,
    )

    LogEntryCount = Struct(
        "logging_enabled" /  Int8ul,
        "count" /  Int16ul,
        "door_sensor_enabled" /  Int8ul,
        "door_sensor_logging_enabled" /  Int8ul,
    )

    NukiChallenge = Struct(
        "nonce" / Bytes(32)
    )

    NukiPublicKey = Struct(
        "public_key" / Bytes(32)
    )

    AuthorizationId = Struct(
        "authenticator" / Bytes(32),
        "auth_id" / Bytes(4),
        "uuuid" / Bytes(16),
        "nonce" / Bytes(32)
    )

    NukiCommandStatus = Struct(
        "status" / StatusCode
    )

    NukiError = Struct(
        "error_code" / ErrorCode,
        "command_identifier" / NukiCommand
    )

    NukiEncryptedMessage = Struct(
        "nonce" / Bytes(24),
        "auth_id" / Bytes(4),
        "length" / Int16ul,
        "encrypted" / Bytes(this.length)
    )

    RequestLogEntries = Struct(
        "start_index" / Int32ul,
        "count" / Int16ul,
        "sort_order" / Int8ul,
        "total_count" / Int8ul,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    VerifySecurityPin = Struct(
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    AddKeypadCode = Struct(
        "code" / Int32ul, #needs to be 6 digits
        "name" / PaddedString(20, "utf8"),
        "time_limited" / Int8ul,
        "allowed_from_date" / NukiDateTime,
        "allowed_until_date" / NukiDateTime,
        "allowed_weekdays" / NukiWeekdaysBits,
        "allowed_from_time" / NukiTime,
        "allowed_until_time" / NukiTime,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    KeypadCodeEntry = Struct(
        "code_id" / Int16ul,
        "code" / Int32ul,
        "name" / PaddedString(20, "utf8"),
        "enabled" / Int8ul,
        "date_created" / NukiDateTime,
        "date_last_active" / NukiDateTime,
        "lock_count" / Int16ul,
        "time_limited" / Int8ul,
        "allowed_from_date" / NukiDateTime,
        "allowed_until_date" / NukiDateTime,
        "allowed_weekdays" / NukiWeekdaysBits,
        "allowed_from_time" / NukiTime,
        "allowed_until_time" / NukiTime,
    )

    UpdatedKeypadCode = Struct(
        "code_id" / Int16ul,
        "code" / Int32ul,
        "name" / PaddedString(20, "utf8"),
        "enabled" / Int8ul,
        "time_limited" / Int8ul,
        "allowed_from_date" / NukiDateTime,
        "allowed_until_date" / NukiDateTime,
        "allowed_weekdays" / NukiWeekdaysBits,
        "allowed_from_time" / NukiTime,
        "allowed_until_time" / NukiTime,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    AuthorizationEntry = Struct(
        "auth_id" / Int32ul,
        "id_type" / Int8ul,
        "name" / PaddedString(32, "utf8"),
        "enabled" / Int8ul,
        "remote_allowed" / Int8ul,
        "date_created" / NukiDateTime,
        "date_last_active" / NukiDateTime,
        "lock_count" / Int16ul,
        "time_limited" / Int8ul,
        "allowed_from_date" / NukiDateTime,
        "allowed_until_date" / NukiDateTime,
        "allowed_weekdays" / NukiWeekdaysBits,
        "allowed_from_time" / NukiTime,
        "allowed_until_time" / NukiTime,
    )

    NewAuthorizationEntry = Struct(
        "name" / PaddedString(32, "utf8"),
        "id_type" / Int8ul,
        "shared_key" / Bytes(32), #TODO: add shared key within class
        "remote_allowed" / Int8ul,
        "time_limited" / Int8ul,
        "allowed_from_date" / NukiDateTime,
        "allowed_until_date" / NukiDateTime,
        "allowed_weekdays" / NukiWeekdaysBits,
        "allowed_from_time" / NukiTime,
        "allowed_until_time" / NukiTime,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    UpdatedAuthorizationEntry = Struct(
        "auth_id" / Int32ul,
        "name" / PaddedString(32, "utf8"),
        "enabled" / Int8ul,
        "remote_allowed" / Int8ul,
        "time_limited" / Int8ul,
        "allowed_from_date" / NukiDateTime,
        "allowed_until_date" / NukiDateTime,
        "allowed_weekdays" / NukiWeekdaysBits,
        "allowed_from_time" / NukiTime,
        "allowed_until_time" / NukiTime,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    LockState = NotImplemented
    LockAction = NotImplemented
    KeyturnerStates = NotImplemented
    Config = NotImplemented

    @functools.cached_property
    def NukiLockActionMsg(self):
        return Struct(
            "lock_action" / self.LockAction,
            "app_id" / Int32ul,
            "flags" / Int8ul,
            "name_suffix" / Optional(PaddedString(20, "utf8")),
            "nonce" / Bytes(32),
        )

    LogEntryExt1 = Struct(
        "logging_enabled" / Int8ul,
    )

    @functools.cached_property
    def LogEntryExt2(self):
        return Struct(
            "lock_action" / self.LockAction,
            "trigger" / self.ActionTrigger,
            "flags" / Int8ul,
            "completion_status" / self.LockActionCompletionStatus,
        )

    @functools.cached_property
    def LogEntryExt3(self):
        return Struct(
        "lock_action" / self.LockAction,
        "source" / Int8ul,
        "completion_status" / self.LockActionCompletionStatus,
        "code_id" / Int16ul,
    )

    LogEntryExt4 = Struct(
        "door_status" / Int8ul,
    )

    @functools.cached_property
    def LogEntry(self):
        return Struct(
            "index" / Int32ul,
            "timestamp" / self.NukiDateTime,
            "auth_id" / Int32ul,
            "name" / PaddedString(32, "utf8"),
            "type" / self.LogEntryType,
            "data" / Switch(this.type, {
                                    self.LogEntryType.LOGGING_ENABLED_DISABLED : self.LogEntryExt1,
                                    self.LogEntryType.LOCK_ACTION : self.LogEntryExt2,
                                    self.LogEntryType.CALIBRATION : self.LogEntryExt2,
                                    self.LogEntryType.INITIALIZATION_RUN : self.LogEntryExt2,
                                    self.LogEntryType.KEYPAD_ACTION : self.LogEntryExt3,
                                    self.LogEntryType.DOOR_SENSOR : self.LogEntryExt4,
                                    self.LogEntryType.DOOR_SENSOR_LOGGING_ENABLED_DISABLED : self.LogEntryExt1,
                                    }),
        )

    @functools.cached_property
    def NukiMessage(self):
        return Struct(
            "auth_id" / Bytes(4),
            "command" / self.NukiCommand,
            "payload" / Switch(this.command, {
                        self.NukiCommand.PUBLIC_KEY : self.NukiPublicKey,
                        self.NukiCommand.CHALLENGE : self.NukiChallenge,
                        self.NukiCommand.AUTHORIZATION_ID : self.AuthorizationId,
                        self.NukiCommand.KEYTURNER_STATES : self.KeyturnerStates,
                        self.NukiCommand.STATUS : self.NukiCommandStatus,
                        self.NukiCommand.ERROR_REPORT : self.NukiError,
                        self.NukiCommand.CONFIG : self.Config,
                        self.NukiCommand.LOG_ENTRY : self.LogEntry,
                        self.NukiCommand.LOG_ENTRY_COUNT : self.LogEntryCount,
            }),
            "crc" / Bytes(2)
        )
    @functools.cached_property
    def  BatteryReport(self):
        return Struct(
            "battery_drain" / Int16ul,
            "battery_voltage" / Int16ul,
            "critical_battery_state" / Int8ul,
            "lock_action" / self.LockAction,
            "start_voltage" / Int16ul,
            "lowest_voltage" / Int16ul,
            "lock_distance" / Int16ul,
            "start_temperature" / Int8sl,
            "max_turn_current" / Int16ul,
            "battery_resistance" / Int16ul,
        )

    @functools.cached_property
    def  TimeControlEntry(self):
        return Struct(
            "entry_id" / Int8ul,
            "enabled" / Int8ul,
            "weekdays" / self.NukiWeekdaysBits,
            "time" / self.NukiTime,
            "lock_action" / self.LockAction,
        )

    @functools.cached_property
    def  NewTimeControlEntry(self):
        return Struct(
            "weekdays" / self.NukiWeekdaysBits,
            "time" / self.NukiTime,
            "lock_action" / self.LockAction,
            "nonce" / Bytes(32),
            "security_pin" / Int16ul,
        )


class NukiLockConst(NukiConst):
    BLE_PAIRING_SERVICE = "a92ee100-5501-11e4-916c-0800200c9a66"
    BLE_PAIRING_CHAR =    "a92ee101-5501-11e4-916c-0800200c9a66"
    BLE_SERVICE =         "a92ee200-5501-11e4-916c-0800200c9a66"
    BLE_CHAR =            "a92ee202-5501-11e4-916c-0800200c9a66"

    LockState = Enum(Int8ul,
        UNCALIBRATED = 0x00,
        LOCKED = 0x01,
        UNLOCKING = 0x02,
        UNLOCKED = 0x03,
        LOCKING = 0x04,
        UNLATCHED = 0x05,
        UNLOCKED_LOCK_N_GO = 0x06,
        UNLATCHING = 0x07,
        CALIBRATION = 0xFC,
        BOOT_RUN = 0xFD,
        MOTOR_BLOCKED = 0xFE,
        UNDEFINED = 0xFF,
    )

    LockAction = Enum(Int8ul,
        NONE = 0x00,
        UNLOCK = 0x01,
        LOCK = 0x02,
        UNLATCH = 0x03,
        LOCK_N_GO = 0x04,
        LOCK_N_GO_UNLATCH = 0x05,
        FULL_LOCK = 0x06,
        FOB_ACTION_1 = 0x81,
        FOB_ACTION_2 = 0x82,
        FOB_ACTION_3 = 0x83,
    )

    ButtonPressAction = Enum(Int8ul,
        NO_ACTION   = 0X00,
        INTELLIGENT = 0X01,
        UNLOCK      = 0X02,
        LOCK        = 0X03,
        UNLATCH     = 0X04,
        LOCK_N_GO   = 0X05,
        SHOW_STATUS = 0X06
    )

    KeyturnerStates = Struct(
        "nuki_state" / NukiConst.State,
        "lock_state" / LockState,
        "trigger" / NukiConst.ActionTrigger,
        "current_time" / NukiConst.NukiDateTime,
        "timezone_offset" / Int16sl,
        "critical_battery_state" / Int8ul,
        "config_update_count" / Int8ul,
        "lock_n_go_timer" / Int8ul,
        "last_lock_action" / LockAction,
        "last_lock_action_trigger" / NukiConst.ActionTrigger,
        "last_lock_action_completion_status" / NukiConst.LockActionCompletionStatus,
        "door_sensor_state" / NukiConst.DoorsensorState,
        "nightmode_active" / Int16ul,
        "accessory_battery_state" / Int8ul,
    )

    Config = Struct(
        "nuki_id" / Int32ul,
        "name" / PaddedString(32, "utf8"),
        "latitude" / Float32l,
        "longitude" / Float32l,
        "auto_unlatch" / Int8ul,
        "pairing_enabled" / Int8ul,
        "button_enabled" / Int8ul,
        "led_enabled" / Int8ul,
        "led_brightness" / Int8ul,
        "current_time" / NukiConst.NukiDateTime,
        "timezone_offset" / Int16sl,
        "dst_mode" / Int8ul,
        "has_fob" / Int8ul,
        "fob_action_1" / Int8ul,
        "fob_action_2" / Int8ul,
        "fob_action_3" / Int8ul,
        "single_lock" / Int8ul,
        "advertising_mode" / NukiConst.AdvertisingMode,
        "has_keypad" / Int8ul,
        "firmware_version" / Int8ul[3],
        "hardware_revision" / Int8ul[2],
        "homekit_status" / Int8ul,
        "timezone_id" / NukiConst.TimeZoneId,
        "undocumented" / Int8ul,
        "undocumented2" / Int8ul,
        "has_keypad_v2" / Int8ul,
    )

    NewConfig = Struct(
        "name" / PaddedString(32, "utf8"),
        "latitude" / Float32l,
        "longitude" / Float32l,
        "auto_unlatch" / Int8ul,
        "pairing_enabled" / Int8ul,
        "button_enabled" / Int8ul,
        "led_enabled" / Int8ul,
        "led_brightness" / Int8ul,
        "timezone_offset" / Int16sl,
        "dst_mode" / Int8ul,
        "fob_action_1" / Int8ul,
        "fob_action_2" / Int8ul,
        "fob_action_3" / Int8ul,
        "single_lock" / Int8ul,
        "advertising_mode" / NukiConst.AdvertisingMode,
        "timezone_id" / NukiConst.TimeZoneId,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    AdvancedConfig = Struct(
        "total_degrees" / Int16ul,
        "unlocked_position_offset_degrees" / Int16sl,
        "locked_position_offset_degrees" / Int16sl,
        "single_locked_position_offset_degrees" / Int16sl,
        "unlocked_to_locked_transition_offset_degrees" / Int16sl,
        "lock_n_go_timeout" / Int8ul,
        "single_button_press_action" / ButtonPressAction,
        "double_button_press_action" / ButtonPressAction,
        "detached_cylinder" / Int8ul,
        "battery_type" / NukiConst.BatteryType,
        "automatic_battery_type_detection" / Int8ul,
        "unlatch_duration" / Int8ul,
        "auto_lock_timeout" / Int16ul,
        "auto_unlock_disabled" / Int8ul,
        "night_mode_enabled" / Int8ul,
        "night_mode_start_time" / NukiConst.NukiTime,
        "night_mode_end_time" / NukiConst.NukiTime,
        "night_mode_auto_lock_enabled" / Int8ul,
        "night_mode_auto_unlock_disabled" / Int8ul,
        "night_mode_immediate_lock_on_start" / Int8ul,
        "auto_lock_enabled" / Int8ul,
        "immediate_auto_lock_enabled" / Int8ul,
        "auto_update_enabled" / Int8ul,
    )

    NewAdvancedConfig = Struct(
        "unlocked_position_offset_degrees" / Int16sl,
        "locked_position_offset_degrees" / Int16sl,
        "single_locked_position_offset_degrees" / Int16sl,
        "unlocked_to_locked_transition_offset_degrees" / Int16sl,
        "lock_n_go_timeout" / Int8ul,
        "single_button_press_action" / ButtonPressAction,
        "double_button_press_action" / ButtonPressAction,
        "detached_cylinder" / Int8ul,
        "battery_type" / NukiConst.BatteryType,
        "automatic_battery_type_detection" / Int8ul,
        "unlatch_duration" / Int8ul,
        "auto_lock_timeout" / Int16ul,
        "auto_unlock_disabled" / Int8ul,
        "night_mode_enabled" / Int8ul,
        "night_mode_start_time" / NukiConst.NukiTime,
        "night_mode_end_time" / NukiConst.NukiTime,
        "night_mode_auto_lock_enabled" / Int8ul,
        "night_mode_auto_unlock_disabled" / Int8ul,
        "night_mode_immediate_lock_on_start" / Int8ul,
        "auto_lock_enabled" / Int8ul,
        "immediate_auto_lock_enabled" / Int8ul,
        "auto_update_enabled" / Int8ul,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

class NukiOpenerConst(NukiConst):
    BLE_PAIRING_SERVICE = "a92ae100-5501-11e4-916c-0800200c9a66"
    BLE_PAIRING_CHAR =    "a92ae101-5501-11e4-916c-0800200c9a66"
    BLE_SERVICE =         "a92ae200-5501-11e4-916c-0800200c9a66"
    BLE_CHAR =            "a92ae202-5501-11e4-916c-0800200c9a66"

    LockState = Enum(Int8ul,
        UNCALIBRATED = 0x00,
        LOCKED = 0x01,
        RTO_ACTIVE = 0x03,
        OPEN = 0x05,
        OPENING = 0x07,
        UNDEFINED = 0xFF,
    )

    LockAction = Enum(Int8ul,
        NONE = 0x00,
        ACTIVATE_RTO = 0X01,
        DEACTIVATE_RTO = 0X02,
        ELECTRIC_STRIKE_ACTUATION = 0X03,
        ACTIVATE_CM = 0X04,
        DEACTIVATE_CM = 0X05,
        FOB_ACTION_1 = 0x81,
        FOB_ACTION_2 = 0x82,
        FOB_ACTION_3 = 0x83,
    )

    ButtonPressAction = Enum(Int8ul,
        NO_ACTION = 0X00,
        TOGGLE_RTO = 0X01,
        ACTIVATE_RTO = 0X02,
        DEACTIVATE_RTO = 0X03,
        TOGGLE_CM = 0X04,
        ACTIVATE_CM = 0X05,
        DEACTIVATE_CM = 0X06,
        OPEN = 0X07
    )

    KeyturnerStates = Struct(
        "nuki_state" / NukiConst.State,
        "lock_state" / LockState,
        "trigger" / NukiConst.ActionTrigger,
        "current_time" / NukiConst.NukiDateTime,
        "timezone_offset" / Int16sl,
        "critical_battery_state" / Int8ul,
        "config_update_count" / Int8ul,
        "ring_to_open_timer" / Int8ul,
        "last_lock_action" / LockAction,
        "last_lock_action_trigger" / NukiConst.ActionTrigger,
        "last_lock_action_completion_status" / NukiConst.LockActionCompletionStatus,
        "door_sensor_state" / NukiConst.DoorsensorState,
        # "nightmode_active" / Int16ul,
        # "accessory_battery_state" / Int8ul,
    )

    Config = Struct(
        "nuki_id" / Int32ul,
        "name" / PaddedString(32, "utf8"),
        "latitude" / Float32l,
        "longitude" / Float32l,
        "capabilities" / Int8ul,
        "pairing_enabled" / Int8ul,
        "button_enabled" / Int8ul,
        "led_enabled" / Int8ul,
        "current_time" / NukiConst.NukiDateTime,
        "timezone_offset" / Int16sl,
        "dst_mode" / Int8ul,
        "has_fob" / Int8ul,
        "fob_action_1" / Int8ul,
        "fob_action_2" / Int8ul,
        "fob_action_3" / Int8ul,
        "operating_mode" / Int8ul,
        "advertising_mode" / NukiConst.AdvertisingMode,
        "has_keypad" / Int8ul,
        "firmware_version" / Int8ul[3],
        "hardware_revision" / Int8ul[2],
        "timezone_id" / NukiConst.TimeZoneId,
        "undocumented" / Int8ul,
        "undocumented2" / Int8ul,
        "has_keypad_v2" / Int8ul,
    )

    NewConfig = Struct(
        "name" / PaddedString(32, "utf8"),
        "latitude" / Float32l,
        "longitude" / Float32l,
        "capabilities" / Int8ul,
        "pairing_enabled" / Int8ul,
        "button_enabled" / Int8ul,
        "led_enabled" / Int8ul,
        "timezone_offset" / Int16sl,
        "dst_mode" / Int8ul,
        "fob_action_1" / Int8ul,
        "fob_action_2" / Int8ul,
        "fob_action_3" / Int8ul,
        "operating_mode" / Int8ul,
        "advertising_mode" / NukiConst.AdvertisingMode,
        "timezone_id" / NukiConst.TimeZoneId,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

    AdvancedConfig = Struct(
        "intercom_id" / Int16ul,
        "bus_mode_switch" / Int8ul,
        "short_circuit_duration" / Int16ul,
        "electric_strike_delay" / Int16ul,
        "random_electric_strike_delay" / Int8ul,
        "electric_strike_duration" / Int16ul,
        "disable_rto_after_ring" / Int8ul,
        "rto_timeout" / Int8ul,
        "unknown" / Int8ul,
        "doorbell_suppression" / Int8ul,
        "doorbell_suppression_duration" / Int16ul,
        "sound_ring" / Int8ul,
        "sound_open" / Int8ul,
        "sound_rto" / Int8ul,
        "sound_cm" / Int8ul,
        "sound_confirmation" / Int8ul,
        "sound_level" / Int8ul,
        "single_button_press_action" / ButtonPressAction,
        "double_button_press_action" / ButtonPressAction,
        "battery_type" / NukiConst.BatteryType,
        "automatic_battery_type_detection" / Int8ul,
    )

    NewAdvancedConfig = Struct(
        "intercom_id" / Int16ul,
        "bus_mode_switch" / Int8ul,
        "short_circuit_duration" / Int16ul,
        "electric_strike_delay" / Int16ul,
        "random_electric_strike_delay" / Int8ul,
        "electric_strike_duration" / Int16ul,
        "disable_rto_after_ring" / Int8ul,
        "rto_timeout" / Int8ul,
        "unknown" / Int8ul,
        "doorbell_suppression" / Int8ul,
        "doorbell_suppression_duration" / Int16ul,
        "sound_ring" / Int8ul,
        "sound_open" / Int8ul,
        "sound_rto" / Int8ul,
        "sound_cm" / Int8ul,
        "sound_confirmation" / Int8ul,
        "sound_level" / Int8ul,
        "single_button_press_action" / ButtonPressAction,
        "double_button_press_action" / ButtonPressAction,
        "battery_type" / NukiConst.BatteryType,
        "automatic_battery_type_detection" / Int8ul,
        "nonce" / Bytes(32),
        "security_pin" / Int16ul,
    )

class NukiErrorException(Exception):
    def __init__(self, error_code: NukiConst.ErrorCode, command : NukiConst.NukiCommand, *args: object) -> None:
        self.error_code = error_code
        self.command = command
        super().__init__(*args)

NukiLockConst = NukiLockConst()
NukiOpenerConst = NukiOpenerConst()