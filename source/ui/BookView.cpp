#include "ui/BookView.h"

#include <stdio.h>

#include "ui/SubScreenService.h"
#include "ui/TextService.h"

namespace {

// Text positions matching the page layout of assets/ui/gen_book.py.
constexpr int kTitleRow = 1;
constexpr int kEdibilityRow = 2;
constexpr int kPageNumberRow = 22;

int CharacterCount(const char *utf8)
{
    int count = 0;
    for (const char *p = utf8; *p != '\0'; p++)
    {
        if ((static_cast<unsigned char>(*p) & 0xC0) != 0x80)
            count++;
    }
    return count;
}

void WriteCentered(TextService &text, int row, const char *utf8)
{
    int column = (TextService::kColumns - CharacterCount(utf8)) / 2;
    text.Write(column < 0 ? 0 : column, row, utf8);
}

} // namespace

void BookView::Open(int page)
{
    page_ = page;
    subScreen_.EnterBookMode();
    DrawPage();
}

void BookView::Close()
{
    text_.Clear();
    text_.Present();
    subScreen_.ExitBookMode();
}

void BookView::Turn(int delta)
{
    page_ = (page_ + delta + kBookSpeciesCount) % kBookSpeciesCount;
    DrawPage();
}

void BookView::DrawPage()
{
    const SpeciesInfo &species = Species(PageSpecies());
    subScreen_.ShowBookPage(page_);

    text_.Clear();
    text_.SetColor(TextColor::Speaker);
    WriteCentered(text_, kTitleRow, species.name);

    text_.SetColor(species.edibility == Edibility::Edible ? TextColor::Good : TextColor::Danger);
    WriteCentered(text_, kEdibilityRow, species.edibilityLabel);

    text_.SetColor(TextColor::Ink);
    char number[24];
    snprintf(number, sizeof(number), "%d/%d", page_ + 1, kBookSpeciesCount);
    WriteCentered(text_, kPageNumberRow, number);

    text_.Present();
}
