#pragma once

#include <array>

#include "math/Vec2.h"
#include "world/MushroomField.h"

class Forest;
class SubScreenService;

// Hand-drawn style map on the bottom screen: forest props as background
// tiles, Nina, Mats and mushrooms as sprites. Scrolls with Nina.
class ForestMap
{
public:
    explicit ForestMap(SubScreenService &subScreen) : subScreen_(subScreen) {}

    // Draws the forest into the map layer and creates the icon sprites (once).
    void Build(const Forest &forest);
    void Update(Vec2 nina, Vec2 mats, const MushroomField &mushrooms);

    // Converts a touch position inside the map area to world coordinates.
    bool ScreenToWorld(int x, int y, Vec2 &out) const;

    static constexpr int kPixelsPerUnit = 12;
    // A tap selects a mushroom within this world distance of the stylus.
    static constexpr Fixed kTapRadius = 1.1_fx;

private:
    static constexpr int kMapSize = 512;
    static constexpr int kTiles = kMapSize / 8;
    static constexpr int kWorldOriginPixel = kMapSize / 2;

    static int ToPixel(Fixed world);
    void PlaceSprite(u32 sprite, Vec2 world, bool visible);

    SubScreenService &subScreen_;
    u32 ninaSprite_ = 0;
    u32 matsSprite_ = 0;
    std::array<u32, MushroomField::kMaxMushrooms> mushroomSprites_ = {};
    int scrollX_ = 0;
    int scrollY_ = 0;
    int frame_ = 0;
};
