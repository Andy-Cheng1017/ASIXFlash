import runpy
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import flash


class DeviceSupportTests(unittest.TestCase):
    def test_original_ax88179_is_allowed(self):
        device = Mock(bcdDevice=0x0100)

        flash.check_device_support(device)

        device.ctrl_transfer.assert_not_called()

    def test_ax88179a_b_is_rejected_without_usb_transfers(self):
        device = Mock(bcdDevice=0x0200)

        with self.assertRaisesRegex(SystemExit, "AX88179A/AX88179B"):
            flash.check_device_support(device)

        device.ctrl_transfer.assert_not_called()

    def test_main_rejects_ax88179b_before_backup_or_transfers(self):
        device = Mock(bcdDevice=0x0200)

        with patch("usb.core.find", return_value=device), \
                patch("builtins.open") as open_file, \
                patch("builtins.print"):
            with self.assertRaisesRegex(SystemExit, "No EEPROM has been read or written"):
                runpy.run_path(str(Path(flash.__file__)), run_name="__main__")

        open_file.assert_not_called()
        device.ctrl_transfer.assert_not_called()

    def test_original_ax88179_keeps_backup_and_write_flow(self):
        device = Mock(bcdDevice=0x0100)
        device.ctrl_transfer.side_effect = (
            [bytes(6)] + [bytes(2)] * flash.AX_EEPROM_SIZE_WORDS
            + [0, 2, 2, 2, 0, 0] + [bytes(6)]
        )

        with patch("usb.core.find", return_value=device), \
                patch("builtins.open") as open_file, \
                patch("builtins.print"):
            runpy.run_path(str(Path(flash.__file__)), run_name="__main__")

        open_file.assert_called_once_with(flash.BACKUP_EEPROM_FILENAME, "wb")
        open_file.return_value.__enter__.return_value.write.assert_called_once_with(
            bytearray(flash.AX_EEPROM_SIZE_BYTES)
        )
        write_requests = [
            call.args[1] for call in device.ctrl_transfer.call_args_list
            if call.args[0] == 0x40
        ]
        self.assertEqual(write_requests, [0x07, 0x04, 0x04, 0x04, 0x08, 0x06])


if __name__ == "__main__":
    unittest.main()
