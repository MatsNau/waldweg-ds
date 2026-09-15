#pragma once

// Shows an error message on the sub screen and halts. For unrecoverable
// setup errors such as missing files in NitroFS.
[[noreturn]] void Fatal(const char *format, ...) __attribute__((format(printf, 1, 2)));
