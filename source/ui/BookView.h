#pragma once

#include "content/Species.h"

class SubScreenService;
class TextService;

// The mushroom book on the NFLib screen: one page per species with the name,
// edibility and three illustrations (no descriptive text: the pictures speak).
class BookView
{
public:
    BookView(SubScreenService &subScreen, TextService &text) : subScreen_(subScreen), text_(text) {}

    void Open(int page);
    void Close();
    // Turns forward (+1) or back (-1), wrapping around.
    void Turn(int delta);

    int Page() const { return page_; }
    SpeciesId PageSpecies() const { return static_cast<SpeciesId>(page_); }

private:
    void DrawPage();

    SubScreenService &subScreen_;
    TextService &text_;
    int page_ = 0;
};
