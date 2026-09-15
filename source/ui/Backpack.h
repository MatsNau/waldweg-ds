#pragma once

#include <array>

#include "content/Items.h"

class GameProgress;
class InputService;
class SubScreenService;

enum class MatsMood
{
    Normal,
    Happy,
    Cold,
    Worried,
};

// Bottom bar: four item slots, the leaves for free mistakes and Mats' portrait.
// Items are handed over by dragging them from a slot onto the portrait.
class Backpack
{
public:
    explicit Backpack(SubScreenService &subScreen) : subScreen_(subScreen) {}

    void Init();
    // Shows the leaves and Mats' portrait again (the final picture hides all sprites).
    void ShowFixedSprites();

    // Returns the item dropped on Mats this frame, or ItemId::Count.
    ItemId Update(const InputService &input, const GameProgress &progress);

    bool IsDragging() const { return dragging_ != ItemId::Count; }
    void SetMatsMood(MatsMood mood);

private:
    void UpdateSlots(const GameProgress &progress);
    void ReturnDraggedItem();

    SubScreenService &subScreen_;
    std::array<u32, kItemCount> slotSprites_ = {};
    std::array<u32, 3> leafSprites_ = {};
    u32 portraitSprite_ = 0;

    ItemId dragging_ = ItemId::Count;
    int frame_ = 0;
};
