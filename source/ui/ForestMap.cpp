#include "ui/ForestMap.h"

#include <nf_lib.h>

#include "ui/SubScreenService.h"
#include "world/Forest.h"

namespace {

using namespace ui;

// Tile indices in map_tiles (see assets/ui/gen_ui.py). Icons are 2x2 tiles:
// index i covers i, i+1 (top) and i+4, i+5 (bottom).
constexpr u32 kTilesParchment[] = { 0, 0, 0, 0, 0, 1, 1, 2, 3 };
constexpr u32 kIconTiles[] = {
    4,  // TreeRound
    6,  // TreeGolden
    12, // TreeFir
    14, // Bush
    20, // Rock
    22, // Stump
    28, // Shrine
};

constexpr int kMapVisibleHeight = 144;
constexpr int kIconHalf = 8;

u32 ParchmentTile(int x, int y)
{
    u32 hash = (static_cast<u32>(x) * 73856093u) ^ (static_cast<u32>(y) * 19349663u);
    hash ^= hash >> 13;
    return kTilesParchment[hash % (sizeof(kTilesParchment) / sizeof(kTilesParchment[0]))];
}

} // namespace

int ForestMap::ToPixel(Fixed world)
{
    return kWorldOriginPixel + ((world.Raw() * kPixelsPerUnit) >> Fixed::kShift);
}

void ForestMap::Build(const Forest &forest)
{
    for (int y = 0; y < kTiles; y++)
    {
        for (int x = 0; x < kTiles; x++)
            NF_SetTileOfMap(kSubScreen, kLayerMap, x, y, ParchmentTile(x, y));
    }

    for (int i = 0; i < forest.PropCount(); i++)
    {
        const Prop &prop = forest.PropAt(i);
        int tx = ToPixel(prop.position.x) / 8 - 1;
        int ty = ToPixel(prop.position.z) / 8 - 1;
        if (tx < 0 || ty < 0 || tx + 1 >= kTiles || ty + 1 >= kTiles)
            continue;

        u32 base = kIconTiles[static_cast<int>(prop.kind)];
        NF_SetTileOfMap(kSubScreen, kLayerMap, tx, ty, base);
        NF_SetTileOfMap(kSubScreen, kLayerMap, tx + 1, ty, base + 1);
        NF_SetTileOfMap(kSubScreen, kLayerMap, tx, ty + 1, base + 4);
        NF_SetTileOfMap(kSubScreen, kLayerMap, tx + 1, ty + 1, base + 5);
    }
    NF_UpdateVramMap(kSubScreen, kLayerMap);

    // Sprites created first are drawn on top: Nina, Mats, then mushrooms.
    ninaSprite_ = subScreen_.CreateSprite(Sheet::Icons, kIconNina, 0, 0, kPriorityMap);
    matsSprite_ = subScreen_.CreateSprite(Sheet::Icons, kIconMats, 0, 0, kPriorityMap);
    for (int i = 0; i < MushroomField::kMaxMushrooms; i++)
    {
        mushroomSprites_[i] = subScreen_.CreateSprite(Sheet::Icons, kIconMushroom, 0, 0, kPriorityMap);
        subScreen_.ShowSprite(mushroomSprites_[i], false);
    }
}

void ForestMap::Update(Vec2 nina, Vec2 mats, const MushroomField &mushrooms)
{
    frame_++;

    scrollX_ = ToPixel(nina.x) - kScreenWidth / 2;
    scrollY_ = ToPixel(nina.z) - kMapVisibleHeight / 2;
    if (scrollX_ < 0)
        scrollX_ = 0;
    if (scrollX_ > kMapSize - kScreenWidth)
        scrollX_ = kMapSize - kScreenWidth;
    if (scrollY_ < 0)
        scrollY_ = 0;
    if (scrollY_ > kMapSize - kMapVisibleHeight)
        scrollY_ = kMapSize - kMapVisibleHeight;
    NF_ScrollBg(kSubScreen, kLayerMap, scrollX_, scrollY_);

    PlaceSprite(ninaSprite_, nina, true);
    PlaceSprite(matsSprite_, mats, true);

    bool blinkOn = (frame_ / 15) % 2 == 0;
    for (int i = mushrooms.Count(); i < MushroomField::kMaxMushrooms; i++)
        subScreen_.ShowSprite(mushroomSprites_[i], false);

    for (int i = 0; i < mushrooms.Count(); i++)
    {
        const Mushroom &m = mushrooms.At(i);
        u32 sprite = mushroomSprites_[i];
        PlaceSprite(sprite, m.position, mushrooms.IsVisible(i));
        bool highlight = mushrooms.IsInReach(i, nina) && blinkOn;
        subScreen_.SetSpriteFrame(sprite, highlight ? kIconMushroomInReach : kIconMushroom);
    }
}

void ForestMap::PlaceSprite(u32 sprite, Vec2 world, bool visible)
{
    int x = ToPixel(world.x) - scrollX_ - kIconHalf;
    int y = ToPixel(world.z) - scrollY_ - kIconHalf;
    bool onMap = x > -16 && x < kScreenWidth && y > -16 && y < kMapVisibleHeight - kIconHalf;

    subScreen_.ShowSprite(sprite, visible && onMap);
    if (visible && onMap)
        subScreen_.MoveSprite(sprite, x, y);
}

bool ForestMap::ScreenToWorld(int x, int y, Vec2 &out) const
{
    if (!kMapArea.Contains(x, y))
        return false;

    int mapX = x + scrollX_ - kWorldOriginPixel;
    int mapY = y + scrollY_ - kWorldOriginPixel;
    out = { Fixed::FromRaw(mapX * Fixed::kOne / kPixelsPerUnit),
            Fixed::FromRaw(mapY * Fixed::kOne / kPixelsPerUnit) };
    return true;
}
