#pragma once

// Bottom-screen layout. Pixel numbers must match assets/ui/gen_ui.py.
namespace ui {

constexpr int kSubScreen = 1;

// BG layers (layer number = priority, 0 is on top).
enum Layer : unsigned
{
    kLayerText = 0,
    kLayerDialog = 1,
    kLayerBar = 2,
    kLayerMap = 3,
};

// Sprite priorities: map icons sit between map and bar, UI above the bar.
constexpr unsigned kPriorityDrag = 0;
constexpr unsigned kPriorityUi = 1;
constexpr unsigned kPriorityMap = 3;

struct Rect
{
    int x, y, w, h;

    constexpr bool Contains(int px, int py) const
    {
        return px >= x && px < x + w && py >= y && py < y + h;
    }
    constexpr Rect Grown(int margin) const
    {
        return { x - margin, y - margin, w + 2 * margin, h + 2 * margin };
    }
};

constexpr int kScreenWidth = 256;
constexpr Rect kMapArea = { 2, 2, 252, 140 };

constexpr int kSlotX0 = 6;
constexpr int kSlotStep = 38;
constexpr int kSlotY = 150;
constexpr int kSlotSize = 36;
constexpr int kLeafX0 = 160;
constexpr int kLeafY = 160;
constexpr Rect kPortrait = { 210, 148, 40, 40 };

constexpr Rect SlotRect(int slot)
{
    return { kSlotX0 + slot * kSlotStep, kSlotY, kSlotSize, kSlotSize };
}

// Text area inside the dialog panel (characters).
constexpr int kPanelColumn = 1;
constexpr int kPanelRow = 1;
constexpr int kPanelColumns = 30;
constexpr int kPanelRows = 6;

// Sprite sheets (NFLib graphics slots) and their frames.
enum class Sheet : unsigned
{
    Icons, // 16x16
    Items, // 32x32
    Count,
};

enum IconFrame : unsigned
{
    kIconMushroom,
    kIconMushroomInReach,
    kIconNina,
    kIconMats,
    kIconLeaf,
    kIconLeafLost,
    kIconSmokeSmall,
    kIconSmokeMedium,
    kIconSmokeLarge,
    kIconSmallLeaf, // + colour * 2 + flutter frame
};

enum ItemFrame : unsigned
{
    kFrameBasket,
    kFrameScarf,
    kFrameLantern,
    kFrameBell,
    kFrameLocked,
    kFrameMatsNormal,
    kFrameMatsHappy,
    kFrameMatsCold,
    kFrameMatsWorried,
};

} // namespace ui
