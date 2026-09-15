#include "ui/TextSurface.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

namespace {

bool IsContinuationByte(char c)
{
    return (static_cast<unsigned char>(c) & 0xC0) == 0x80;
}

} // namespace

void TextSurface::Format(int column, int row, const char *format, ...)
{
    char line[kColumns * 4 + 1];

    va_list args;
    va_start(args, format);
    vsnprintf(line, sizeof(line), format, args);
    va_end(args);

    Write(column, row, line);
}

int TextSurface::WriteWrapped(int column, int row, int width, int maxRows, const char *utf8)
{
    char line[kColumns * 4 + 1];
    const char *p = utf8;
    int rows = 0;

    while (*p != '\0' && rows < maxRows)
    {
        while (*p == ' ')
            p++;

        // Take as many whole words as fit into `width` characters.
        const char *lineEnd = p;
        const char *cursor = p;
        int chars = 0;
        while (*cursor != '\0' && *cursor != '\n')
        {
            const char *wordEnd = cursor;
            int wordChars = 0;
            while (*wordEnd != '\0' && *wordEnd != ' ' && *wordEnd != '\n')
            {
                if (!IsContinuationByte(*wordEnd))
                    wordChars++;
                wordEnd++;
            }

            int needed = chars + (chars > 0 ? 1 : 0) + wordChars;
            if (needed > width && chars > 0)
                break;

            chars = needed;
            lineEnd = wordEnd;
            cursor = wordEnd;
            if (*cursor == ' ')
                cursor++;
            if (chars >= width)
                break;
        }

        size_t length = static_cast<size_t>(lineEnd - p);
        if (length >= sizeof(line))
            length = sizeof(line) - 1;
        memcpy(line, p, length);
        line[length] = '\0';
        Write(column, row + rows, line);
        rows++;

        p = lineEnd;
        if (*p == '\n')
            p++;
    }
    return rows;
}
