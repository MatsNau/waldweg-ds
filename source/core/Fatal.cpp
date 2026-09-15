#include "core/Fatal.h"

#include <stdarg.h>
#include <stdio.h>

#include <nds.h>

void Fatal(const char *format, ...)
{
    consoleDemoInit();
    printf("Fehler:\n\n");

    va_list args;
    va_start(args, format);
    vprintf(format, args);
    va_end(args);

    while (true)
        swiWaitForVBlank();
}
