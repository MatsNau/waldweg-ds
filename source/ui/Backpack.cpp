#include "ui/Backpack.h"

#include "core/InputService.h"
#include "game/GameProgress.h"
#include "ui/SubScreenService.h"

namespace {

using namespace ui;

constexpr int kItemSize = 32;
constexpr int kDropMargin = 10;

constexpr u32 kItemFrames[kItemCount] = { kFrameBasket, kFrameScarf, kFrameLantern, kFrameBell };

int SlotSpriteX(int slot)
{
    return SlotRect(slot).x + (kSlotSize - kItemSize) / 2;
}

int SlotSpriteY(int slot)
{
    return SlotRect(slot).y + (kSlotSize - kItemSize) / 2;
}

} // namespace

void Backpack::Init()
{
    for (int i = 0; i < kItemCount; i++)
    {
        slotSprites_[i] = subScreen_.CreateSprite(Sheet::Items, kFrameLocked,
                                                  SlotSpriteX(i), SlotSpriteY(i), kPriorityUi);
    }
    for (size_t i = 0; i < leafSprites_.size(); i++)
    {
        leafSprites_[i] = subScreen_.CreateSprite(Sheet::Icons, kIconLeaf,
                                                  kLeafX0 + static_cast<int>(i) * 16, kLeafY, kPriorityUi);
    }
    portraitSprite_ = subScreen_.CreateSprite(Sheet::Items, kFrameMatsNormal,
                                              kPortrait.x + (kPortrait.w - kItemSize) / 2,
                                              kPortrait.y + (kPortrait.h - kItemSize) / 2, kPriorityUi);
}

ItemId Backpack::Update(const InputService &input, const GameProgress &progress)
{
    frame_++;
    ItemId given = ItemId::Count;

    if (!IsDragging() && input.IsPressed(Button::Touch))
    {
        for (int i = 0; i < kItemCount; i++)
        {
            ItemId item = static_cast<ItemId>(i);
            if (SlotRect(i).Contains(input.TouchX(), input.TouchY()) &&
                progress.IsUnlocked(item) && !progress.IsGiven(item))
            {
                dragging_ = item;
                subScreen_.SetSpritePriority(slotSprites_[i], kPriorityDrag);
            }
        }
    }

    if (IsDragging())
    {
        u32 sprite = slotSprites_[static_cast<int>(dragging_)];
        if (input.IsTouching())
        {
            subScreen_.MoveSprite(sprite, input.TouchX() - kItemSize / 2, input.TouchY() - kItemSize / 2);
        }
        else
        {
            if (kPortrait.Grown(kDropMargin).Contains(input.TouchX(), input.TouchY()))
                given = dragging_;
            ReturnDraggedItem();
        }
    }

    UpdateSlots(progress);

    int lost = progress.Mistakes();
    for (size_t i = 0; i < leafSprites_.size(); i++)
    {
        bool isLost = static_cast<int>(i) >= static_cast<int>(leafSprites_.size()) - lost;
        subScreen_.SetSpriteFrame(leafSprites_[i], isLost ? kIconLeafLost : kIconLeaf);
    }

    return given;
}

void Backpack::ShowFixedSprites()
{
    for (u32 sprite : leafSprites_)
        subScreen_.ShowSprite(sprite, true);
    subScreen_.ShowSprite(portraitSprite_, true);
}

void Backpack::ReturnDraggedItem()
{
    int slot = static_cast<int>(dragging_);
    subScreen_.SetSpritePriority(slotSprites_[slot], kPriorityUi);
    subScreen_.MoveSprite(slotSprites_[slot], SlotSpriteX(slot), SlotSpriteY(slot));
    dragging_ = ItemId::Count;
}

void Backpack::UpdateSlots(const GameProgress &progress)
{
    for (int i = 0; i < kItemCount; i++)
    {
        ItemId item = static_cast<ItemId>(i);
        u32 sprite = slotSprites_[i];

        if (progress.IsGiven(item))
        {
            subScreen_.ShowSprite(sprite, false);
            continue;
        }

        subScreen_.ShowSprite(sprite, true);
        if (!progress.IsUnlocked(item))
        {
            subScreen_.SetSpriteFrame(sprite, kFrameLocked);
            continue;
        }

        subScreen_.SetSpriteFrame(sprite, kItemFrames[i]);
        if (dragging_ != item)
        {
            // New items hop gently to draw attention.
            int hop = ((frame_ / 20) % 2 == 0) ? 0 : -2;
            subScreen_.MoveSprite(sprite, SlotSpriteX(i), SlotSpriteY(i) + hop);
        }
    }
}

void Backpack::SetMatsMood(MatsMood mood)
{
    u32 frame = kFrameMatsNormal;
    if (mood == MatsMood::Happy)
        frame = kFrameMatsHappy;
    else if (mood == MatsMood::Cold)
        frame = kFrameMatsCold;
    else if (mood == MatsMood::Worried)
        frame = kFrameMatsWorried;
    subScreen_.SetSpriteFrame(portraitSprite_, frame);
}
