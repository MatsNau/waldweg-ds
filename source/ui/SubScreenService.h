#pragma once

#include <nds/ndstypes.h>

#include "ui/UiLayout.h"

// Owns the NFLib setup of the bottom screen: background layers (map, bar,
// dialog panel, text) and sprites, and uploads sprites once per frame.
class SubScreenService
{
public:
    // Requires NitroFS and NF_Set2D() on the sub screen.
    void Init();

    // Creates a sprite from a sheet and returns its NFLib sprite id.
    u32 CreateSprite(ui::Sheet sheet, u32 frame, int x, int y, u32 priority);
    void SetSpriteFrame(u32 id, u32 frame);
    void MoveSprite(u32 id, int x, int y);
    void ShowSprite(u32 id, bool show);
    void SetSpritePriority(u32 id, u32 priority);

    void ShowDialogPanel(bool show);

    // Book mode: map, bar and sprites are hidden and a book page fills the
    // screen (layer 1). Used by the inspection view, where the screens are swapped.
    void EnterBookMode();
    void ShowBookPage(int page);
    // Shows another full-screen page from nitrofiles/book (e.g. "ending").
    void ShowBookImage(const char *name);
    void ExitBookMode();

    // Final picture: the sky with the village replaces map and bar, all
    // sprites of the forest UI are hidden.
    void EnterEndingMode();
    // Back to the forest UI (new game); the map tiles are kept in RAM.
    void ExitEndingMode();

    // Call before waiting for the VBlank ...
    void PrepareFrame();
    // ... and right after it.
    void AfterVBlank();

private:
    static constexpr u32 kMaxSprites = 128;

    u32 nextSprite_ = 0;
    bool pageLoaded_ = false;
};
